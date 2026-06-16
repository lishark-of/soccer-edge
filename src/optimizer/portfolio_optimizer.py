from __future__ import annotations

from copy import deepcopy

from src.optimizer.candidate_pool import build_parlay_candidates
from src.optimizer.best_parlay import build_best_parlay_summary
from src.optimizer.constraints import RISK_PROFILES, merge_config, risk_allowed
from src.optimizer.scoring import score_candidate
from src.market.clv import build_clv_tracking

RANKING_LIMIT = 30


def optimize_portfolio(candidates: list[dict], bankroll: float = 10000.0, config: dict | None = None) -> dict:
    cfg = merge_config({**(config or {}), "bankroll": bankroll})
    result = _optimize_single_profile(candidates, bankroll, cfg)
    if cfg.get("compare_profiles"):
        result["profile_comparison"] = {
            profile: _comparison_summary(_optimize_single_profile(candidates, bankroll, merge_config({"risk_profile": profile, "bankroll": bankroll})))
            for profile in ("conservative", "balanced", "aggressive")
        }
    else:
        result["profile_comparison"] = {}
    return result


def _optimize_single_profile(candidates: list[dict], bankroll: float, cfg: dict) -> dict:
    singles_ranked = _rank_singles(candidates, bankroll, cfg)
    parlay_ranked = _rank_parlays(singles_ranked, bankroll, cfg)

    selected = {"singles": [], "parlay_2x1": [], "parlay_3x1": []}
    exposure = 0.0
    cap = float(cfg["daily_exposure_cap"])
    exposure = _select_ranked(selected["singles"], singles_ranked, int(cfg["max_singles"]), exposure, cap)
    exposure = _select_ranked(selected["parlay_2x1"], [item for item in parlay_ranked if item["candidate_type"] == "parlay_2x1"], int(cfg["max_parlay_2x1"]), exposure, cap)
    exposure = _select_ranked(selected["parlay_3x1"], [item for item in parlay_ranked if item["candidate_type"] == "parlay_3x1"], int(cfg["max_parlay_3x1"]), exposure, cap)

    rankings = {
        "singles": [_ranking_row(item) for item in singles_ranked[:RANKING_LIMIT]],
        "parlay_2x1": [_ranking_row(item) for item in [x for x in parlay_ranked if x["candidate_type"] == "parlay_2x1"][:RANKING_LIMIT]],
        "parlay_3x1": [_ranking_row(item) for item in [x for x in parlay_ranked if x["candidate_type"] == "parlay_3x1"][:RANKING_LIMIT]],
    }
    rejected = _rejected_summary([item for group in (singles_ranked, parlay_ranked) for item in group if not item.get("selected")][:120])
    no_2x1_reason = _no_2x1_reason(selected, rankings["parlay_2x1"], cfg)
    result = {
        "risk_profile": cfg["risk_profile"],
        "risk_profile_label": cfg["risk_profile_label"],
        "bankroll": round(float(bankroll), 2),
        "daily_exposure_cap": round(cap, 2),
        "recommended_paper_exposure": round(exposure, 2),
        "selected_portfolio": selected,
        "recommended_observation_portfolio": selected,
        "candidate_rankings": rankings,
        "rejected_candidates": rejected,
        "risk_summary": _risk_summary(selected, exposure, cap, cfg),
        "explanations": _explanations(selected, exposure, cap, cfg, no_2x1_reason),
        "no_2x1_reason": no_2x1_reason,
        "warnings": [],
        "disclaimer": "仅供纸面模拟和概率研究，不构成投注建议。本工具不提供投注、下单、支付、代购或自动化购彩能力。",
    }
    result["best_parlay_summary"] = build_best_parlay_summary(result)
    result["clv_tracking"] = build_clv_tracking(_selected_observations_for_clv(selected))
    return result


def _rank_singles(candidates: list[dict], bankroll: float, cfg: dict) -> list[dict]:
    ranked = []
    for candidate in candidates:
        item = score_candidate(candidate, bankroll, cfg)
        item["selected"] = False
        item["reject_reason"] = _base_reject_reason(item, cfg)
        ranked.append(item)
    return sorted(ranked, key=lambda item: item.get("score", -999), reverse=True)


def _rank_parlays(singles_ranked: list[dict], bankroll: float, cfg: dict) -> list[dict]:
    valid_singles = [item for item in singles_ranked if not item.get("reject_reason")]
    parlay_raw = build_parlay_candidates(valid_singles, max_legs=3)
    if not parlay_raw:
        diagnostic_legs = [
            item
            for item in singles_ranked
            if float(item.get("odds") or 0.0) > 1.01 and float(item.get("model_prob") or 0.0) > 0.0 and float(item.get("market_prob") or 0.0) > 0.0
        ][:8]
        parlay_raw = build_parlay_candidates(diagnostic_legs, max_legs=3)
    ranked = []
    for candidate in parlay_raw:
        if candidate.get("rejected"):
            item = {**candidate, "score": -999.0, "suggested_paper_stake": 0.0, "selected": False, "reject_reason": candidate.get("reject_reason", "未通过组合约束")}
        else:
            item = score_candidate(candidate, bankroll, cfg)
            item["selected"] = False
            item["reject_reason"] = _parlay_reject_reason(item, cfg)
        ranked.append(item)
    return sorted(ranked, key=lambda item: item.get("score", -999), reverse=True)


def _base_reject_reason(candidate: dict, cfg: dict) -> str:
    kind = candidate.get("candidate_type", "single")
    if kind == "parlay_2x1" and int(cfg.get("max_parlay_2x1", 0)) <= 0:
        return "当前风险档位不启用 2串1"
    if kind == "parlay_3x1" and (not cfg.get("enable_3x1") or int(cfg.get("max_parlay_3x1", 0)) <= 0):
        return "3串1 当前档位关闭"
    if float(candidate.get("ev") or 0.0) < float(cfg["min_ev"]):
        return "EV 不足"
    if float(candidate.get("edge") or 0.0) < float(cfg["min_edge"]):
        return "Edge 不足"
    if not (kind == "single" and candidate.get("parlay_eligible") is False) and not risk_allowed(str(candidate.get("risk_level", "medium")), str(cfg["max_risk"])):
        return "风险等级过高"
    odds = float(candidate.get("odds") or candidate.get("combo_odds") or 0.0)
    if odds <= 1.01:
        return "赔率过低"
    if float(candidate.get("correlation_discount") or 1.0) <= 0:
        return "相关性过强"
    return ""


def _parlay_reject_reason(candidate: dict, cfg: dict) -> str:
    reasons = []
    kind = candidate.get("candidate_type", "parlay_2x1")
    base = _base_reject_reason(candidate, cfg)
    if base:
        reasons.append(base)
    combo_prob = float(candidate.get("combo_prob") or candidate.get("model_prob") or 0.0)
    if kind == "parlay_3x1":
        min_combo_prob = float(cfg.get("min_parlay_3x1_prob", 0.12))
        combo_label = "3串1"
    else:
        min_combo_prob = float(cfg.get("min_parlay_2x1_prob", 0.20))
        combo_label = "2串1"
    if combo_prob < min_combo_prob:
        reasons.append(f"{combo_label} 组合命中概率低于纪律门槛 {min_combo_prob:.0%}")
    weak_legs = []
    min_leg_confidence = float(cfg.get("min_leg_confidence", 0.50))
    for leg in candidate.get("legs", []) or []:
        if leg.get("parlay_eligible") is False:
            weak_legs.append(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}：高赔率冷门腿不适合作为串联核心".strip())
            continue
        leg_confidence = float(leg.get("observation_confidence") or leg.get("confidence_score") or 0.0)
        if leg_confidence and leg_confidence < min_leg_confidence:
            weak_legs.append(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}：单腿可信度低于 {min_leg_confidence:.0%}".strip())
            continue
        leg_quality = float(leg.get("leg_quality_score") or 0.0)
        if leg_quality and leg_quality < 0.45:
            weak_legs.append(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}：单腿质量分偏低".strip())
            continue
        leg_reason = leg.get("reject_reason") or _base_reject_reason(leg, cfg)
        if leg_reason:
            weak_legs.append(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}：{leg_reason}".strip())
    if weak_legs:
        reasons.append("组合腿未全部通过单关纪律（" + "；".join(weak_legs[:3]) + "）")
    if float(candidate.get("correlation_discount") or 1.0) < 0.98:
        reasons.append("相关性折扣后吸引力下降")
    return "；".join(dict.fromkeys(reasons))


def _select_ranked(target: list, ranked: list[dict], limit: int, exposure: float, cap: float) -> float:
    selected_count = 0
    for item in ranked:
        if item.get("reject_reason"):
            continue
        stake = float(item.get("suggested_paper_stake") or 0.0)
        if selected_count >= limit:
            item["reject_reason"] = "超过当前档位数量上限"
            continue
        if stake <= 0:
            item["reject_reason"] = "建议纸面投入为 0"
            continue
        if exposure + stake > cap:
            item["reject_reason"] = "超过每日风险暴露"
            continue
        selected = deepcopy(item)
        selected["selected"] = True
        selected["reject_reason"] = ""
        target.append(selected)
        item["selected"] = True
        selected_count += 1
        exposure += stake
    return exposure


def _ranking_row(item: dict) -> dict:
    return {
        "type": item.get("candidate_type", "single"),
        "match": _label(item),
        "legs": _legs_label(item),
        "odds": item.get("odds") or item.get("combo_odds"),
        "model_prob": item.get("model_prob") or item.get("combo_prob"),
        "market_prob": item.get("market_prob"),
        "ev": item.get("ev"),
        "edge": item.get("edge"),
        "correlation_discount": item.get("correlation_discount", 1.0),
        "confidence_score": item.get("observation_confidence") or item.get("confidence_score"),
        "combo_score": item.get("combo_score"),
        "risk_adjusted_score": item.get("risk_adjusted_score"),
        "leg_quality_score": item.get("leg_quality_score"),
        "information_score": item.get("information_score"),
        "risk_penalty": item.get("risk_penalty"),
        "market_model_agreement": item.get("market_model_agreement"),
        "odds_quality": item.get("odds_quality"),
        "drawdown_safety": item.get("drawdown_safety"),
        "calibrated_prob": item.get("calibrated_prob"),
        "calibrated_ev": item.get("calibrated_ev"),
        "signal_category": item.get("signal_category"),
        "signal_category_zh": item.get("signal_category_zh"),
        "recommended_use_zh": item.get("recommended_use_zh"),
        "odds_bucket_zh": item.get("odds_bucket_zh"),
        "probability_bin": item.get("probability_bin"),
        "probability_bin_weight": item.get("probability_bin_weight"),
        "probability_bin_message_zh": item.get("probability_bin_message_zh", ""),
        "break_even_prob": item.get("break_even_prob"),
        "safety_margin": item.get("safety_margin"),
        "safety_margin_label_zh": item.get("safety_margin_label_zh"),
        "odds_reading_zh": item.get("odds_reading_zh"),
        "decision_level": item.get("decision_level"),
        "decision_label_zh": item.get("decision_label_zh"),
        "decision_action_zh": item.get("decision_action_zh"),
        "decision_reason_zh": item.get("decision_reason_zh"),
        "parlay_policy_zh": item.get("parlay_policy_zh"),
        "hit_rate_discipline_zh": item.get("hit_rate_discipline_zh", ""),
        "risk_level": item.get("risk_level"),
        "paper_stake": item.get("suggested_paper_stake", 0.0),
        "longshot_warning": item.get("longshot_warning", ""),
        "parlay_eligible": item.get("parlay_eligible", True),
        "selected": bool(item.get("selected")),
        "status": "入选" if item.get("selected") else "未入选",
        "reject_reason": item.get("reject_reason") or "已入选",
    }


def _rejected_summary(items: list[dict]) -> list[dict]:
    rows = []
    for item in items:
        rows.append(
            {
                "type": item.get("candidate_type", "single"),
                "match": _label(item),
                "ev": item.get("ev"),
                "edge": item.get("edge"),
                "risk_level": item.get("risk_level"),
                "paper_stake": item.get("suggested_paper_stake", 0.0),
                "reason": item.get("reject_reason", "未入选"),
            }
        )
    return rows


def _risk_summary(portfolio: dict, exposure: float, cap: float, cfg: dict) -> dict:
    return {
        "risk_profile": cfg.get("risk_profile"),
        "risk_profile_label": cfg.get("risk_profile_label"),
        "exposure_used": round(exposure, 2),
        "exposure_cap": round(cap, 2),
        "exposure_usage_pct": round(exposure / cap, 6) if cap > 0 else 0.0,
        "max_risk": cfg.get("max_risk"),
        "enable_3x1": bool(cfg.get("enable_3x1")),
        "profile_limits": {
            "max_singles": cfg.get("max_singles"),
            "max_parlay_2x1": cfg.get("max_parlay_2x1"),
            "max_parlay_3x1": cfg.get("max_parlay_3x1"),
            "min_ev": cfg.get("min_ev"),
            "min_edge": cfg.get("min_edge"),
            "min_parlay_2x1_prob": cfg.get("min_parlay_2x1_prob"),
            "min_parlay_3x1_prob": cfg.get("min_parlay_3x1_prob"),
            "min_leg_confidence": cfg.get("min_leg_confidence"),
        },
        "portfolio_counts": {key: len(value) for key, value in portfolio.items()},
    }


def _explanations(portfolio: dict, exposure: float, cap: float, cfg: dict, no_2x1_reason: str) -> list[str]:
    return [
        f"当前风险档位：{cfg.get('risk_profile_label')}。每日纸面暴露上限为本金 {float(cfg.get('max_daily_exposure_pct', 0)):.1%}。",
        no_2x1_reason,
        f"串联命中率纪律：2串1 最低组合命中概率 {float(cfg.get('min_parlay_2x1_prob', 0)):.0%}，3串1 最低组合命中概率 {float(cfg.get('min_parlay_3x1_prob', 0)):.0%}，单腿可信度门槛 {float(cfg.get('min_leg_confidence', 0)):.0%}。",
        "为什么没有更激进：优化器会先限制每日纸面暴露，再限制单关、2串1、3串1 的单项纸面投入，并用 EV、Edge、风险等级和相关性折扣过滤组合。",
        "如果切换到均衡或进取档，可能出现更多 2串1 或 3串1 观察项，但回撤和连续亏损概率也会升高。",
        "10000 元模拟只赚约 180 元，主要因为投入比例保守、候选数量有限、组合数量少，且 fixture 不是真实生产数据。",
        f"当前推荐纸面投入 {exposure:.2f} / 上限 {cap:.2f}。该结果不是实盘建议。",
    ]


def _no_2x1_reason(portfolio: dict, parlay2_rankings: list[dict], cfg: dict) -> str:
    if portfolio.get("parlay_2x1"):
        return f"当前{cfg.get('risk_profile_label')}档已有 2串1 观察项；仍需重点关注组合命中概率下降和风险放大。"
    if not parlay2_rankings:
        return "为什么当前没有 2串1：候选池不足，无法形成满足约束的 2串1。"
    reasons = sorted({str(item.get("reject_reason") or "未入选") for item in parlay2_rankings if not item.get("selected")})
    joined = "、".join(reasons[:4]) if reasons else "组合风险/相关性折扣/EV/每日暴露限制未通过"
    return f"为什么当前没有 2串1：{joined}。你可以切换到“均衡”或“进取”查看纸面模拟组合，但风险会升高。"


def _comparison_summary(result: dict) -> dict:
    portfolio = result.get("selected_portfolio", {})
    return {
        "risk_profile": result.get("risk_profile"),
        "risk_profile_label": result.get("risk_profile_label"),
        "daily_exposure_cap": result.get("daily_exposure_cap"),
        "recommended_paper_exposure": result.get("recommended_paper_exposure"),
        "singles_count": len(portfolio.get("singles", []) or []),
        "parlay_2x1_count": len(portfolio.get("parlay_2x1", []) or []),
        "parlay_3x1_count": len(portfolio.get("parlay_3x1", []) or []),
        "no_2x1_reason": result.get("no_2x1_reason"),
    }


def _selected_observations_for_clv(portfolio: dict) -> list[dict]:
    rows = []
    for key in ("singles", "parlay_2x1", "parlay_3x1"):
        for item in portfolio.get(key, []) or []:
            rows.append(item)
    return rows


def _label(item: dict) -> str:
    if item.get("legs"):
        return "；".join(_leg_label(leg) for leg in item.get("legs", []))
    return _leg_label(item)


def _legs_label(item: dict) -> str:
    if not item.get("legs"):
        return ""
    return "；".join(_leg_label(leg) for leg in item.get("legs", []) or [])


def _leg_label(item: dict) -> str:
    teams = f"{item.get('home_team','')} vs {item.get('away_team','')}".strip()
    play = _play_label(item.get("play_type"))
    direction = str(item.get("outcome_label") or item.get("direction") or "").strip()
    suffix = "·".join(part for part in [play, direction] if part)
    return f"{teams}｜{suffix}".strip("｜")


def _play_label(value: str | None) -> str:
    return {
        "had": "胜平负",
        "hhad": "让球胜平负",
        "total_goals": "总进球",
        "correct_score": "比分",
    }.get(str(value or ""), str(value or ""))

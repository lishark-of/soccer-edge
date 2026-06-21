from __future__ import annotations

from collections import Counter
from copy import deepcopy

from src.optimizer.candidate_pool import build_parlay_candidates
from src.optimizer.best_parlay import build_best_parlay_summary
from src.optimizer.constraints import RISK_PROFILES, merge_config, risk_allowed
from src.optimizer.play_bias import diagnose_play_bias
from src.optimizer.scoring import score_candidate
from src.market.clv import build_clv_tracking
from src.learning.history import build_learning_history
from src.learning.market_benchmark import build_market_benchmark_from_learning

RANKING_LIMIT = 30


def optimize_portfolio(candidates: list[dict], bankroll: float = 10000.0, config: dict | None = None) -> dict:
    cfg = merge_config({**(config or {}), "bankroll": bankroll})
    cfg = _attach_play_type_learning(cfg)
    result = _optimize_single_profile(candidates, bankroll, cfg)
    if cfg.get("compare_profiles"):
        result["profile_comparison"] = {
            profile: _comparison_summary(_optimize_single_profile(candidates, bankroll, _attach_play_type_learning(merge_config({
                "risk_profile": profile,
                "bankroll": bankroll,
                "play_type_learning_rows": cfg.get("play_type_learning_rows", []),
                "strategy_adjustments": cfg.get("strategy_adjustments", []),
                "learning_probability_quality": cfg.get("learning_probability_quality", {}),
                "learning_clv_summary": cfg.get("learning_clv_summary", {}),
                "learning_market_benchmark": cfg.get("learning_market_benchmark", {}),
                "learning_settled_count": cfg.get("learning_settled_count", 0),
                "probability_shrinkage_status": cfg.get("probability_shrinkage_status", {}),
            }))))
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
        "play_bias_diagnostics": diagnose_play_bias(rankings),
        "play_type_learning_status": cfg.get("play_type_learning_status", {}),
        "strategy_adjustment_status": cfg.get("strategy_adjustment_status", {}),
        "probability_shrinkage_status": cfg.get("probability_shrinkage_status", {}),
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
        item = _apply_play_type_learning(item, cfg)
        item = _apply_strategy_adjustments(item, cfg)
        item["selected"] = False
        item["reject_reason"] = _base_reject_reason(item, cfg)
        ranked.append(item)
    ranked = sorted(ranked, key=lambda item: item.get("score", -999), reverse=True)
    return _apply_single_play_concentration(ranked, cfg)


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
            item = _apply_play_diversity(item, cfg)
            item = _apply_combo_homogeneity(item, cfg)
            item = _apply_parlay_play_type_learning(item, cfg)
            item = _apply_parlay_strategy_adjustments(item, cfg)
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
        strategy_penalty = float(leg.get("strategy_adjustment_penalty") or 0.0)
        if strategy_penalty >= 0.06:
            weak_legs.append(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}：赛后学习调参提示该腿需降权复核".strip())
            continue
        robust_status = str(leg.get("robust_value_status") or "")
        if robust_status == "fragile":
            weak_legs.append(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}：概率区间下沿显示稳健价值不足".strip())
            continue
        disagreement_penalty = float(leg.get("model_disagreement_penalty") or 0.0)
        if disagreement_penalty >= 0.08:
            weak_legs.append(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}：模型与市场分歧较大，需要额外复核".strip())
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
    diversity = candidate.get("play_diversity") or {}
    if diversity.get("hard_block"):
        reasons.append(diversity.get("reason_zh", "玩法过于集中，组合不够分散"))
    homogeneity = candidate.get("combo_homogeneity") or {}
    if homogeneity.get("hard_block"):
        reasons.append(homogeneity.get("reason_zh", "组合逻辑过于同质化，暂不升级为优秀串联"))
    if float(candidate.get("correlation_discount") or 1.0) < 0.98:
        reasons.append("相关性折扣后吸引力下降")
    return "；".join(dict.fromkeys(reasons))


def _apply_play_diversity(candidate: dict, cfg: dict) -> dict:
    legs = candidate.get("legs") or []
    if not legs:
        return candidate
    kind = candidate.get("candidate_type", "parlay_2x1")
    max_same = int(cfg.get("max_same_play_type_3x1" if kind == "parlay_3x1" else "max_same_play_type_2x1", 1))
    penalty_unit = float(cfg.get("same_play_type_score_penalty", 0.14))
    play_counts = Counter(str(leg.get("play_type") or "unknown") for leg in legs)
    direction_counts = Counter(f"{leg.get('play_type') or 'unknown'}:{leg.get('outcome_key') or leg.get('outcome_label') or ''}" for leg in legs)
    broad_direction_counts = Counter(_broad_direction_family(leg) for leg in legs)
    max_count = max(play_counts.values()) if play_counts else 0
    max_direction_count = max(direction_counts.values()) if direction_counts else 0
    max_broad_direction_count = max(broad_direction_counts.values()) if broad_direction_counts else 0
    excess = max(0, max_count - max_same)
    direction_excess = max(0, max_direction_count - max_same)
    broad_excess = max(0, max_broad_direction_count - max_same)
    total_penalty = round((excess + direction_excess + broad_excess) * penalty_unit, 6)
    labels = [_play_label(key) for key in play_counts]
    if excess or direction_excess:
        reason = f"玩法过于集中：{'、'.join(labels)} 同类腿过多，已降权并阻止升级为强组合。"
    elif broad_excess:
        reason = f"方向过于集中：{_direction_counts_text(broad_direction_counts)}，已降权并阻止升级为强组合。"
    elif len(play_counts) == 1:
        reason = f"玩法集中：{'、'.join(labels)}，保留候选但排序降权。"
        total_penalty = max(total_penalty, round(penalty_unit * 0.5, 6))
    else:
        reason = f"玩法分散：{' + '.join(labels)}，组合结构更均衡。"
    item = dict(candidate)
    if total_penalty:
        item["score"] = round(float(item.get("score") or 0.0) - total_penalty * 10.0, 6)
        item["combo_score"] = round(float(item.get("combo_score") or 0.0) - total_penalty, 6)
        item["risk_adjusted_score"] = round(float(item.get("risk_adjusted_score") or 0.0) - total_penalty, 6)
        item["leg_quality_score"] = round(max(0.0, float(item.get("leg_quality_score") or 0.0) - total_penalty * 0.5), 6)
    item["play_diversity"] = {
        "play_type_counts": dict(play_counts),
        "direction_counts": dict(direction_counts),
        "broad_direction_counts": dict(broad_direction_counts),
        "max_same_play_type": max_same,
        "penalty": total_penalty,
        "hard_block": bool(excess or direction_excess or broad_excess),
        "reason_zh": reason,
        "mix_zh": " + ".join(labels),
    }
    item["play_diversity_reason_zh"] = reason
    item["play_type_mix_zh"] = " + ".join(labels)
    return item


def _apply_combo_homogeneity(candidate: dict, cfg: dict) -> dict:
    legs = candidate.get("legs") or []
    if len(legs) < 2:
        return candidate
    kind = candidate.get("candidate_type", "parlay_2x1")
    max_same_direction = int(cfg.get("max_same_direction_3x1" if kind == "parlay_3x1" else "max_same_direction_2x1", 1))
    unit = float(cfg.get("combo_homogeneity_penalty_unit", 0.06))
    direction_counts = Counter(_play_direction_key(leg) for leg in legs)
    broad_direction_counts = Counter(_broad_direction_family(leg) for leg in legs)
    odds_bucket_counts = Counter(str(leg.get("odds_bucket") or leg.get("odds_bucket_zh") or "unknown") for leg in legs)
    ai_factor_counts = Counter(str(leg.get("ai_factor") or "unknown") for leg in legs)
    signal_counts = Counter(str(leg.get("signal_category") or leg.get("signal_category_zh") or "unknown") for leg in legs)
    repeated_direction = sum(max(0, count - max_same_direction) for count in direction_counts.values())
    repeated_broad_direction = sum(max(0, count - max_same_direction) for count in broad_direction_counts.values())
    repeated_odds_bucket = sum(max(0, count - 1) for bucket, count in odds_bucket_counts.items() if bucket != "unknown")
    repeated_ai_factor = sum(max(0, count - 1) for factor, count in ai_factor_counts.items() if factor != "unknown")
    repeated_signal = sum(max(0, count - 1) for signal, count in signal_counts.items() if signal != "unknown")
    hard_block = repeated_direction > 0 or repeated_broad_direction > 0
    soft_units = repeated_odds_bucket * 0.55 + repeated_ai_factor * 0.45 + repeated_signal * 0.40
    penalty = round(min(0.26, repeated_direction * unit * 1.5 + repeated_broad_direction * unit * 1.2 + soft_units * unit), 6)
    if hard_block:
        level = "blocked"
    elif penalty >= 0.10:
        level = "crowded"
    elif penalty > 0:
        level = "watch"
    else:
        level = "balanced"
    reason = _combo_homogeneity_reason(
        hard_block,
        direction_counts,
        broad_direction_counts,
        odds_bucket_counts,
        ai_factor_counts,
        signal_counts,
        penalty,
    )
    item = dict(candidate)
    if penalty:
        item["score"] = round(float(item.get("score") or 0.0) - penalty * 10.0, 6)
        item["combo_score"] = round(float(item.get("combo_score") or 0.0) - penalty, 6)
        item["risk_adjusted_score"] = round(float(item.get("risk_adjusted_score") or 0.0) - penalty, 6)
        item["leg_quality_score"] = round(max(0.0, float(item.get("leg_quality_score") or 0.0) - penalty * 0.5), 6)
    item["combo_homogeneity"] = {
        "level": level,
        "penalty": penalty,
        "hard_block": hard_block,
        "play_direction_counts": dict(direction_counts),
        "broad_direction_counts": dict(broad_direction_counts),
        "odds_bucket_counts": dict(odds_bucket_counts),
        "ai_factor_counts": dict(ai_factor_counts),
        "signal_category_counts": dict(signal_counts),
        "reason_zh": reason,
    }
    item["combo_homogeneity_reason_zh"] = reason
    return item


def _attach_play_type_learning(cfg: dict) -> dict:
    if not cfg.get("use_play_type_learning", True) and not cfg.get("use_strategy_adjustments", True):
        return cfg
    history = None
    if cfg.get("play_type_learning_rows") is None:
        try:
            history = build_learning_history()
            rows = history.get("play_type_rows", []) or []
            learning_status = {
                "status": "loaded",
                "reason_zh": "已读取赛后玩法复盘，排序会参考玩法历史表现。",
                "play_type_count": len(rows),
            }
        except Exception as exc:
            rows = []
            learning_status = {
                "status": "fallback",
                "reason_zh": f"玩法复盘读取失败，本轮不因历史玩法表现调权：{str(exc).splitlines()[0]}",
                "play_type_count": 0,
            }
        cfg = {**cfg, "play_type_learning_rows": rows, "play_type_learning_status": learning_status}
    else:
        cfg = {**cfg, "play_type_learning_status": cfg.get("play_type_learning_status") or {
            "status": "provided",
            "reason_zh": "已使用调用方提供的玩法复盘样本。",
            "play_type_count": len(cfg.get("play_type_learning_rows", []) or []),
        }}
    if cfg.get("strategy_adjustments") is None:
        try:
            if history is None:
                history = build_learning_history()
            adjustments = history.get("strategy_adjustments", []) or []
            adjustment_status = {
                "status": "loaded",
                "reason_zh": "已读取赛后调参建议，排序会轻量参考弱玩法、赔率段、CLV 和概率质量。",
                "adjustment_count": len(adjustments),
            }
        except Exception as exc:
            adjustments = []
            adjustment_status = {
                "status": "fallback",
                "reason_zh": f"赛后调参建议读取失败，本轮不使用学习调权：{str(exc).splitlines()[0]}",
                "adjustment_count": 0,
            }
        cfg = {**cfg, "strategy_adjustments": adjustments, "strategy_adjustment_status": adjustment_status}
        if history:
            cfg = {
                **cfg,
                "learning_probability_quality": history.get("probability_quality", {}) or {},
                "learning_clv_summary": history.get("clv_history_summary", {}) or {},
                "learning_market_benchmark": build_market_benchmark_from_learning(history),
                "learning_settled_count": history.get("settled_count", 0),
                "probability_shrinkage_status": {
                    "status": "loaded",
                    "reason_zh": "已读取赛后 Brier/Log Loss/CLV 和市场基准技能分，模型概率会按证据强弱向市场概率收缩。",
                    "settled_count": history.get("settled_count", 0),
                },
            }
    else:
        cfg = {**cfg, "strategy_adjustment_status": cfg.get("strategy_adjustment_status") or {
            "status": "provided",
            "reason_zh": "已使用调用方提供的赛后调参建议。",
            "adjustment_count": len(cfg.get("strategy_adjustments", []) or []),
        }}
        cfg = {**cfg, "probability_shrinkage_status": cfg.get("probability_shrinkage_status") or {
            "status": "provided",
            "reason_zh": "已使用调用方提供的概率校准证据。",
            "settled_count": cfg.get("learning_settled_count", 0),
        }}
    return {
        **cfg,
        "play_type_learning_map": _play_type_learning_map(cfg.get("play_type_learning_rows", []) or []),
    }


def _play_type_learning_map(rows: list[dict]) -> dict[str, dict]:
    out = {}
    for row in rows:
        key = str(row.get("play_type") or "")
        if key:
            out[key] = dict(row)
    return out


def _apply_play_type_learning(candidate: dict, cfg: dict) -> dict:
    play = str(candidate.get("play_type") or "unknown")
    row = (cfg.get("play_type_learning_map") or {}).get(play)
    if not row:
        return {
            **candidate,
            "play_type_learning": {
                "status": "no_history",
                "penalty": 0.0,
                "reason_zh": f"{_play_label(play)} 暂无足够赛后玩法样本，当前不因历史表现调权。",
            },
            "play_type_learning_reason_zh": f"{_play_label(play)} 暂无足够赛后玩法样本，当前不因历史表现调权。",
        }
    attempts = int(row.get("attempts") or 0)
    min_attempts = int(cfg.get("play_type_learning_min_attempts", 10))
    hit_rate = _safe_float(row.get("hit_rate"))
    roi = _safe_float(row.get("paper_roi"))
    brier = _safe_float(row.get("brier_score"))
    cap = float(cfg.get("play_type_learning_penalty_cap", 0.10))
    roi_floor = float(cfg.get("play_type_learning_roi_floor", -0.02))
    penalty = 0.0
    status = "watch"
    reasons = []
    label = row.get("label_zh") or _play_label(play)
    if attempts < min_attempts:
        reasons.append(f"{label} 已有 {attempts} 条玩法样本，但不足 {min_attempts} 条，不直接调权。")
    else:
        if roi is not None and roi < roi_floor:
            penalty += min(cap, abs(roi) * 0.35 + 0.02)
            reasons.append(f"{label} 历史纸面 ROI {_pct_text(roi)}，低于阈值 {_pct_text(roi_floor)}。")
        if hit_rate is not None and hit_rate < 0.34:
            penalty += min(cap * 0.5, (0.34 - hit_rate) * 0.20)
            reasons.append(f"{label} 历史命中率 {_pct_text(hit_rate)} 偏弱。")
        if brier is not None and brier > 0.28:
            penalty += min(cap * 0.5, (brier - 0.28) * 0.30)
            reasons.append(f"{label} 历史 Brier {brier:.3f} 偏高，概率校准需降权。")
        penalty = round(min(cap, penalty), 6)
        status = "penalized" if penalty > 0 else "supported"
        if not reasons:
            reasons.append(f"{label} 历史玩法样本暂未触发降权；继续用赛后命中率、ROI 和校准指标跟踪。")
    adjusted = dict(candidate)
    if penalty:
        adjusted["score"] = round(float(adjusted.get("score") or 0.0) - penalty * 10.0, 6)
        adjusted["leg_quality_score"] = round(max(0.0, float(adjusted.get("leg_quality_score") or 0.0) - penalty * 0.45), 6)
        adjusted["risk_adjusted_score"] = round(float(adjusted.get("risk_adjusted_score") or 0.0) - penalty, 6)
    reason = " ".join(reasons)
    adjusted["play_type_learning"] = {
        "status": status,
        "play_type": play,
        "label_zh": label,
        "attempts": attempts,
        "hit_rate": hit_rate,
        "paper_roi": roi,
        "brier_score": brier,
        "penalty": penalty,
        "reason_zh": reason,
        "model_action_zh": row.get("model_action_zh") or "",
    }
    adjusted["play_type_learning_reason_zh"] = reason
    return adjusted


def _apply_strategy_adjustments(candidate: dict, cfg: dict) -> dict:
    adjustments = list(cfg.get("strategy_adjustments") or [])
    if not adjustments or not cfg.get("use_strategy_adjustments", True):
        return {
            **candidate,
            "strategy_adjustments_applied": [],
            "strategy_adjustment_penalty": 0.0,
            "strategy_adjustment_reason_zh": "暂无赛后调参建议影响该候选。",
        }
    cap = float(cfg.get("strategy_adjustment_penalty_cap", 0.08))
    odds = float(candidate.get("odds") or candidate.get("combo_odds") or 0.0)
    play = str(candidate.get("play_type") or "")
    bucket = str(candidate.get("odds_bucket") or "")
    risk = str(candidate.get("risk_level") or "")
    applied = []
    total_penalty = 0.0
    for row in adjustments:
        action = str(row.get("action") or "")
        target = row.get("target") or {}
        if not _strategy_adjustment_matches(action, target, candidate, odds, play, bucket, risk):
            continue
        confidence = _safe_float(row.get("confidence")) or 0.50
        priority = _safe_float(row.get("priority")) or 50.0
        penalty = min(cap, max(0.01, (priority / 100.0) * confidence * 0.11))
        if action in {"keep_small_sample_guard", "review_combo_gate"}:
            penalty *= 0.35
        if action == "tighten_longshot_gate":
            penalty = max(penalty, min(cap, 0.07))
        penalty = round(min(cap, penalty), 6)
        total_penalty += penalty
        applied.append({
            "key": row.get("key", action),
            "action": action,
            "label_zh": row.get("label_zh") or _strategy_action_label(action),
            "penalty": penalty,
            "reason_zh": row.get("reason_zh") or "",
            "expected_effect_zh": row.get("expected_effect_zh") or "",
        })
    total_penalty = round(min(cap, total_penalty), 6)
    adjusted = dict(candidate)
    if total_penalty:
        adjusted["score"] = round(float(adjusted.get("score") or 0.0) - total_penalty * 10.0, 6)
        adjusted["leg_quality_score"] = round(max(0.0, float(adjusted.get("leg_quality_score") or 0.0) - total_penalty * 0.45), 6)
        adjusted["risk_adjusted_score"] = round(float(adjusted.get("risk_adjusted_score") or 0.0) - total_penalty, 6)
        if any(row.get("action") == "tighten_longshot_gate" for row in applied):
            adjusted["parlay_eligible"] = False
            warning = adjusted.get("longshot_warning") or "高赔率冷门受赛后学习门控影响，不作为串联核心。"
            adjusted["longshot_warning"] = warning
    adjusted["strategy_adjustments_applied"] = applied
    adjusted["strategy_adjustment_penalty"] = total_penalty
    adjusted["strategy_adjustment_reason_zh"] = _strategy_adjustment_reason(applied)
    return adjusted


def _strategy_adjustment_matches(action: str, target: dict, candidate: dict, odds: float, play: str, bucket: str, risk: str) -> bool:
    if action == "downweight_play_type":
        return str(target.get("play_type") or "") == play
    if action == "downweight_competition_segment":
        return str(target.get("competition_segment") or "") == str(candidate.get("competition_segment") or "")
    if action == "downweight_ai_factor":
        return str(target.get("ai_factor") or "") == str(candidate.get("ai_factor") or "")
    if action == "tighten_longshot_gate":
        return odds >= float(target.get("odds_min") or 6.0)
    if action == "downweight_odds_bucket":
        return bool(bucket) and str(target.get("bucket") or "") == bucket
    if action == "reduce_confidence_on_negative_clv":
        return float(candidate.get("ev") or 0.0) > 0.08 or risk in {"high", "very_high"}
    if action == "downweight_model_probability":
        return float(candidate.get("model_disagreement_penalty") or 0.0) > 0.03 or float(candidate.get("safety_margin") or 0.0) < 0.05
    if action == "keep_small_sample_guard":
        return odds >= 4.0 or risk in {"high", "very_high"} or float(candidate.get("ev") or 0.0) > 0.15
    if action == "review_combo_gate":
        return False
    return False


def _strategy_adjustment_reason(applied: list[dict]) -> str:
    if not applied:
        return "暂无赛后调参建议影响该候选。"
    labels = []
    for row in applied[:3]:
        label = row.get("label_zh") or _strategy_action_label(str(row.get("action") or ""))
        reason = row.get("reason_zh") or row.get("expected_effect_zh") or ""
        labels.append(f"{label}：{reason}".strip("："))
    return "赛后学习调参：" + "；".join(labels)


def _strategy_action_label(action: str) -> str:
    return {
        "downweight_play_type": "弱玩法降权",
        "downweight_competition_segment": "赛事语境降权",
        "downweight_ai_factor": "AI因子降权",
        "tighten_longshot_gate": "高赔率冷门收紧",
        "downweight_odds_bucket": "弱赔率段降权",
        "reduce_confidence_on_negative_clv": "CLV 偏负降自信",
        "downweight_model_probability": "概率质量降权",
        "keep_small_sample_guard": "小样本保护",
        "review_combo_gate": "复查组合门控",
    }.get(action, action or "调参建议")


def _apply_parlay_play_type_learning(candidate: dict, cfg: dict) -> dict:
    legs = candidate.get("legs") or []
    if not legs:
        return candidate
    penalized = [leg.get("play_type_learning") for leg in legs if (leg.get("play_type_learning") or {}).get("penalty")]
    if not penalized:
        candidate["play_type_learning_reason_zh"] = "组合腿暂无玩法历史降权。"
        return candidate
    penalty = min(float(cfg.get("play_type_learning_penalty_cap", 0.10)), sum(float(row.get("penalty") or 0.0) for row in penalized) * 0.6)
    adjusted = dict(candidate)
    adjusted["score"] = round(float(adjusted.get("score") or 0.0) - penalty * 10.0, 6)
    adjusted["combo_score"] = round(float(adjusted.get("combo_score") or 0.0) - penalty, 6)
    adjusted["risk_adjusted_score"] = round(float(adjusted.get("risk_adjusted_score") or 0.0) - penalty, 6)
    adjusted["leg_quality_score"] = round(max(0.0, float(adjusted.get("leg_quality_score") or 0.0) - penalty * 0.5), 6)
    reasons = [str(row.get("reason_zh") or "") for row in penalized if row.get("reason_zh")]
    adjusted["play_type_learning"] = {
        "status": "penalized",
        "penalty": round(penalty, 6),
        "reason_zh": "；".join(reasons[:2]),
    }
    adjusted["play_type_learning_reason_zh"] = "玩法历史复盘触发组合降权：" + "；".join(reasons[:2])
    return adjusted


def _apply_parlay_strategy_adjustments(candidate: dict, cfg: dict) -> dict:
    legs = candidate.get("legs") or []
    applied = []
    for leg in legs:
        applied.extend(leg.get("strategy_adjustments_applied") or [])
    if not applied:
        candidate["strategy_adjustments_applied"] = []
        candidate["strategy_adjustment_penalty"] = 0.0
        candidate["strategy_adjustment_reason_zh"] = "组合腿暂无赛后调参降权。"
        return candidate
    cap = float(cfg.get("strategy_adjustment_penalty_cap", 0.08))
    penalty = round(min(cap, sum(float(row.get("penalty") or 0.0) for row in applied) * 0.55), 6)
    adjusted = dict(candidate)
    adjusted["score"] = round(float(adjusted.get("score") or 0.0) - penalty * 10.0, 6)
    adjusted["combo_score"] = round(float(adjusted.get("combo_score") or 0.0) - penalty, 6)
    adjusted["risk_adjusted_score"] = round(float(adjusted.get("risk_adjusted_score") or 0.0) - penalty, 6)
    adjusted["leg_quality_score"] = round(max(0.0, float(adjusted.get("leg_quality_score") or 0.0) - penalty * 0.5), 6)
    adjusted["strategy_adjustments_applied"] = applied[:6]
    adjusted["strategy_adjustment_penalty"] = penalty
    adjusted["strategy_adjustment_reason_zh"] = _strategy_adjustment_reason(applied)
    return adjusted


def _apply_single_play_concentration(ranked: list[dict], cfg: dict) -> list[dict]:
    play_counts: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    penalty_unit = float(cfg.get("single_play_concentration_penalty", 0.06))
    out = []
    for item in ranked:
        play = str(item.get("play_type") or "unknown")
        direction = f"{play}:{item.get('outcome_key') or item.get('outcome_label') or ''}"
        prior_play = play_counts[play]
        prior_direction = direction_counts[direction]
        penalty = round((max(0, prior_play - 1) + max(0, prior_direction - 1)) * penalty_unit, 6)
        adjusted = dict(item)
        if penalty:
            adjusted["score"] = round(float(adjusted.get("score") or 0.0) - penalty * 10.0, 6)
            adjusted["leg_quality_score"] = round(max(0.0, float(adjusted.get("leg_quality_score") or 0.0) - penalty * 0.35), 6)
        adjusted["play_concentration"] = {
            "play_type": play,
            "play_type_zh": _play_label(play),
            "prior_same_play_count": prior_play,
            "prior_same_direction_count": prior_direction,
            "penalty": penalty,
            "reason_zh": _single_concentration_reason(play, prior_play, prior_direction, penalty),
        }
        adjusted["play_concentration_reason_zh"] = adjusted["play_concentration"]["reason_zh"]
        out.append(adjusted)
        play_counts[play] += 1
        direction_counts[direction] += 1
    return sorted(out, key=lambda item: item.get("score", -999), reverse=True)


def _single_concentration_reason(play: str, prior_play: int, prior_direction: int, penalty: float) -> str:
    label = _play_label(play)
    if penalty > 0:
        return f"{label} 同类候选已出现 {prior_play} 次，同方向已出现 {prior_direction} 次；为避免单一玩法刷屏，排序已小幅降权。"
    if prior_play > 0:
        return f"{label} 已有同类候选，当前仍保留排序，后续若继续扎堆会降权。"
    return f"{label} 暂无拥挤惩罚。"


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
        "play_type": item.get("play_type"),
        "play_type_zh": item.get("play_type_mix_zh") or _play_label(item.get("play_type")),
        "direction": item.get("direction") or item.get("outcome_label"),
        "outcome_key": item.get("outcome_key"),
        "outcome_label": item.get("outcome_label") or item.get("direction"),
        "direction_family_zh": _combo_direction_summary(item) if item.get("legs") else _broad_direction_family(item),
        "leg_play_types": [_play_label(leg.get("play_type")) for leg in item.get("legs", []) or [] if isinstance(leg, dict)],
        "leg_directions": [str(leg.get("outcome_label") or leg.get("direction") or leg.get("outcome_key") or "") for leg in item.get("legs", []) or [] if isinstance(leg, dict)],
        "match": _label(item),
        "legs": _legs_label(item),
        "odds": item.get("odds") or item.get("combo_odds"),
        "model_prob": item.get("model_prob") or item.get("combo_prob"),
        "market_prob": item.get("market_prob"),
        "ev": item.get("ev"),
        "edge": item.get("edge"),
        "correlation_discount": item.get("correlation_discount", 1.0),
        "correlation_quality": item.get("correlation_quality", {}),
        "confidence_score": item.get("observation_confidence") or item.get("confidence_score"),
        "combo_score": item.get("combo_score"),
        "risk_adjusted_score": item.get("risk_adjusted_score"),
        "leg_quality_score": item.get("leg_quality_score"),
        "information_score": item.get("information_score"),
        "risk_penalty": item.get("risk_penalty"),
        "market_model_agreement": item.get("market_model_agreement"),
        "model_market_gap": item.get("model_market_gap"),
        "model_disagreement_penalty": item.get("model_disagreement_penalty"),
        "model_disagreement_reason_zh": item.get("model_disagreement_reason_zh", ""),
        "probability_shrinkage": item.get("probability_shrinkage", {}),
        "probability_shrinkage_reason_zh": item.get("probability_shrinkage_reason_zh", ""),
        "probability_shrinkage_weight": item.get("probability_shrinkage_weight", 0.0),
        "raw_model_prob": item.get("raw_model_prob"),
        "raw_ev": item.get("raw_ev"),
        "raw_edge": item.get("raw_edge"),
        "probability_lower": item.get("probability_lower"),
        "probability_upper": item.get("probability_upper"),
        "robust_edge": item.get("robust_edge"),
        "robust_ev": item.get("robust_ev"),
        "robust_value_status": item.get("robust_value_status"),
        "robust_value_label_zh": item.get("robust_value_label_zh", ""),
        "robust_value_reason_zh": item.get("robust_value_reason_zh", ""),
        "robustness_penalty": item.get("robustness_penalty", 0.0),
        "short_cycle_adjustment": item.get("short_cycle_adjustment", {}),
        "short_cycle_score_adjustment": item.get("short_cycle_score_adjustment", 0.0),
        "short_cycle_reason_zh": item.get("short_cycle_reason_zh", ""),
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
        "play_diversity": item.get("play_diversity", {}),
        "play_diversity_reason_zh": item.get("play_diversity_reason_zh", ""),
        "combo_homogeneity": item.get("combo_homogeneity", {}),
        "combo_homogeneity_reason_zh": item.get("combo_homogeneity_reason_zh", ""),
        "play_type_mix_zh": item.get("play_type_mix_zh", ""),
        "play_concentration": item.get("play_concentration", {}),
        "play_concentration_reason_zh": item.get("play_concentration_reason_zh", ""),
        "play_type_learning": item.get("play_type_learning", {}),
        "play_type_learning_reason_zh": item.get("play_type_learning_reason_zh", ""),
        "strategy_adjustments_applied": item.get("strategy_adjustments_applied", []),
        "strategy_adjustment_penalty": item.get("strategy_adjustment_penalty", 0.0),
        "strategy_adjustment_reason_zh": item.get("strategy_adjustment_reason_zh", ""),
        "competition_segment": item.get("competition_segment"),
        "competition_segment_zh": item.get("competition_segment_zh", ""),
        "competition_segment_reason_zh": item.get("competition_segment_reason_zh", ""),
        "ai_factor": item.get("ai_factor"),
        "ai_factor_zh": item.get("ai_factor_zh", ""),
        "ai_factor_reason_zh": item.get("ai_factor_reason_zh", ""),
        "risk_level": item.get("risk_level"),
        "paper_stake": item.get("suggested_paper_stake", 0.0),
        "longshot_warning": item.get("longshot_warning", ""),
        "parlay_eligible": item.get("parlay_eligible", True),
        "selected": bool(item.get("selected")),
        "status": "通过门控" if bool(item.get("selected")) else "未过门控",
        "reject_reason": item.get("reject_reason") or "未通过门控。",
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
                "reason": item.get("reject_reason", "未过门控"),
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
            "max_same_play_type_2x1": cfg.get("max_same_play_type_2x1"),
            "max_same_play_type_3x1": cfg.get("max_same_play_type_3x1"),
            "max_same_direction_2x1": cfg.get("max_same_direction_2x1"),
            "max_same_direction_3x1": cfg.get("max_same_direction_3x1"),
        },
        "portfolio_counts": {key: len(value) for key, value in portfolio.items()},
    }


def _explanations(portfolio: dict, exposure: float, cap: float, cfg: dict, no_2x1_reason: str) -> list[str]:
    return [
        f"当前风险档位：{cfg.get('risk_profile_label')}。每日纸面暴露上限为本金 {float(cfg.get('max_daily_exposure_pct', 0)):.1%}。",
        no_2x1_reason,
        f"串联命中率纪律：2串1 最低组合命中概率 {float(cfg.get('min_parlay_2x1_prob', 0)):.0%}，3串1 最低组合命中概率 {float(cfg.get('min_parlay_3x1_prob', 0)):.0%}，单腿可信度门槛 {float(cfg.get('min_leg_confidence', 0)):.0%}。",
        f"玩法分散纪律：2串1 不让两腿都来自同一玩法；3串1 同一玩法最多 {int(cfg.get('max_same_play_type_3x1', 2))} 腿，避免让球胜平负一类信号扎堆。",
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
    reasons = sorted({str(item.get("reject_reason") or "未通过门控") for item in parlay2_rankings if not item.get("selected")})
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


def _play_direction_key(leg: dict) -> str:
    play = str(leg.get("play_type") or "unknown")
    direction = str(leg.get("outcome_key") or leg.get("outcome_label") or leg.get("direction") or "unknown")
    return f"{play}:{_direction_family(direction)}"


def _broad_direction_family(leg: dict) -> str:
    direction = str(leg.get("outcome_key") or leg.get("outcome_label") or leg.get("direction") or "").lower()
    play = str(leg.get("play_type") or "").lower()
    if "handicap_home" in direction or "让胜" in direction or ("home" in direction and play == "hhad"):
        return "主队方向"
    if "home" in direction or "主胜" in direction or direction in {"h", "win"}:
        return "主队方向"
    if "handicap_away" in direction or "让负" in direction or ("away" in direction and play == "hhad"):
        return "客队方向"
    if "away" in direction or "客胜" in direction or direction in {"a", "lose"}:
        return "客队方向"
    if "handicap_draw" in direction or "让平" in direction or "draw" in direction or "平" in direction or direction in {"d"}:
        return "平局方向"
    if "over" in direction or "大" in direction:
        return "大球方向"
    if "under" in direction or "小" in direction:
        return "小球方向"
    return "未知方向"


def _combo_direction_summary(item: dict) -> str:
    labels = []
    for leg in item.get("legs", []) or []:
        if not isinstance(leg, dict):
            continue
        label = _broad_direction_family(leg)
        if label and label not in labels:
            labels.append(label)
    return " + ".join(labels[:4]) if labels else "未知方向"


def _direction_counts_text(counts: Counter) -> str:
    return "、".join(f"{key}×{count}" for key, count in counts.items() if count > 1) or "方向集中"


def _direction_family(direction: str) -> str:
    text = str(direction or "").lower()
    if "让胜" in text or "handicap_home" in text:
        return "让胜"
    if "让平" in text or "handicap_draw" in text:
        return "让平"
    if "让负" in text or "handicap_away" in text:
        return "让负"
    if "主胜" in text or "home" in text or text in {"h"}:
        return "主胜"
    if "客胜" in text or "away" in text or text in {"a"}:
        return "客胜"
    if "平" in text or "draw" in text or text in {"d"}:
        return "平"
    if "大" in text or "over" in text:
        return "大球"
    if "小" in text or "under" in text:
        return "小球"
    return str(direction or "未知方向")


def _combo_homogeneity_reason(
    hard_block: bool,
    direction_counts: Counter,
    broad_direction_counts: Counter,
    odds_bucket_counts: Counter,
    ai_factor_counts: Counter,
    signal_counts: Counter,
    penalty: float,
) -> str:
    repeated = []
    repeated.extend([f"同玩法同方向 {key}×{count}" for key, count in direction_counts.items() if count > 1])
    repeated.extend([f"同大方向 {key}×{count}" for key, count in broad_direction_counts.items() if key != "未知方向" and count > 1])
    repeated.extend([f"同赔率段 {key}×{count}" for key, count in odds_bucket_counts.items() if key != "unknown" and count > 1])
    repeated.extend([f"同AI因子 {key}×{count}" for key, count in ai_factor_counts.items() if key != "unknown" and count > 1])
    repeated.extend([f"同信号类别 {key}×{count}" for key, count in signal_counts.items() if key != "unknown" and count > 1])
    if hard_block:
        return "组合逻辑过于同质化：" + "；".join(repeated[:4]) + "。不是不同比赛就一定分散，暂不升级为优秀串联。"
    if penalty > 0:
        return "组合存在隐性同质化：" + "；".join(repeated[:4]) + "。已降权，需赛后验证这类拼法是否真的有效。"
    return "组合玩法、方向、赔率段和解释因子相对分散。"


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct_text(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value) * 100:.1f}%"

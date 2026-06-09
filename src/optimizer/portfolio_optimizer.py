from __future__ import annotations

from src.optimizer.candidate_pool import build_parlay_candidates
from src.optimizer.constraints import merge_config, risk_allowed
from src.optimizer.scoring import score_candidate


def optimize_portfolio(candidates: list[dict], bankroll: float = 10000.0, config: dict | None = None) -> dict:
    cfg = merge_config({**(config or {}), "bankroll": bankroll})
    rejected: list[dict] = []
    singles_scored = []
    for candidate in candidates:
        checked = _check_candidate(candidate, cfg)
        if checked:
            rejected.append({**candidate, "reject_reason": checked})
            continue
        singles_scored.append(score_candidate(candidate, bankroll, cfg))
    singles_scored = sorted(singles_scored, key=lambda item: item["score"], reverse=True)

    max_legs = 3 if cfg.get("enable_3x1") else 2
    parlay_raw = build_parlay_candidates(singles_scored, max_legs=max_legs)
    parlay_scored = []
    for candidate in parlay_raw:
        if candidate.get("rejected"):
            rejected.append(candidate)
            continue
        if candidate["candidate_type"] == "parlay_3x1" and not cfg.get("enable_3x1"):
            rejected.append({**candidate, "reject_reason": "3串1 默认关闭"})
            continue
        checked = _check_candidate(candidate, cfg)
        if checked:
            rejected.append({**candidate, "reject_reason": checked})
            continue
        parlay_scored.append(score_candidate(candidate, bankroll, cfg))
    parlay_scored = sorted(parlay_scored, key=lambda item: item["score"], reverse=True)

    portfolio = {"singles": [], "parlay_2x1": [], "parlay_3x1": []}
    exposure = 0.0
    cap = float(cfg["daily_exposure_cap"])
    exposure = _add_limited(portfolio["singles"], singles_scored, int(cfg["max_singles"]), exposure, cap)
    exposure = _add_limited(portfolio["parlay_2x1"], [item for item in parlay_scored if item["candidate_type"] == "parlay_2x1"], int(cfg["max_parlay_2x1"]), exposure, cap)
    if cfg.get("enable_3x1"):
        exposure = _add_limited(portfolio["parlay_3x1"], [item for item in parlay_scored if item["candidate_type"] == "parlay_3x1"], int(cfg["max_parlay_3x1"]), exposure, cap)
    return {
        "bankroll": round(float(bankroll), 2),
        "daily_exposure_cap": round(cap, 2),
        "recommended_paper_exposure": round(exposure, 2),
        "recommended_observation_portfolio": portfolio,
        "rejected_candidates": _rejected_summary(rejected[:80]),
        "risk_summary": _risk_summary(portfolio, exposure, cap, cfg),
        "explanations": _explanations(portfolio, exposure, cap),
        "disclaimer": "仅供概率研究，不构成投注建议。本工具不提供投注、下单、支付、代购或自动化购彩能力。",
    }


def _check_candidate(candidate: dict, cfg: dict) -> str:
    if float(candidate.get("ev") or 0.0) < float(cfg["min_ev"]):
        return "EV 不足"
    if float(candidate.get("edge") or 0.0) < float(cfg["min_edge"]):
        return "Edge 不足"
    if not risk_allowed(str(candidate.get("risk_level", "medium")), str(cfg["max_risk"])):
        return "风险等级过高"
    odds = float(candidate.get("odds") or candidate.get("combo_odds") or 0.0)
    if odds <= 1.01:
        return "赔率过低"
    if float(candidate.get("correlation_discount") or 1.0) <= 0:
        return "相关性过强"
    return ""


def _add_limited(target: list, items: list[dict], limit: int, exposure: float, cap: float) -> float:
    for item in items:
        if len(target) >= limit:
            break
        stake = float(item.get("suggested_paper_stake") or 0.0)
        if stake <= 0:
            continue
        if exposure + stake > cap:
            continue
        target.append(item)
        exposure += stake
    return exposure


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
                "reason": item.get("reject_reason", "未入选"),
            }
        )
    return rows


def _risk_summary(portfolio: dict, exposure: float, cap: float, cfg: dict) -> dict:
    return {
        "exposure_used": round(exposure, 2),
        "exposure_cap": round(cap, 2),
        "exposure_usage_pct": round(exposure / cap, 6) if cap > 0 else 0.0,
        "max_risk": cfg.get("max_risk"),
        "enable_3x1": bool(cfg.get("enable_3x1")),
        "portfolio_counts": {key: len(value) for key, value in portfolio.items()},
    }


def _explanations(portfolio: dict, exposure: float, cap: float) -> list[str]:
    return [
        "为什么没有更激进：默认每日纸面暴露不超过本金 3%，单关 1%，2串1 0.5%，3串1 默认关闭。",
        "如果想提高纸面收益，需要提高风险暴露或放宽风险等级，但这会增加回撤和连续亏损概率。",
        "10000 元模拟只赚约 180 元，主要因为投入比例保守、候选数量有限、组合数量少，且 fixture 不是真实生产数据。",
        f"当前推荐纸面投入 {exposure:.2f} / 上限 {cap:.2f}，未用满也可能是因为候选 EV、Edge、风险或相关性约束不足。",
        "当前结果不是实盘建议，也不会改变概率、EV 或候选筛选逻辑。",
    ]


def _label(item: dict) -> str:
    if item.get("legs"):
        return "；".join(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}".strip() for leg in item.get("legs", []))
    return f"{item.get('home_team','')} vs {item.get('away_team','')} {item.get('outcome_label','')}".strip()

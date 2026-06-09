from __future__ import annotations

from itertools import combinations

DEFAULT_SELECTION_CONFIG = {
    "max_single_per_day": 2,
    "max_parlay_2x1_per_day": 1,
    "max_parlay_3x1_per_day": 0,
    "min_ev": 0.04,
    "min_edge": 0.025,
    "max_risk_level": "medium",
}

DEFAULT_STAKE_CONFIG = {
    "single_stake_pct": 0.01,
    "parlay_2x1_stake_pct": 0.005,
    "parlay_3x1_stake_pct": 0.0025,
    "max_total_daily_stake_pct": 0.03,
    "min_stake": 10.0,
    "round_to": 2.0,
}

_RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "very_high": 4}


def select_daily_observations(analysis: dict, config: dict | None = None) -> dict:
    cfg = {**DEFAULT_SELECTION_CONFIG, **(config or {})}
    max_risk = _RISK_ORDER.get(str(cfg.get("max_risk_level", "medium")), 2)
    singles = []
    skipped = []
    for item in list(analysis.get("single_candidates", []) or []):
        if _risk_rank(item) > max_risk:
            skipped.append({"type": "single", "reason": "风险等级高于策略上限", "item": _label(item)})
            continue
        if float(item.get("ev") or 0.0) < float(cfg["min_ev"]):
            skipped.append({"type": "single", "reason": "EV 低于阈值", "item": _label(item)})
            continue
        if float(item.get("edge") or 0.0) < float(cfg["min_edge"]):
            skipped.append({"type": "single", "reason": "Edge 低于阈值", "item": _label(item)})
            continue
        enriched = {**item, "observation_type": "single", "selection_reason": "EV、Edge 和风险等级满足纸面观察策略。"}
        singles.append(enriched)
    singles = sorted(singles, key=lambda item: (float(item.get("ev") or 0.0), float(item.get("edge") or 0.0)), reverse=True)
    singles = singles[: int(cfg["max_single_per_day"])]

    parlay_2 = _select_parlays(analysis.get("parlay_2x1_candidates", []) or [], int(cfg["max_parlay_2x1_per_day"]), max_risk, "parlay_2x1")
    parlay_3 = _select_parlays(analysis.get("parlay_3x1_candidates", []) or [], int(cfg["max_parlay_3x1_per_day"]), max_risk, "parlay_3x1")
    return {"singles": singles, "parlay_2x1": parlay_2, "parlay_3x1": parlay_3, "skipped": skipped, "warnings": []}


def allocate_paper_stakes(observations: dict, bankroll: float, config: dict | None = None) -> list[dict]:
    cfg = {**DEFAULT_STAKE_CONFIG, **(config or {})}
    current_bankroll = max(0.0, float(bankroll or 0.0))
    if current_bankroll <= 0:
        return []
    daily_cap = current_bankroll * float(cfg["max_total_daily_stake_pct"])
    allocated = 0.0
    result: list[dict] = []
    ordered = []
    ordered.extend(("single", item) for item in observations.get("singles", []) or [])
    ordered.extend(("parlay_2x1", item) for item in observations.get("parlay_2x1", []) or [])
    ordered.extend(("parlay_3x1", item) for item in observations.get("parlay_3x1", []) or [])
    for kind, item in ordered:
        pct = float(cfg["single_stake_pct"] if kind == "single" else cfg["parlay_2x1_stake_pct"] if kind == "parlay_2x1" else cfg["parlay_3x1_stake_pct"])
        desired = max(float(cfg["min_stake"]), current_bankroll * pct)
        remaining = max(0.0, daily_cap - allocated)
        if remaining < float(cfg["min_stake"]):
            break
        stake = min(desired, remaining)
        stake = _round_to(stake, float(cfg["round_to"]))
        if stake <= 0:
            continue
        allocated += stake
        result.append({**item, "paper_stake": stake, "stake_reason": _stake_reason(kind, pct, cfg["max_total_daily_stake_pct"])})
    return result


def build_parlay_candidates(single_candidates: list[dict], max_size: int = 3) -> dict:
    clean = [item for item in single_candidates if item.get("match_id")]
    parlay_2 = [_parlay_from_legs(legs, "2x1") for legs in combinations(clean[:6], 2)]
    parlay_3 = [_parlay_from_legs(legs, "3x1") for legs in combinations(clean[:6], 3)] if max_size >= 3 else []
    parlay_2 = [item for item in parlay_2 if item]
    parlay_3 = [item for item in parlay_3 if item]
    return {
        "parlay_2x1_candidates": sorted(parlay_2, key=lambda item: item.get("ev", 0), reverse=True),
        "parlay_3x1_candidates": sorted(parlay_3, key=lambda item: item.get("ev", 0), reverse=True),
    }


def _select_parlays(items, limit: int, max_risk: int, kind: str) -> list[dict]:
    selected = []
    for item in sorted(list(items), key=lambda row: float(row.get("ev") or 0.0), reverse=True):
        if len(selected) >= limit:
            break
        if _risk_rank(item) > max_risk:
            continue
        selected.append({**item, "observation_type": kind, "selection_reason": "组合 EV 与风险等级满足纸面观察策略。"})
    return selected


def _parlay_from_legs(legs, pass_type: str) -> dict:
    combined_odds = 1.0
    hit_probability = 1.0
    market_probability = 1.0
    risk_level = "medium"
    for leg in legs:
        combined_odds *= float(leg.get("odds") or 0.0)
        hit_probability *= float(leg.get("model_prob") or 0.0)
        market_probability *= float(leg.get("fair_prob") or 0.0)
        if _risk_rank(leg) >= 3:
            risk_level = "high"
    if combined_odds <= 1 or hit_probability <= 0:
        return {}
    return {
        "pass_type": pass_type,
        "legs": [dict(leg) for leg in legs],
        "combined_odds": round(combined_odds, 4),
        "hit_probability": round(hit_probability, 6),
        "market_probability": round(market_probability, 6),
        "ev": round(hit_probability * combined_odds - 1.0, 6),
        "risk_level": risk_level,
        "risk_label": "中" if risk_level == "medium" else "高",
        "explanation": "组合观察会叠加多个不确定事件，需重点关注命中概率和回撤。",
    }


def _risk_rank(item: dict) -> int:
    return _RISK_ORDER.get(str(item.get("risk_level", "medium")).lower(), 2)


def _label(item: dict) -> str:
    return f"{item.get('home_team', '')} vs {item.get('away_team', '')}".strip()


def _round_to(value: float, unit: float) -> float:
    if unit <= 0:
        return round(value, 2)
    return round(round(value / unit) * unit, 2)


def _stake_reason(kind: str, pct: float, daily_pct: float) -> str:
    zh = {"single": "单关", "parlay_2x1": "2串1", "parlay_3x1": "3串1"}.get(kind, "观察项")
    return f"{zh}模拟金额按当前纸面本金的 {pct:.2%} 估算，且每日总模拟投入不超过 {daily_pct:.2%}。这是纸面资金管理，不是资金建议。"

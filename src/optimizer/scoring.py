from __future__ import annotations

from src.optimizer.constraints import stake_cap_for


def score_candidate(candidate: dict, bankroll: float, config: dict | None = None) -> dict:
    cfg = config or {}
    kind = candidate.get("candidate_type", "single")
    odds = _odds(candidate)
    probability = _probability(candidate)
    ev = float(candidate.get("ev") or 0.0)
    edge = float(candidate.get("edge") or 0.0)
    kelly_fraction = _kelly_fraction(probability, odds)
    cap = stake_cap_for(kind, bankroll, cfg)
    kelly_stake = float(bankroll) * max(0.0, kelly_fraction) * float(cfg.get("kelly_multiplier", 0.25))
    suggested = round(min(cap, max(0.0, kelly_stake)), 2)
    if ev > 0 and suggested <= 0:
        suggested = min(cap, max(10.0, cap * 0.25))
    score = ev * 100 + edge * 20 + min(kelly_fraction, 0.25) * 10
    return {
        **candidate,
        "score": round(score, 6),
        "kelly_fraction": round(kelly_fraction, 6),
        "suggested_paper_stake": round(suggested, 2),
        "stake_cap": round(cap, 2),
        "stake_reason": "按 1/4 Kelly 参考值估算，并受单项上限与每日总暴露约束。这是纸面投入，不是资金建议。",
        "selection_reason": _selection_reason(kind, ev, edge, candidate.get("risk_level")),
    }


def _odds(candidate: dict) -> float:
    return float(candidate.get("odds") or candidate.get("combo_odds") or 0.0)


def _probability(candidate: dict) -> float:
    return float(candidate.get("model_prob") or candidate.get("combo_prob") or 0.0)


def _kelly_fraction(probability: float, odds: float) -> float:
    if odds <= 1:
        return 0.0
    return (probability * odds - 1.0) / (odds - 1.0)


def _selection_reason(kind: str, ev: float, edge: float, risk: str | None) -> str:
    label = {"single": "单关观察", "parlay_2x1": "2串1 组合观察", "parlay_3x1": "3串1 组合观察"}.get(kind, kind)
    return f"{label}满足 EV {ev:.2%}、Edge {edge:.2%} 与风险等级 {risk or 'medium'} 的约束。"

from __future__ import annotations

from src.optimizer.constraints import stake_cap_for


def score_candidate(candidate: dict, bankroll: float, config: dict | None = None) -> dict:
    cfg = config or {}
    kind = candidate.get("candidate_type", "single")
    odds = _odds(candidate)
    probability = _probability(candidate)
    ev = float(candidate.get("ev") or 0.0)
    edge = float(candidate.get("edge") or 0.0)
    longshot = odds >= 6.0
    if longshot:
        candidate = {**candidate, "risk_level": "very_high"}
    confidence = float(candidate.get("observation_confidence") or candidate.get("confidence_score") or 0.45)
    market_prob = float(candidate.get("market_prob") or 0.0)
    correlation_discount = float(candidate.get("correlation_discount") or 1.0)
    risk_level = str(candidate.get("risk_level") or "medium")
    risk_penalty = {"low": 0.0, "medium": 0.08, "high": 0.18, "very_high": 0.32}.get(risk_level, 0.1)
    market_model_agreement = max(0.0, 1.0 - min(1.0, abs(probability - market_prob) * 4)) if probability and market_prob else 0.35
    odds_quality = min(1.0, odds / 5.0) if odds else 0.0
    normalized_ev = max(-1.0, min(1.0, ev / 0.25)) if ev else 0.0
    drawdown_safety = max(0.0, 1.0 - risk_penalty)
    combo_score = (
        0.35 * normalized_ev
        + 0.20 * confidence
        + 0.15 * market_model_agreement
        + 0.10 * odds_quality
        + 0.10 * max(0.0, min(1.0, correlation_discount))
        + 0.10 * drawdown_safety
    )
    risk_adjusted_score = combo_score - risk_penalty
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
        "combo_score": round(combo_score, 6),
        "risk_adjusted_score": round(risk_adjusted_score, 6),
        "market_model_agreement": round(market_model_agreement, 6),
        "odds_quality": round(odds_quality, 6),
        "drawdown_safety": round(drawdown_safety, 6),
        "kelly_fraction": round(kelly_fraction, 6),
        "suggested_paper_stake": round(suggested, 2),
        "stake_cap": round(cap, 2),
        "stake_reason": "按 1/4 Kelly 参考值估算，并受单项上限与每日总暴露约束。这是纸面投入，不是资金建议。",
        "selection_reason": _selection_reason(kind, ev, edge, candidate.get("risk_level")),
        "longshot_warning": "这是高赔率冷门观察，不是稳健信号；除非可信度充分补齐，否则不适合作为串联核心。" if longshot else "",
        "parlay_eligible": not longshot,
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

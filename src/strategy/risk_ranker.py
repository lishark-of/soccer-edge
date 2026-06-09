from __future__ import annotations

from math import prod

from src.domain.match import Match
from src.domain.odds import OddsHistory
from src.domain.selection import Selection


def score_selection_risk(
    match: Match,
    odds: float,
    confidence: float,
    odds_history: OddsHistory | None = None,
) -> tuple[float, str, list[str]]:
    sample_size = float(match.metadata.get("historical_sample_size", 10))
    league_uncertainty = float(match.metadata.get("league_uncertainty", 0.15))
    odds_risk = min(1.0, max(0.0, (odds - 1.30) / 3.50))
    model_uncertainty = max(0.0, min(1.0, 1.0 - confidence))
    volatility = _market_volatility(odds_history)
    sample_size_penalty = max(0.0, 1.0 - min(sample_size, 25.0) / 25.0)
    risk_score = (
        odds_risk * 0.28
        + model_uncertainty * 0.24
        + volatility * 0.18
        + sample_size_penalty * 0.14
        + league_uncertainty * 0.16
    )
    level = _risk_level(risk_score)
    reasons: list[str] = []
    if odds >= 3.50:
        reasons.append("赔率偏高，冷门属性强。")
    if confidence < 0.54:
        reasons.append("模型置信度偏低。")
    if volatility >= 0.08:
        reasons.append("赔率波动偏大。")
    if sample_size < 15:
        reasons.append("历史样本不足。")
    if league_uncertainty >= 0.2:
        reasons.append("联赛不确定性较高。")
    if not reasons:
        reasons.append("风险处于可控范围，但仍需谨慎。")
    return round(risk_score, 4), level, reasons


def score_parlay_risk(selections: list[Selection], correlation_penalty: float) -> tuple[float, str, list[str]]:
    if not selections:
        return 1.0, "very_high", ["组合为空。"]
    base = sum(selection.risk_score for selection in selections) / len(selections)
    leg_penalty = max(0.0, (len(selections) - 1) * 0.11)
    combined_odds = prod(selection.odds for selection in selections)
    odds_penalty = min(0.25, max(0.0, (combined_odds - 2.0) / 20.0))
    risk_score = min(1.0, base + leg_penalty + correlation_penalty + odds_penalty)
    reasons = [
        "串关会显著放大风险。",
        f"组合腿数={len(selections)}，命中概率下降。",
    ]
    if correlation_penalty > 0:
        reasons.append("组合腿存在相关性折扣。")
    if combined_odds >= 4.0:
        reasons.append("组合赔率较高，波动明显放大。")
    return round(risk_score, 4), _risk_level(risk_score), reasons


def _market_volatility(odds_history: OddsHistory | None) -> float:
    if odds_history is None or not odds_history.history:
        return 0.02
    spreads: list[float] = []
    for points in odds_history.history.values():
        home_values = [point.outcomes["home"] for point in points]
        if len(home_values) >= 2:
            spreads.append((max(home_values) - min(home_values)) / max(home_values))
    if not spreads:
        return 0.02
    return min(1.0, max(spreads))


def _risk_level(score: float) -> str:
    if score < 0.28:
        return "low"
    if score < 0.48:
        return "medium"
    if score < 0.68:
        return "high"
    return "very_high"

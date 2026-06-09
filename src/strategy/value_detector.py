from __future__ import annotations

from src.domain.analysis_result import MatchAnalysis
from src.domain.match import Match
from src.domain.selection import Selection
from src.rules.play_types import outcome_label


def calculate_edge(model_probability: float, fair_probability: float) -> float:
    return round(model_probability - fair_probability, 6)


def calculate_ev(model_probability: float, odds: float) -> float:
    return round(model_probability * odds - 1.0, 6)


def analyze_market_outcomes(
    match: Match,
    play_type: str,
    odds: dict[str, float],
    fair_probabilities: dict[str, float],
    model_probabilities: dict[str, float],
    confidence: float,
    risk_level: str,
    risk_score: float,
    risk_reasons: list[str],
    model_reasons: list[str],
) -> list[MatchAnalysis]:
    analyses: list[MatchAnalysis] = []
    for outcome_key, outcome_odds in odds.items():
        fair_prob = fair_probabilities[outcome_key]
        model_prob = model_probabilities[outcome_key]
        edge = calculate_edge(model_prob, fair_prob)
        ev = calculate_ev(model_prob, outcome_odds)
        risks = list(risk_reasons)
        if outcome_odds >= 3.50:
            risks.append("赔率偏高，冷门属性强。")
        selection = Selection(
            match_id=match.match_id,
            match_no=match.match_no,
            league=match.league,
            home_team=match.home_team,
            away_team=match.away_team,
            play_type=play_type,
            outcome_key=outcome_key,
            outcome_label=outcome_label(play_type, outcome_key),
            odds=round(outcome_odds, 4),
            fair_prob=round(fair_prob, 6),
            model_prob=round(model_prob, 6),
            edge=edge,
            ev=ev,
            confidence=confidence,
            risk_level=risk_level,
            risk_score=round(risk_score, 4),
            reasons=list(model_reasons),
            risks=risks,
            supports_single=match.supports_single,
            correlation_group=match.correlation_group,
        )
        analyses.append(
            MatchAnalysis(
                selection=selection,
                recommended_use=_recommended_use(selection),
            )
        )
    return analyses


def _recommended_use(selection: Selection) -> str:
    if selection.ev >= 0.08 and selection.edge >= 0.04 and selection.confidence >= 0.60 and selection.odds >= 1.45:
        return "单关候选"
    if selection.ev >= 0.04 and selection.edge >= 0.025:
        if selection.risk_level in {"low", "medium"} and selection.supports_single and selection.odds >= 1.45:
            return "单关候选"
        return "2串候选"
    if selection.ev > 0:
        if selection.odds >= 3.50 or selection.risk_level in {"high", "very_high"}:
            return "仅观察"
        return "3串候选"
    return "放弃"

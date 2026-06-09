from __future__ import annotations

from src.domain.match import Match
from src.domain.odds import MarketOdds, OddsHistory


def _normalize(probabilities: dict[str, float]) -> dict[str, float]:
    total = sum(max(value, 0.0001) for value in probabilities.values())
    return {
        key: round(max(value, 0.0001) / total, 6)
        for key, value in probabilities.items()
    }


def _movement_adjustment(play_type: str, history: OddsHistory | None) -> tuple[float, float]:
    if history is None or play_type not in history.history:
        return 0.0, 0.0
    points = history.history[play_type]
    if len(points) < 2:
        return 0.0, 0.0
    first = points[0].outcomes
    last = points[-1].outcomes
    home_shift = first["home"] - last["home"]
    away_shift = first["away"] - last["away"]
    return home_shift * 0.01, away_shift * 0.01


def build_model_probabilities(
    match: Match,
    market: MarketOdds,
    fair_probabilities: dict[str, float],
    odds_history: OddsHistory | None = None,
) -> tuple[dict[str, float], float, list[str]]:
    home_rating = float(match.metadata.get("home_rating", 50))
    away_rating = float(match.metadata.get("away_rating", 50))
    draw_bias = float(match.metadata.get("draw_bias", 0.04))
    rating_gap = home_rating - away_rating
    home_adj = rating_gap / 85.0
    away_adj = -home_adj * 0.85
    draw_adj = draw_bias - abs(rating_gap) / 400.0
    move_home, move_away = _movement_adjustment(market.play_type, odds_history)

    model = {
        "home": fair_probabilities["home"] + home_adj + move_home,
        "draw": fair_probabilities["draw"] + draw_adj * (0.7 if market.play_type == "had" else 0.45),
        "away": fair_probabilities["away"] + away_adj + move_away,
    }

    if market.play_type == "hhad" and market.handicap is not None and market.handicap < 0:
        model["draw"] = max(0.04, model["draw"] - 0.02)
        model["away"] = max(0.04, model["away"] + 0.015)

    normalized = _normalize(model)
    confidence = round(max(normalized.values()), 6)
    reasons = [
        f"市场去水概率作为基线，玩法={market.play_type}",
        f"主客队强度差调整={round(home_adj, 4)}",
        f"赔率历史微调 home={round(move_home, 4)} away={round(move_away, 4)}",
    ]
    return normalized, confidence, reasons

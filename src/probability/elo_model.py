from __future__ import annotations

import math

from src.backtesting.historical_loader import HistoricalMatch
from src.modeling.features import historical_matches_before_date


DEFAULT_INITIAL_RATING = 1500.0
DEFAULT_K = 20.0
DEFAULT_HOME_ADVANTAGE = 60.0


def expected_score(
    rating_a: float,
    rating_b: float,
) -> float:
    return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))


def update_elo(
    home_rating: float,
    away_rating: float,
    result: str,
    k: float = DEFAULT_K,
    home_advantage: float = DEFAULT_HOME_ADVANTAGE,
) -> tuple[float, float]:
    normalized = result.strip().upper()
    if normalized not in {"H", "D", "A"}:
        raise ValueError("result must be one of H, D, A")
    expected_home = expected_score(home_rating + home_advantage, away_rating)
    actual_home = {"H": 1.0, "D": 0.5, "A": 0.0}[normalized]
    delta = k * (actual_home - expected_home)
    return round(home_rating + delta, 6), round(away_rating - delta, 6)


def build_elo_ratings(
    historical_matches: list[HistoricalMatch],
    before_date: str,
    initial_rating: float = DEFAULT_INITIAL_RATING,
    k: float = DEFAULT_K,
    home_advantage: float = DEFAULT_HOME_ADVANTAGE,
) -> dict[str, float]:
    ratings: dict[str, float] = {}
    for match in historical_matches_before_date(historical_matches, before_date):
        ratings.setdefault(match.home_team, initial_rating)
        ratings.setdefault(match.away_team, initial_rating)
        new_home, new_away = update_elo(
            ratings[match.home_team],
            ratings[match.away_team],
            match.result_1x2,
            k=k,
            home_advantage=home_advantage,
        )
        ratings[match.home_team] = new_home
        ratings[match.away_team] = new_away
    return {team: round(rating, 6) for team, rating in ratings.items()}


def elo_to_1x2_probs(
    home_rating: float,
    away_rating: float,
    draw_base: float = 0.26,
    home_advantage: float = DEFAULT_HOME_ADVANTAGE,
) -> dict[str, float]:
    expected_home_value = expected_score(home_rating + home_advantage, away_rating)
    gap = abs(expected_home_value - 0.5)
    draw_probability = max(0.12, min(0.32, draw_base - gap * 0.35))
    remaining = 1.0 - draw_probability
    win_probability = remaining * expected_home_value
    lose_probability = remaining * (1.0 - expected_home_value)
    total = win_probability + draw_probability + lose_probability
    return {
        "win": round(win_probability / total, 6),
        "draw": round(draw_probability / total, 6),
        "lose": round(lose_probability / total, 6),
    }

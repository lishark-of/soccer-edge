from __future__ import annotations

import math


def poisson_pmf(k: int, lam: float) -> float:
    if k < 0:
        raise ValueError("k must be >= 0")
    if lam <= 0:
        raise ValueError("lam must be > 0")
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def scoreline_distribution(
    home_xg: float,
    away_xg: float,
    max_goals: int = 8,
) -> dict[tuple[int, int], float]:
    if home_xg <= 0 or away_xg <= 0:
        raise ValueError("home_xg and away_xg must be > 0")
    if max_goals < 1:
        raise ValueError("max_goals must be >= 1")

    distribution: dict[tuple[int, int], float] = {}
    total = 0.0
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            probability = poisson_pmf(home_goals, home_xg) * poisson_pmf(away_goals, away_xg)
            distribution[(home_goals, away_goals)] = probability
            total += probability
    if total <= 0:
        raise ValueError("distribution total must be > 0")
    return {scoreline: probability / total for scoreline, probability in distribution.items()}


def derive_1x2_probs(scoreline_dist: dict[tuple[int, int], float]) -> dict[str, float]:
    win = 0.0
    draw = 0.0
    lose = 0.0
    for (home_goals, away_goals), probability in scoreline_dist.items():
        if home_goals > away_goals:
            win += probability
        elif home_goals == away_goals:
            draw += probability
        else:
            lose += probability
    return _normalize({"win": win, "draw": draw, "lose": lose})


def derive_total_goals_probs(scoreline_dist: dict[tuple[int, int], float]) -> dict[str, float]:
    over = 0.0
    under = 0.0
    for (home_goals, away_goals), probability in scoreline_dist.items():
        if home_goals + away_goals > 2.5:
            over += probability
        else:
            under += probability
    return _normalize({"over_2_5": over, "under_2_5": under})


def derive_handicap_probs(
    scoreline_dist: dict[tuple[int, int], float],
    handicap: float,
) -> dict[str, float]:
    win = 0.0
    draw = 0.0
    lose = 0.0
    for (home_goals, away_goals), probability in scoreline_dist.items():
        adjusted = home_goals + handicap - away_goals
        if adjusted > 0:
            win += probability
        elif adjusted < 0:
            lose += probability
        else:
            draw += probability
    return _normalize({"win": win, "draw": draw, "lose": lose})


def _normalize(probabilities: dict[str, float]) -> dict[str, float]:
    total = sum(probabilities.values())
    if total <= 0:
        raise ValueError("probabilities must sum to > 0")
    return {key: round(value / total, 6) for key, value in probabilities.items()}

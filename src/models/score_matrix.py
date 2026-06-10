from __future__ import annotations

import math


def poisson_pmf(lam: float, max_goals: int = 8) -> list[float]:
    lam = max(0.05, float(lam or 0.05))
    probs = [math.exp(-lam) * lam**k / math.factorial(k) for k in range(max_goals + 1)]
    total = sum(probs) or 1.0
    return [value / total for value in probs]


def build_score_matrix(home_xg: float, away_xg: float, max_goals: int = 8) -> dict[tuple[int, int], float]:
    home = poisson_pmf(home_xg, max_goals)
    away = poisson_pmf(away_xg, max_goals)
    matrix = {(h, a): home[h] * away[a] for h in range(max_goals + 1) for a in range(max_goals + 1)}
    return normalize_matrix(matrix)


def normalize_matrix(matrix: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
    total = sum(max(0.0, value) for value in matrix.values()) or 1.0
    return {score: max(0.0, value) / total for score, value in matrix.items()}


def outcome_probabilities(matrix: dict[tuple[int, int], float]) -> dict[str, float]:
    probs = {"home": 0.0, "draw": 0.0, "away": 0.0}
    for (home, away), prob in matrix.items():
        if home > away:
            probs["home"] += prob
        elif home == away:
            probs["draw"] += prob
        else:
            probs["away"] += prob
    return normalize_probs(probs)


def handicap_probabilities(matrix: dict[tuple[int, int], float], handicap: float | None) -> dict[str, float]:
    if handicap is None:
        return outcome_probabilities(matrix)
    probs = {"home": 0.0, "draw": 0.0, "away": 0.0}
    for (home, away), prob in matrix.items():
        adjusted = home + float(handicap)
        if adjusted > away:
            probs["home"] += prob
        elif adjusted == away:
            probs["draw"] += prob
        else:
            probs["away"] += prob
    return normalize_probs(probs)


def total_goals_distribution(matrix: dict[tuple[int, int], float], max_bucket: int = 7) -> dict[str, float]:
    dist = {str(i): 0.0 for i in range(max_bucket)}
    dist[f"{max_bucket}+"] = 0.0
    for (home, away), prob in matrix.items():
        goals = home + away
        key = str(goals) if goals < max_bucket else f"{max_bucket}+"
        dist[key] += prob
    return normalize_probs(dist)


def top_scores(matrix: dict[tuple[int, int], float], n: int = 5) -> list[dict]:
    return [
        {"score": f"{home}-{away}", "home_goals": home, "away_goals": away, "probability": round(prob, 6)}
        for (home, away), prob in sorted(matrix.items(), key=lambda item: item[1], reverse=True)[:n]
    ]


def normalize_probs(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(value or 0.0)) for value in values.values()) or 1.0
    return {key: round(max(0.0, float(value or 0.0)) / total, 6) for key, value in values.items()}

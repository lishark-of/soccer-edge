from __future__ import annotations

from src.models.score_matrix import normalize_matrix

LOW_SCORE_FACTORS = {
    (0, 0): 1.08,
    (1, 0): 0.96,
    (0, 1): 0.96,
    (1, 1): 1.04,
}


def apply_dixon_coles_adjustment(matrix: dict[tuple[int, int], float], rho: float = 0.08) -> dict[tuple[int, int], float]:
    rho = max(0.0, min(0.25, float(rho or 0.0)))
    adjusted = {}
    for score, prob in matrix.items():
        factor = LOW_SCORE_FACTORS.get(score, 1.0)
        adjusted[score] = prob * (1.0 + (factor - 1.0) * (rho / 0.08 if rho else 0.0))
    return normalize_matrix(adjusted)

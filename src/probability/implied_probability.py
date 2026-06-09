from __future__ import annotations


def calculate_implied_probabilities(odds: dict[str, float]) -> dict[str, float]:
    implied = {}
    for key, value in odds.items():
        if value <= 0:
            raise ValueError(f"Odds must be positive for {key}")
        implied[key] = 1.0 / value
    return implied

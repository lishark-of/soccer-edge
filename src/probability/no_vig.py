from __future__ import annotations


def remove_vig(implied_probabilities: dict[str, float]) -> dict[str, float]:
    total = sum(implied_probabilities.values())
    if total <= 0:
        raise ValueError("Implied probabilities must sum to a positive value")
    return {key: value / total for key, value in implied_probabilities.items()}

from __future__ import annotations


def no_vig_probs(odds: dict[str, float | None] | None) -> dict[str, float]:
    odds = odds or {}
    implied = {}
    for key, value in odds.items():
        if key == "handicap":
            continue
        try:
            odd = float(value)
        except (TypeError, ValueError):
            continue
        if odd > 1.01:
            normalized_key = {"win": "home", "lose": "away"}.get(key, key)
            implied[normalized_key] = 1.0 / odd
    total = sum(implied.values()) or 1.0
    return {key: round(value / total, 6) for key, value in implied.items()}


def odds_for_outcome(odds: dict[str, float | None] | None, outcome: str) -> float | None:
    odds = odds or {}
    key = {"home": "win", "away": "lose", "draw": "draw"}.get(outcome, outcome)
    value = odds.get(key)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None

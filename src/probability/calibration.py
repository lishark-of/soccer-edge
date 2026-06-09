from __future__ import annotations


def apply_reliability_adjustment(
    probs: dict,
    calibration_table: dict | None = None,
) -> dict:
    del calibration_table
    normalized = {key: max(0.0, float(value)) for key, value in probs.items()}
    total = sum(normalized.values())
    if total <= 0:
        return {key: round(1.0 / len(normalized), 6) for key in normalized}
    return {key: round(value / total, 6) for key, value in normalized.items()}

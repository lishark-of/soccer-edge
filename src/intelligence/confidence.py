from __future__ import annotations


def confidence_score(signals: dict) -> dict:
    missing = [key for key, value in signals.items() if isinstance(value, dict) and value.get("status") == "not_connected"]
    score = max(0.35, 0.75 - 0.06 * len(missing))
    return {"confidence_score": round(score, 4), "missing_signals": missing}

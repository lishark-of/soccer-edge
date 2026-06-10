from __future__ import annotations

from datetime import datetime


def schedule_signal(match) -> dict:
    kickoff = _value(match, "kickoff_at", "")
    try:
        parsed = datetime.fromisoformat(str(kickoff).replace("Z", "+00:00"))
        kickoff_hour = parsed.hour
    except Exception:
        kickoff_hour = None
    return {
        "rest_days": "unknown",
        "travel_flag": "unknown",
        "kickoff_hour": kickoff_hour,
        "status": "basic_only",
        "impact": "unknown",
    }


def _value(obj, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

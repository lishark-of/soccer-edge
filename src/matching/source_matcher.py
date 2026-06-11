from __future__ import annotations

from difflib import SequenceMatcher

from src.matching.team_aliases import canonical_team_name


def match_source_event(match: dict, events: list[dict], *, date: str | None = None, threshold: float = 0.68) -> dict:
    best_event = None
    best_score = 0.0
    for event in events or []:
        score = _event_score(match, event, date)
        if score > best_score:
            best_score = score
            best_event = event
    status = "matched" if best_event and best_score >= threshold else "unmatched"
    return {
        "status": status,
        "score": round(best_score, 4),
        "event": best_event if status == "matched" else None,
        "reason_zh": "球队名和日期接近，已匹配。" if status == "matched" else "未找到足够接近的同场比赛，避免强行合并。",
    }


def _event_score(match: dict, event: dict, date: str | None) -> float:
    home = canonical_team_name(_value(match, "home_team"))
    away = canonical_team_name(_value(match, "away_team"))
    event_home = canonical_team_name(event.get("home_team"))
    event_away = canonical_team_name(event.get("away_team"))
    same_order = (_sim(home, event_home) + _sim(away, event_away)) / 2.0
    swapped = (_sim(home, event_away) + _sim(away, event_home)) / 2.0
    team_score = max(same_order, swapped)
    date_score = 0.0
    event_date = str(event.get("date") or event.get("kickoff_at") or "")[:10]
    match_date = str(_value(match, "date") or date or "")[:10]
    if event_date and match_date:
        date_score = 1.0 if event_date == match_date else 0.35
    return team_score * 0.82 + date_score * 0.18


def _sim(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    if left in right or right in left:
        return 0.88
    return SequenceMatcher(None, left, right).ratio()


def _value(obj, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

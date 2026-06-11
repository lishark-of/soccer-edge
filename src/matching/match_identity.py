from __future__ import annotations

from src.matching.source_matcher import match_source_event


def build_match_identity(match, api_football_events: list[dict] | None = None, odds_events: list[dict] | None = None, date: str | None = None) -> dict:
    match_info = _match_dict(match)
    api_match = match_source_event(match_info, api_football_events or [], date=date)
    odds_match = match_source_event(match_info, odds_events or [], date=date, threshold=0.62)
    matched = {
        "sporttery": "matched" if match_info.get("source") or match_info.get("match_id") else "unknown",
        "api_football": api_match["status"],
        "the_odds_api": odds_match["status"],
        "weather": "missing",
    }
    scores = [api_match.get("score", 0.0), odds_match.get("score", 0.0)]
    confidence = 0.55 + (0.25 if api_match["status"] == "matched" else 0) + (0.15 if odds_match["status"] == "matched" else 0)
    unresolved = [key for key, value in matched.items() if value in {"missing", "unmatched", "unknown"}]
    return {
        "sporttery_match_id": match_info.get("match_id"),
        "match_no": match_info.get("match_no"),
        "home_team": match_info.get("home_team"),
        "away_team": match_info.get("away_team"),
        "matched_sources": matched,
        "match_confidence": round(min(0.98, confidence), 4),
        "source_match_scores": {"api_football": api_match.get("score", 0), "the_odds_api": odds_match.get("score", 0)},
        "unresolved_fields": unresolved,
        "api_football_event": api_match.get("event"),
        "the_odds_event": odds_match.get("event"),
        "message_zh": _message(matched, scores),
    }


def _message(matched: dict, scores: list[float]) -> str:
    if matched.get("api_football") == "matched" and matched.get("the_odds_api") == "matched":
        return "Sporttery、API-Football 和海外赔率事件均能较好匹配。"
    if matched.get("api_football") == "matched":
        return "已匹配 API-Football 赛程；海外赔率暂未匹配到同场。"
    if matched.get("the_odds_api") == "matched":
        return "已匹配海外赔率事件；API-Football 赛程暂未匹配到同场。"
    return "未能跨源匹配到同场比赛，当前仅按 Sporttery 主数据分析。"


def _match_dict(match) -> dict:
    if isinstance(match, dict):
        return dict(match)
    return {
        "match_id": getattr(match, "match_id", ""),
        "match_no": getattr(match, "match_no", ""),
        "date": getattr(match, "date", ""),
        "league": getattr(match, "league", ""),
        "kickoff_at": getattr(match, "kickoff_at", ""),
        "home_team": getattr(match, "home_team", ""),
        "away_team": getattr(match, "away_team", ""),
        "source": getattr(match, "source", ""),
    }

from __future__ import annotations

from src.backtesting.historical_loader import HistoricalMatch
from src.modeling.features import historical_matches_before_date


DEFAULT_HOME_XG = 1.35
DEFAULT_AWAY_XG = 1.10
MIN_XG = 0.2
MAX_XG = 4.0


def build_team_strengths(historical_matches: list[HistoricalMatch], before_date: str) -> dict:
    filtered = historical_matches_before_date(historical_matches, before_date)
    teams: dict[str, dict[str, float | int]] = {}
    total_home_goals = 0
    total_away_goals = 0

    for match in filtered:
        home_stats = teams.setdefault(match.home_team, _empty_team_stats())
        away_stats = teams.setdefault(match.away_team, _empty_team_stats())

        home_stats["matches"] += 1
        home_stats["goals_for"] += match.home_goals
        home_stats["goals_against"] += match.away_goals
        home_stats["home_matches"] += 1
        home_stats["home_goals_for"] += match.home_goals
        home_stats["home_goals_against"] += match.away_goals

        away_stats["matches"] += 1
        away_stats["goals_for"] += match.away_goals
        away_stats["goals_against"] += match.home_goals
        away_stats["away_matches"] += 1
        away_stats["away_goals_for"] += match.away_goals
        away_stats["away_goals_against"] += match.home_goals

        total_home_goals += match.home_goals
        total_away_goals += match.away_goals

    sample_size = len(filtered)
    league_average_home_goals = round(total_home_goals / sample_size, 4) if sample_size else DEFAULT_HOME_XG
    league_average_away_goals = round(total_away_goals / sample_size, 4) if sample_size else DEFAULT_AWAY_XG

    return {
        "before_date": before_date,
        "sample_size": sample_size,
        "league_average_home_goals": league_average_home_goals,
        "league_average_away_goals": league_average_away_goals,
        "teams": teams,
    }


def estimate_xg_for_match(match, team_strengths: dict) -> tuple[float, float]:
    if not team_strengths or int(team_strengths.get("sample_size", 0)) <= 0:
        return DEFAULT_HOME_XG, DEFAULT_AWAY_XG

    teams = team_strengths.get("teams", {})
    home_stats = teams.get(match.home_team)
    away_stats = teams.get(match.away_team)
    if not isinstance(home_stats, dict) or not isinstance(away_stats, dict):
        return DEFAULT_HOME_XG, DEFAULT_AWAY_XG

    league_home = float(team_strengths.get("league_average_home_goals", DEFAULT_HOME_XG)) or DEFAULT_HOME_XG
    league_away = float(team_strengths.get("league_average_away_goals", DEFAULT_AWAY_XG)) or DEFAULT_AWAY_XG

    if int(home_stats.get("home_matches", 0)) <= 0 or int(away_stats.get("away_matches", 0)) <= 0:
        return DEFAULT_HOME_XG, DEFAULT_AWAY_XG

    home_attack = _blend_factor(
        _safe_ratio(float(home_stats["home_goals_for"]) / float(home_stats["home_matches"]), league_home),
        int(home_stats["home_matches"]),
    )
    away_defense = _blend_factor(
        _safe_ratio(float(away_stats["away_goals_against"]) / float(away_stats["away_matches"]), league_home),
        int(away_stats["away_matches"]),
    )
    away_attack = _blend_factor(
        _safe_ratio(float(away_stats["away_goals_for"]) / float(away_stats["away_matches"]), league_away),
        int(away_stats["away_matches"]),
    )
    home_defense = _blend_factor(
        _safe_ratio(float(home_stats["home_goals_against"]) / float(home_stats["home_matches"]), league_away),
        int(home_stats["home_matches"]),
    )

    home_xg = _clamp_xg(league_home * home_attack * away_defense)
    away_xg = _clamp_xg(league_away * away_attack * home_defense)
    return round(home_xg, 4), round(away_xg, 4)


def _empty_team_stats() -> dict[str, float | int]:
    return {
        "matches": 0,
        "goals_for": 0,
        "goals_against": 0,
        "home_matches": 0,
        "away_matches": 0,
        "home_goals_for": 0,
        "home_goals_against": 0,
        "away_goals_for": 0,
        "away_goals_against": 0,
    }


def _safe_ratio(value: float, baseline: float) -> float:
    if baseline <= 0:
        return 1.0
    return max(0.5, min(1.8, value / baseline))


def _blend_factor(raw_factor: float, sample_size: int) -> float:
    confidence = min(1.0, max(0.0, sample_size / 5.0))
    return 1.0 + (raw_factor - 1.0) * confidence


def _clamp_xg(value: float) -> float:
    return max(MIN_XG, min(MAX_XG, value))

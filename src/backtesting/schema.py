from __future__ import annotations

from src.backtesting.historical_loader import HistoricalMatch


def validate_historical_match(match) -> list[str]:
    issues: list[str] = []
    date = getattr(match, "date", "")
    if not isinstance(date, str) or not _is_iso_date(date):
        issues.append("date must be a valid YYYY-MM-DD string")
    if not getattr(match, "league", ""):
        issues.append("league is required")
    home_team = getattr(match, "home_team", "")
    away_team = getattr(match, "away_team", "")
    if not home_team:
        issues.append("home_team is required")
    if not away_team:
        issues.append("away_team is required")
    if home_team and away_team and home_team == away_team:
        issues.append("home_team and away_team must differ")
    home_goals = getattr(match, "home_goals", None)
    away_goals = getattr(match, "away_goals", None)
    if not isinstance(home_goals, int) or home_goals < 0:
        issues.append("home_goals must be a non-negative integer")
    if not isinstance(away_goals, int) or away_goals < 0:
        issues.append("away_goals must be a non-negative integer")
    if getattr(match, "result_1x2", None) not in {"H", "D", "A"}:
        issues.append("result_1x2 must be H, D, or A")
    odds = getattr(match, "odds_had", None)
    if odds:
        for key in ("win", "draw", "lose"):
            value = odds.get(key)
            if not isinstance(value, (int, float)) or value <= 1:
                issues.append(f"odds_had.{key} must be greater than 1")
    return issues


def is_valid_historical_match(match) -> bool:
    return not validate_historical_match(match)


def validate_historical_dataset(matches: list[HistoricalMatch]) -> dict:
    invalid = [match for match in matches if validate_historical_match(match)]
    warnings: list[str] = []
    if any(not getattr(match, "odds_had", None) for match in matches):
        warnings.append("some matches are missing HAD odds")
    dates = sorted(match.date for match in matches if _is_iso_date(getattr(match, "date", "")))
    teams = {
        team
        for match in matches
        for team in (getattr(match, "home_team", ""), getattr(match, "away_team", ""))
        if team
    }
    leagues = {getattr(match, "league", "") for match in matches if getattr(match, "league", "")}
    return {
        "matches": len(matches),
        "valid_matches": len(matches) - len(invalid),
        "invalid_matches": len(invalid),
        "warnings": warnings,
        "date_min": dates[0] if dates else None,
        "date_max": dates[-1] if dates else None,
        "leagues": len(leagues),
        "teams": len(teams),
    }


def _is_iso_date(value: str) -> bool:
    parts = value.split("-")
    return len(parts) == 3 and all(part.isdigit() for part in parts) and len(parts[0]) == 4

from __future__ import annotations

from csv import DictReader
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json


@dataclass(frozen=True, slots=True)
class HistoricalMatch:
    date: str
    league: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    result_1x2: str
    half_time_score: Optional[str] = None
    odds_had: Optional[dict] = None
    odds_hhad: Optional[dict] = None
    raw: Optional[dict] = None


def load_historical_matches(path: str) -> list[HistoricalMatch]:
    file_path = Path(path)
    if file_path.suffix.lower() not in {".csv", ".jsonl"}:
        raise ValueError(f"unsupported historical data format: {file_path.suffix or 'unknown'}")
    matches, _ = load_historical_matches_with_warnings(path)
    return matches


def load_historical_matches_with_warnings(path: str) -> tuple[list[HistoricalMatch], list[str]]:
    warnings: list[str] = []
    matches: list[HistoricalMatch] = []
    file_path = Path(path)
    if not file_path.exists():
        return [], [f"historical data missing: {path}"]
    if file_path.suffix.lower() not in {".csv", ".jsonl"}:
        return [], [f"unsupported historical data format: {file_path.suffix or 'unknown'}"]
    try:
        if file_path.suffix.lower() == ".jsonl":
            with file_path.open("r", encoding="utf-8") as handle:
                for index, line in enumerate(handle, start=1):
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        row = json.loads(text)
                        if not isinstance(row, dict):
                            raise ValueError("jsonl row is not an object")
                        matches.append(normalize_historical_row(row))
                    except (json.JSONDecodeError, ValueError) as exc:
                        warnings.append(f"skip row {index}: {exc}")
        else:
            with file_path.open("r", encoding="utf-8", newline="") as handle:
                reader = DictReader(handle)
                for index, row in enumerate(reader, start=2):
                    try:
                        matches.append(normalize_historical_row(row))
                    except ValueError as exc:
                        warnings.append(f"skip row {index}: {exc}")
    except OSError as exc:
        return [], [f"historical data unreadable: {exc}"]
    return matches, warnings


def normalize_historical_row(row: dict) -> HistoricalMatch:
    date_value = _normalize_date(_first_value(row, "date", "match_date", "matchDate", "matchDay"))
    league = _clean_text(_first_value(row, "league", "competition", "league_name", "leagueName", "tournament") or "Unknown")
    home_team = _clean_text(_first_value(row, "home_team", "home", "homeTeam", "home_name", "homeName"))
    away_team = _clean_text(_first_value(row, "away_team", "away", "awayTeam", "away_name", "awayName"))
    if not home_team or not away_team:
        raise ValueError("missing team names")

    score_text = _clean_text(_first_value(row, "score", "full_time_score", "ft_score", "result_score", "full_time_result"))
    home_goals = _parse_optional_int(_first_value(row, "home_goals", "home_score", "homeGoals", "homeScore"))
    away_goals = _parse_optional_int(_first_value(row, "away_goals", "away_score", "awayGoals", "awayScore"))
    if home_goals is None or away_goals is None:
        parsed_score = _parse_score(score_text)
        if parsed_score is None:
            raise ValueError("missing score information")
        home_goals, away_goals = parsed_score
    if home_goals < 0 or away_goals < 0:
        raise ValueError("goals cannot be negative")

    if home_goals > away_goals:
        result_1x2 = "H"
    elif home_goals < away_goals:
        result_1x2 = "A"
    else:
        result_1x2 = "D"

    return HistoricalMatch(
        date=date_value,
        league=league,
        home_team=home_team,
        away_team=away_team,
        home_goals=home_goals,
        away_goals=away_goals,
        result_1x2=result_1x2,
        half_time_score=_clean_text(_first_value(row, "half_time_score", "halfTimeScore")) or None,
        odds_had=_parse_had_odds(row),
        odds_hhad=_parse_market_blob(_first_value(row, "odds_hhad", "hhad_odds")),
        raw=dict(row),
    )


def _normalize_date(value: object) -> str:
    text = _clean_text(value)
    if not text:
        raise ValueError("missing date")
    text = text.split("T", 1)[0].strip()
    for separator in ("/", "."):
        text = text.replace(separator, "-")
    parts = text.split("-")
    if len(parts) != 3:
        raise ValueError(f"unsupported date format: {text}")
    year, month, day = parts
    if not (year.isdigit() and month.isdigit() and day.isdigit()):
        raise ValueError(f"unsupported date format: {text}")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _parse_score(score_text: str) -> tuple[int, int] | None:
    if not score_text:
        return None
    normalized = score_text.replace("：", ":").replace("-", ":").replace(" 比 ", ":").replace("比", ":")
    if ":" not in normalized:
        return None
    left, right = normalized.split(":", 1)
    if not left.strip().isdigit() or not right.strip().isdigit():
        return None
    return int(left.strip()), int(right.strip())


def _parse_optional_int(value: object) -> int | None:
    text = _clean_text(value)
    if not text:
        return None
    if not text.lstrip("-").isdigit():
        return None
    return int(text)


def _parse_market_blob(value: object) -> Optional[dict]:
    text = _clean_text(value)
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_had_odds(row: dict) -> Optional[dict]:
    blob = _parse_market_blob(_first_value(row, "odds_had", "had_odds"))
    if blob:
        return blob
    home = _parse_optional_float(_first_value(row, "odds_home", "home_odds", "h"))
    draw = _parse_optional_float(_first_value(row, "odds_draw", "draw_odds", "d"))
    away = _parse_optional_float(_first_value(row, "odds_away", "away_odds", "a"))
    if home is None and draw is None and away is None:
        return None
    return {"win": home, "draw": draw, "lose": away}


def _parse_optional_float(value: object) -> float | None:
    text = _clean_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _first_value(row: dict, *keys: str) -> object:
    for key in keys:
        if key in row and _clean_text(row.get(key)):
            return row.get(key)
    return None


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()

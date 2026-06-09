from __future__ import annotations

import json
from pathlib import Path


DEFAULT_FIELD_ALIASES = {
    "date": ["date", "match_date", "matchDate", "match_time", "日期", "比赛日期", "开赛日期"],
    "league": ["league", "competition", "league_name", "leagueName", "game", "赛事", "联赛"],
    "home_team": ["home_team", "home", "homeTeam", "home_name", "主队", "主队名称"],
    "away_team": ["away_team", "away", "awayTeam", "away_name", "客队", "客队名称"],
    "score": ["score", "full_time_score", "ft_score", "result_score", "比分", "全场比分"],
    "half_time_score": ["half_time_score", "half_score", "半场比分"],
    "odds_home": ["odds_home", "home_odds", "h", "胜赔", "主胜", "胜"],
    "odds_draw": ["odds_draw", "draw_odds", "d", "平赔", "平"],
    "odds_away": ["odds_away", "away_odds", "a", "负赔", "客胜", "负"],
    "handicap": ["handicap", "让球"],
    "hhad_win": ["hhad_win", "让胜"],
    "hhad_draw": ["hhad_draw", "让平"],
    "hhad_lose": ["hhad_lose", "让负"],
}


def infer_field_mapping(columns: list[str]) -> dict:
    normalized = {_norm(column): column for column in columns}
    mapping = {}
    for canonical, aliases in DEFAULT_FIELD_ALIASES.items():
        matches = list(dict.fromkeys(normalized[_norm(alias)] for alias in aliases if _norm(alias) in normalized))
        if len(matches) == 1:
            mapping[canonical] = matches[0]
    return mapping


def apply_field_mapping(row: dict, mapping: dict) -> dict:
    output = {}
    for canonical, source in mapping.items():
        output[canonical] = row.get(source)
    return output


def load_field_mapping(path: str) -> dict:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"field mapping unreadable: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("field mapping must be a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def normalize_row_with_mapping(row: dict, mapping: dict) -> dict:
    mapped = apply_field_mapping(row, mapping)
    return {key: value for key, value in mapped.items() if value not in (None, "")}


def _norm(value: str) -> str:
    return str(value).strip().lower().replace(" ", "").replace("_", "")

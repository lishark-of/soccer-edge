from __future__ import annotations

REQUIRED_FIELDS = ["date", "league", "home_team", "away_team"]
SCORE_ALTERNATIVES = ["score", "home_goals", "away_goals"]
ODDS_FIELDS = ["odds_home", "odds_draw", "odds_away"]
OPTIONAL_FIELDS = ["half_time_score", "handicap", "hhad_win", "hhad_draw", "hhad_lose"]

LABELS_ZH = {
    "date": "比赛日期",
    "league": "赛事/联赛",
    "home_team": "主队",
    "away_team": "客队",
    "score": "比分",
    "home_goals": "主队进球",
    "away_goals": "客队进球",
    "odds_home": "胜赔",
    "odds_draw": "平赔",
    "odds_away": "负赔",
}


def build_field_recognition_report(
    columns: list[str],
    inferred_mapping: dict,
    required_fields: list[str] | None = None,
) -> dict:
    required = list(required_fields or REQUIRED_FIELDS)
    recognized = []
    for canonical, source in sorted((inferred_mapping or {}).items()):
        recognized.append({"canonical": canonical, "label_zh": LABELS_ZH.get(canonical, canonical), "source": source, "status": "recognized"})
    missing_required = [field for field in required if field not in inferred_mapping]
    has_score = "score" in inferred_mapping or {"home_goals", "away_goals"}.issubset(set(inferred_mapping))
    if not has_score:
        missing_required.append("score")
    missing_required = list(dict.fromkeys(missing_required))
    missing_odds = [field for field in ODDS_FIELDS if field not in inferred_mapping]
    optional = [field for field in OPTIONAL_FIELDS if field in inferred_mapping]
    warnings = []
    if missing_odds:
        warnings.append("缺少胜平负赔率字段时，可以导入赛果，但无法进行基于赔率的 EV 回测。")
    if missing_required:
        warnings.append("存在必需字段未识别，请按修复建议补充 CSV 列或 mapping JSON。")
    confidence = _confidence(missing_required, missing_odds, len(recognized))
    return {
        "columns": list(columns or []),
        "recognized_fields": recognized,
        "missing_required_fields": missing_required,
        "missing_odds_fields": missing_odds,
        "optional_fields": optional,
        "confidence": confidence,
        "can_normalize": not missing_required,
        "can_backtest_with_ev": not missing_required and not missing_odds,
        "warnings": warnings,
    }


def _confidence(missing_required: list[str], missing_odds: list[str], recognized_count: int) -> str:
    if missing_required:
        return "low"
    if missing_odds or recognized_count < 7:
        return "medium"
    return "high"

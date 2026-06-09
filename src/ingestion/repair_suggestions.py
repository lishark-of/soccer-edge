from __future__ import annotations

FIELD_MESSAGES = {
    "date": ("未识别比赛日期字段。", "请在 CSV 中增加 `比赛日期` 或 `date` 列，或在 mapping JSON 中配置 `date` 对应的列名。", {"date": "比赛日期"}),
    "league": ("未识别赛事字段。", "请在 CSV 中增加 `赛事` / `联赛` 列，或在 mapping JSON 中配置 `league` 对应的列名。", {"league": "赛事"}),
    "home_team": ("未识别主队字段。", "请在 CSV 中增加 `主队` 列，或在 mapping JSON 中配置 `home_team` 对应的列名。", {"home_team": "主队"}),
    "away_team": ("未识别客队字段。", "请在 CSV 中增加 `客队` 列，或在 mapping JSON 中配置 `away_team` 对应的列名。", {"away_team": "客队"}),
    "score": ("未识别比分字段。", "请在 CSV 中增加 `比分` 列，例如 `2-1`，或同时提供 `home_goals` 与 `away_goals` 映射。", {"score": "比分"}),
    "odds_home": ("未识别胜赔字段。", "如需 EV 回测，请增加 `胜赔` 列，或在 mapping JSON 中配置 `odds_home`。", {"odds_home": "胜赔"}),
    "odds_draw": ("未识别平赔字段。", "如需 EV 回测，请增加 `平赔` 列，或在 mapping JSON 中配置 `odds_draw`。", {"odds_draw": "平赔"}),
    "odds_away": ("未识别负赔字段。", "如需 EV 回测，请增加 `负赔` 列，或在 mapping JSON 中配置 `odds_away`。", {"odds_away": "负赔"}),
}


def build_repair_suggestions(field_report: dict) -> list[dict]:
    suggestions = []
    for field in field_report.get("missing_required_fields", []) or []:
        suggestions.append(_suggestion("error", field))
    for field in field_report.get("missing_odds_fields", []) or []:
        suggestions.append(_suggestion("warning", field))
    if not suggestions:
        suggestions.append(
            {
                "severity": "info",
                "field": "all",
                "message_zh": "字段识别结果良好。",
                "suggestion_zh": "可以继续生成标准化 CSV，并基于该数据运行概率回测。",
                "mapping_example": {},
            }
        )
    return suggestions


def _suggestion(severity: str, field: str) -> dict:
    message, suggestion, example = FIELD_MESSAGES.get(
        field,
        (f"未识别 `{field}` 字段。", f"请在 mapping JSON 中配置 `{field}` 对应的列名。", {field: "你的列名"}),
    )
    return {
        "severity": severity,
        "field": field,
        "message_zh": message,
        "suggestion_zh": suggestion,
        "mapping_example": example,
    }

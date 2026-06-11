from __future__ import annotations

from src.intelligence.coverage_status import is_confirmed, is_missing, is_partial, normalize_coverage_status, status_zh

SUPPORTED_EXTERNAL_FIELDS = [
    "injuries",
    "lineup",
    "match_city",
    "weather",
    "news",
    "travel",
    "motivation",
    "neutral_ground",
    "tournament_importance",
]

FIELD_LABELS = {
    "injuries": "伤停",
    "lineup": "首发",
    "match_city": "比赛城市",
    "weather": "天气",
    "news": "新闻面",
    "travel": "旅行",
    "motivation": "战意",
    "neutral_ground": "中立场",
    "tournament_importance": "赛事重要性",
}

FIELD_SUPPLY_HINTS = {
    "injuries": "可在 data/external_signals/*.json 中补充 injuries 数组，写明球员、球队、状态和来源。",
    "lineup": "可补充 lineup.home / lineup.away，临近开赛后再更新更可靠。",
    "match_city": "可补充 match_city 或 venue_city，天气会优先使用明确比赛城市。",
    "weather": "可补充 weather，或完善球场/城市坐标后由 Open-Meteo 读取。",
    "news": "可补充 news 数组，保留标题、来源、链接和摘要；系统不会自动编造新闻。",
    "travel": "可补充 travel，包括长途旅行、跨时区、连续客场等事实。",
    "motivation": "可补充 motivation，但必须写明来源，避免主观臆测。",
    "neutral_ground": "可补充 neutral_ground=true/false，并注明比赛地点。",
    "tournament_importance": "可补充 tournament_importance，例如淘汰赛、友谊赛、争冠/保级背景。",
}


def build_missing_info_status(context: dict | None = None, coverage: dict | None = None) -> dict:
    context = context or {}
    coverage = coverage or context.get("source_coverage") or {}
    signals = context.get("signals") or {}
    rows = []
    for key in SUPPORTED_EXTERNAL_FIELDS:
        signal = coverage.get(key) or signals.get(key) or {}
        status = normalize_coverage_status(signal.get("status"))
        rows.append(
            {
                "key": key,
                "label_zh": FIELD_LABELS[key],
                "status": status,
                "status_zh": status_zh(status),
                "impact": signal.get("impact", "unknown"),
                "impact_zh": "未知" if signal.get("impact", "unknown") == "unknown" else str(signal.get("impact")),
                "user_can_supply": not is_confirmed(status),
                "supply_hint_zh": FIELD_SUPPLY_HINTS[key],
                "message_zh": signal.get("message_zh") or _message(key, status),
            }
        )
    missing = [row for row in rows if is_missing(row["status"])]
    partial = [row for row in rows if is_partial(row["status"])]
    return {
        "fields": rows,
        "missing_information": [row["label_zh"] for row in missing],
        "partial_information": [row["label_zh"] for row in partial],
        "summary_zh": _summary(missing, partial),
        "external_signals_dir": "data/external_signals/",
        "gitignore_required": True,
        "disclaimer": "缺失情报只会降低信心，系统不会编造伤停、首发、天气或新闻。",
    }


def build_missing_info_from_preview(preview: dict) -> dict:
    contexts = preview.get("contexts") or []
    by_label: dict[str, dict] = {}
    for context in contexts:
        status = build_missing_info_status(context)
        for row in status["fields"]:
            current = by_label.get(row["label_zh"])
            if current is None or _status_rank(row["status"]) < _status_rank(current["status"]):
                by_label[row["label_zh"]] = row
    rows = list(by_label.values())
    missing = [row for row in rows if is_missing(row["status"])]
    partial = [row for row in rows if is_partial(row["status"])]
    return {
        "fields": rows,
        "missing_information": [row["label_zh"] for row in missing],
        "partial_information": [row["label_zh"] for row in partial],
        "summary_zh": _summary(missing, partial),
        "external_signals_dir": "data/external_signals/",
        "disclaimer": "如果没有可靠外部 JSON，相关字段保持 unknown/not_connected。",
    }


def _status_rank(status: str) -> int:
    return {"not_connected": 0, "error": 0, "unknown": 1, "checked_empty": 3, "fallback_estimated": 4, "user_supplied": 8, "confirmed": 9}.get(status, 1)


def _message(key: str, status: str) -> str:
    if status in {"confirmed", "user_supplied"}:
        return f"{FIELD_LABELS[key]}已有可用来源。"
    if status in {"checked_empty", "fallback_estimated"}:
        return f"{FIELD_LABELS[key]}已尝试读取或只有部分覆盖，会降低观察可信度。"
    return f"{FIELD_LABELS[key]}未接入，当前影响保持 unknown。"


def _summary(missing: list[dict], partial: list[dict]) -> str:
    parts = []
    if missing:
        parts.append("主要缺失：" + "、".join(row["label_zh"] for row in missing[:6]))
    if partial:
        parts.append("部分覆盖：" + "、".join(row["label_zh"] for row in partial[:6]))
    return "；".join(parts) if parts else "关键外部情报已有覆盖记录。"

from __future__ import annotations


FACTOR_LABELS = {
    "market_value": "赔率价值",
    "model_probability": "模型概率",
    "combo_risk": "组合风险",
    "injury_lineup": "伤停/首发",
    "weather": "天气",
    "schedule_travel": "赛程/旅行",
    "motivation_news": "战意/新闻",
    "score_tempo": "比分/节奏",
    "unknown": "未知因子",
}


def classify_ai_factor(text: str | dict | None, category: str | None = None) -> dict:
    if isinstance(text, dict):
        parts = []
        for key in (
            "target",
            "hypothesis_zh",
            "note_zh",
            "usage_zh",
            "reason_zh",
            "validation_rule_zh",
            "play_type",
            "outcome_key",
            "outcome_label",
            "direction",
            "market_prob",
            "model_prob",
            "odds",
            "ev",
            "edge",
        ):
            if key in text and text.get(key) not in (None, ""):
                parts.append(f"{key} {text.get(key)}")
        raw = " ".join(parts)
    else:
        raw = str(text or "")
    haystack = raw.lower()
    category = str(category or "").lower()
    if category in {"daily_2x1_candidate", "daily_3x1_candidate", "rejected_combo_review"} or _contains(haystack, "组合", "串", "parlay", "相关性", "回撤"):
        key = "combo_risk"
    elif _contains(haystack, "伤停", "首发", "阵容", "injury", "lineup"):
        key = "injury_lineup"
    elif _contains(haystack, "天气", "降雨", "风", "weather", "rain", "wind"):
        key = "weather"
    elif _contains(haystack, "赛程", "休息", "旅行", "travel", "rest", "密度"):
        key = "schedule_travel"
    elif _contains(haystack, "战意", "新闻", "motivation", "news", "舆情"):
        key = "motivation_news"
    elif category in {"score", "total_goals"} or _contains(haystack, "比分", "总进球", "节奏", "score", "goals", "tempo"):
        key = "score_tempo"
    elif _contains(haystack, "赔率", "市场", "clv", "edge", "ev", "低估", "高估", "value", "odds"):
        key = "market_value"
    elif _contains(haystack, "概率", "模型", "poisson", "elo", "xg", "dixon"):
        key = "model_probability"
    else:
        key = "unknown"
    return {
        "ai_factor": key,
        "ai_factor_zh": FACTOR_LABELS.get(key, key),
        "ai_factor_reason_zh": _reason(key),
    }


def _contains(text: str, *needles: str) -> bool:
    return any(needle.lower() in text for needle in needles)


def _reason(key: str) -> str:
    return {
        "market_value": "该假设主要讨论赔率、EV、Edge 或市场是否低估。",
        "model_probability": "该假设主要讨论模型概率、xG、Poisson、Elo 或比分模型。",
        "combo_risk": "该假设主要讨论串联、相关性、回撤或组合纪律。",
        "injury_lineup": "该假设主要依赖伤停、首发或阵容信息。",
        "weather": "该假设主要依赖天气影响。",
        "schedule_travel": "该假设主要依赖赛程、休息或旅行影响。",
        "motivation_news": "该假设主要依赖战意、新闻或舆情。",
        "score_tempo": "该假设主要讨论比分、节奏或总进球。",
        "unknown": "暂不能识别主要因子，赛后只做整体复盘。",
    }.get(key, "暂不能识别主要因子。")

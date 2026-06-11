from __future__ import annotations

WEIGHTS = {
    "sporttery_odds": 25,
    "overseas_odds": 15,
    "schedule_time": 10,
    "team_info": 10,
    "injuries": 15,
    "lineup": 10,
    "weather": 5,
    "history_recent": 5,
    "motivation_news": 5,
}

LABELS = {
    "sporttery_odds": "Sporttery 官方赔率",
    "overseas_odds": "海外赔率参考",
    "schedule_time": "赛程/时间",
    "team_info": "球队基础信息",
    "injuries": "伤停",
    "lineup": "首发",
    "weather": "天气",
    "history_recent": "近期/历史补充",
    "motivation_news": "战意/新闻",
}


def build_intelligence_completeness(context: dict, coverage: dict | None = None) -> dict:
    coverage = coverage or {}
    signals = context.get("signals", {}) or {}
    sporttery_odds = context.get("sporttery_odds", {}) or {}
    components = []
    score = 0

    def add(key: str, status: str, gained: int, message: str):
        nonlocal score
        max_score = WEIGHTS[key]
        gained = max(0, min(max_score, int(round(gained))))
        score += gained
        components.append({"key": key, "label": LABELS[key], "status": status, "score": gained, "max_score": max_score, "message_zh": message})

    has_odds = bool((sporttery_odds.get("had") or {}) or (sporttery_odds.get("hhad") or {}))
    add("sporttery_odds", "connected" if has_odds else "missing", 25 if has_odds else 0, "官方胜平负/让球赔率可用。" if has_odds else "缺少竞彩官方赔率。")
    odds_cov = coverage.get("the_odds_api", {})
    add("overseas_odds", odds_cov.get("status", "unknown"), odds_cov.get("score", 0), odds_cov.get("label_zh", "海外赔率未匹配。"))
    match = context.get("match", {}) or {}
    has_time = bool(match.get("kickoff_at") or match.get("date"))
    add("schedule_time", "basic_only" if has_time else "missing", 10 if has_time else 0, "已有开赛日期/时间。" if has_time else "缺少开赛时间。")
    api_cov = coverage.get("api_football", {})
    add("team_info", api_cov.get("status", "unknown"), min(10, api_cov.get("score", 0) // 2), api_cov.get("label_zh", "球队信息未匹配。"))
    injuries = coverage.get("injuries") or signals.get("injuries", {})
    add("injuries", injuries.get("status", "not_connected"), _signal_score(injuries, full=15, partial=6), _signal_message(injuries, "伤停"))
    lineup = coverage.get("lineup") or signals.get("lineup", {})
    add("lineup", lineup.get("status", "not_connected"), _signal_score(lineup, full=10, partial=2), _signal_message(lineup, "首发"))
    weather = coverage.get("weather") or signals.get("weather", {})
    add("weather", weather.get("status", "not_connected"), _signal_score(weather, full=5, partial=0), _signal_message(weather, "天气"))
    add("history_recent", api_cov.get("status", "unknown"), 3 if api_cov.get("status") == "matched" else 0, "API-Football 匹配后可作为近期数据补充。" if api_cov.get("status") == "matched" else "近期/历史补充不足。")
    motivation = signals.get("motivation", {})
    news = coverage.get("news") or signals.get("news", {})
    motivated = motivation.get("status") == "connected" or news.get("status") == "connected"
    news_score = 5 if motivated else 1 if news.get("status") == "not_found" else 0
    add("motivation_news", "connected" if motivated else news.get("status", "not_connected"), news_score, _signal_message(news, "新闻/战意") if not motivated else "新闻/战意已接入。")

    return {
        "score": min(100, score),
        "label_zh": _label(score),
        "components": components,
        "missing_keys": [item["key"] for item in components if item["score"] <= 0],
        "main_gaps_zh": [item["label"] for item in components if item["score"] <= 0],
        "partial_gaps_zh": [item["label"] for item in components if 0 < item["score"] < item["max_score"]],
        "summary_zh": _summary(score, components),
    }


def build_overall_completeness(contexts: list[dict]) -> dict:
    scores = [float((ctx.get("intelligence_completeness") or {}).get("score", 0)) for ctx in contexts]
    avg = round(sum(scores) / len(scores), 1) if scores else 0
    gaps = []
    partial_gaps = []
    for ctx in contexts:
        for gap in (ctx.get("intelligence_completeness") or {}).get("main_gaps_zh", []):
            if gap not in gaps:
                gaps.append(gap)
        for gap in (ctx.get("intelligence_completeness") or {}).get("partial_gaps_zh", []):
            if gap not in partial_gaps:
                partial_gaps.append(gap)
    return {
        "score": avg,
        "label_zh": _label(avg),
        "main_gaps_zh": gaps[:8],
        "partial_gaps_zh": partial_gaps[:8],
        "summary_zh": f"平均情报完整度 {avg}/100，评级：{_label(avg)}。",
    }


def _label(score: float) -> str:
    if score >= 80:
        return "高"
    if score >= 60:
        return "中"
    if score >= 40:
        return "中低"
    return "低"


def _summary(score: float, components: list[dict]) -> str:
    gaps = [item["label"] for item in components if item["score"] <= 0]
    if not gaps:
        return f"情报完整度 {score}/100，核心数据较完整。"
    return f"情报完整度 {score}/100，主要缺口：{'、'.join(gaps[:5])}。"


def _signal_score(signal: dict, *, full: int, partial: int) -> int:
    status = signal.get("status")
    if status == "connected":
        return full
    if status in {"covered_empty", "not_found", "not_available", "basic_only"}:
        return partial
    return 0


def _signal_message(signal: dict, label: str) -> str:
    if signal.get("message_zh"):
        return signal["message_zh"]
    if signal.get("status") == "connected":
        return f"{label}已接入。"
    if signal.get("status") in {"covered_empty", "not_found", "not_available"}:
        return f"{label}已尝试读取，但未获得强覆盖。"
    return f"{label}未接入，不编造。"

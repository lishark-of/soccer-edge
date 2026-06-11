from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError

from src.matching.match_identity import build_match_identity
from src.providers.api_football_enrichment import get_fixture_enrichment
from src.providers.api_football_provider import get_api_football_fixtures
from src.providers.gdelt_news_provider import get_match_news
from src.providers.the_odds_provider import get_the_odds_soccer_odds
from src.providers.weather_provider import get_match_weather


def build_source_coverage(matches: list, target_date: str | None) -> dict:
    api_status = get_api_football_fixtures(target_date, timeout=5)
    odds_status = get_the_odds_soccer_odds(target_date, max_sports=1, timeout=5)
    api_events = api_status.get("fixtures", []) if api_status.get("status") == "ok" else []
    odds_events = odds_status.get("events", []) if odds_status.get("status") == "ok" else []
    match_rows = []
    by_match_id = {}
    with ThreadPoolExecutor(max_workers=max(1, min(4, len(matches) or 1))) as executor:
        futures = []
        for match in matches:
            identity = build_match_identity(match, api_events, odds_events, target_date)
            futures.append(executor.submit(_coverage_row, match, identity, api_status, odds_status))
        for future in futures:
            try:
                row = future.result(timeout=12)
            except TimeoutError:
                continue
            match_rows.append(row)
            if row.get("match_id"):
                by_match_id[str(row["match_id"])] = row
    cards = _source_cards(match_rows, api_status, odds_status)
    return {
        "coverage_version": "phase2q_enrichment_coverage_v0",
        "date": target_date,
        "source_cards": cards,
        "match_coverage": match_rows,
        "by_match_id": by_match_id,
        "api_football_status": _public_api_status(api_status),
        "the_odds_api_status": _public_odds_status(odds_status),
        "summary_zh": _summary(cards),
        "warnings": _warnings(api_status, odds_status, match_rows),
    }


def _coverage_row(match, identity: dict, api_status: dict, odds_status: dict) -> dict:
    match_id = _value(match, "match_id", "")
    api_matched = identity.get("matched_sources", {}).get("api_football") == "matched"
    odds_matched = identity.get("matched_sources", {}).get("the_odds_api") == "matched"
    api_event = identity.get("api_football_event") or {}
    fixture_id = api_event.get("fixture_id")
    with ThreadPoolExecutor(max_workers=3) as executor:
        enrichment_future = executor.submit(get_fixture_enrichment, fixture_id, timeout=4) if api_matched else None
        weather_future = executor.submit(get_match_weather, api_event.get("venue_city"), api_event.get("kickoff_at"), timeout=4) if api_matched else None
        news_future = executor.submit(get_match_news, _value(match, "home_team", ""), _value(match, "away_team", ""), timeout=4)
        enrichment = _future_value(enrichment_future, get_fixture_enrichment(None), timeout=6) if enrichment_future else get_fixture_enrichment(None)
        weather_signal = _future_value(weather_future, _unknown_signal("天气", "未匹配 API-Football 赛程，缺少球场城市。"), timeout=6) if weather_future else _unknown_signal("天气", "未匹配 API-Football 赛程，缺少球场城市。")
        news_signal = _future_value(news_future, _unknown_signal("新闻", "新闻读取超时或暂不可用。"), timeout=6)
    injuries = enrichment.get("injuries", _unknown_signal("伤停", "伤停未接入。"))
    lineup = enrichment.get("lineup", _unknown_signal("首发", "首发未接入。"))
    return {
        "match_id": str(match_id),
        "match_no": _value(match, "match_no", ""),
        "match": f"{_value(match, 'match_no', '')} {_value(match, 'home_team', '')} vs {_value(match, 'away_team', '')}".strip(),
        "home_team": _value(match, "home_team", ""),
        "away_team": _value(match, "away_team", ""),
        "sporttery": {"status": "matched", "label_zh": "竞彩主源已接入", "score": 25},
        "api_football": {
            "status": "matched" if api_matched else api_status.get("status", "unknown"),
            "label_zh": "已匹配赛程" if api_matched else "已接入但未匹配同场" if api_status.get("status") == "ok" else "未接入",
            "score": 20 if api_matched else 8 if api_status.get("status") == "ok" else 0,
            "event": api_event,
        },
        "the_odds_api": {
            "status": "matched" if odds_matched else odds_status.get("status", "unknown"),
            "label_zh": "已匹配海外赔率" if odds_matched else "已接入但未匹配同场" if odds_status.get("status") == "ok" else "未接入",
            "score": 15 if odds_matched else 6 if odds_status.get("status") == "ok" else 0,
            "event": identity.get("the_odds_event"),
        },
        "injuries": _signal_card(injuries),
        "lineup": _signal_card(lineup),
        "weather": _signal_card(weather_signal),
        "news": _signal_card(news_signal),
        "enrichment": {
            "fixture_id": fixture_id,
            "api_football": enrichment,
            "weather": weather_signal,
            "news": news_signal,
        },
        "identity": {k: v for k, v in identity.items() if k not in {"api_football_event", "the_odds_event"}},
        "message_zh": _match_message(identity, injuries, lineup, weather_signal, news_signal),
    }


def _source_cards(match_rows: list[dict], api_status: dict, odds_status: dict) -> list[dict]:
    total = len(match_rows)
    api_matched = _count(match_rows, "api_football", "matched")
    odds_matched = _count(match_rows, "the_odds_api", "matched")
    injuries_covered = _count_signal(match_rows, "injuries", {"connected", "covered_empty"})
    lineup_covered = _count_signal(match_rows, "lineup", {"connected"})
    weather_covered = _count_signal(match_rows, "weather", {"connected"})
    news_found = _count_signal(match_rows, "news", {"connected"})
    news_checked = _count_signal(match_rows, "news", {"connected", "not_found", "timeout"})
    news_timeout = _count_signal(match_rows, "news", {"timeout"})
    return [
        {
            "source": "Sporttery",
            "status": "available" if total else "empty",
            "label_zh": "竞彩主数据",
            "coverage": f"{total}/{total}" if total else "0/0",
            "score": 95 if total else 20,
            "message_zh": "可售比赛和官方赔率主数据源。" if total else "当前未读取到可售比赛。",
        },
        {
            "source": "API-Football",
            "status": api_status.get("status", "unknown"),
            "label_zh": "赛程/球队补充",
            "coverage": f"{api_matched}/{total}",
            "score": _coverage_score(api_matched, total, api_status),
            "message_zh": api_status.get("message_zh", ""),
        },
        {
            "source": "API-Football 伤停",
            "status": "ok" if injuries_covered else "not_available",
            "label_zh": "伤停补充",
            "coverage": f"{injuries_covered}/{total}",
            "score": _ratio_score(injuries_covered, total),
            "message_zh": "已尝试读取每场 fixture 的公开伤停；空结果不等于确认无人缺阵。",
        },
        {
            "source": "API-Football 首发",
            "status": "ok" if lineup_covered else "not_available",
            "label_zh": "首发补充",
            "coverage": f"{lineup_covered}/{total}",
            "score": _ratio_score(lineup_covered, total),
            "message_zh": "首发通常临近开赛才公布；未返回时显示未公布/未覆盖。",
        },
        {
            "source": "The Odds API",
            "status": odds_status.get("status", "unknown"),
            "label_zh": "海外赔率参考",
            "coverage": f"{odds_matched}/{total}",
            "score": _coverage_score(odds_matched, total, odds_status),
            "message_zh": odds_status.get("message_zh", ""),
        },
        {
            "source": "Open-Meteo",
            "status": "ok" if weather_covered else "not_connected",
            "label_zh": "天气补充",
            "coverage": f"{weather_covered}/{total}",
            "score": _ratio_score(weather_covered, total),
            "message_zh": "通过 API-Football 城市/球场信息读取小时级天气。" if weather_covered else "缺少城市坐标或天气接口未返回。",
        },
        {
            "source": "GDELT 新闻",
            "status": "ok" if news_found else "timeout" if news_timeout else "not_found",
            "label_zh": "新闻标题补充",
            "coverage": f"{news_checked}/{total}",
            "score": _ratio_score(news_found, total),
            "message_zh": "已尝试读取新闻标题/来源/链接；未返回时不编造新闻，也不改变概率。",
        },
    ]


def _signal_card(signal: dict) -> dict:
    return {
        "status": signal.get("status", "unknown"),
        "label_zh": signal.get("label_zh") or signal.get("message_zh") or "未知",
        "impact": signal.get("impact", "unknown"),
        "items_count": len(signal.get("items") or []),
        "items": signal.get("items") or [],
        "message_zh": signal.get("message_zh", ""),
    }


def _match_message(identity: dict, injuries: dict, lineup: dict, weather: dict, news: dict) -> str:
    parts = [identity.get("message_zh", "已读取主数据。")]
    parts.append(f"伤停：{injuries.get('label_zh', injuries.get('status'))}")
    parts.append(f"首发：{lineup.get('label_zh', lineup.get('status'))}")
    parts.append(f"天气：{weather.get('label_zh', weather.get('status'))}")
    parts.append(f"新闻：{news.get('label_zh', news.get('status'))}")
    return "；".join(parts)


def _coverage_score(matched: int, total: int, status: dict) -> int:
    if status.get("status") != "ok":
        return 0
    if total <= 0:
        return 45
    return round(45 + matched / total * 45)


def _ratio_score(count: int, total: int) -> int:
    if total <= 0:
        return 0
    return round(count / total * 90)


def _summary(cards: list[dict]) -> str:
    parts = [f"{card['source']}：{card.get('label_zh')}，覆盖 {card.get('coverage')}" for card in cards]
    return "；".join(parts)


def _warnings(api_status: dict, odds_status: dict, match_rows: list[dict]) -> list[str]:
    warnings = []
    for status in (api_status, odds_status):
        if status.get("status") not in {"ok", "not_configured"}:
            warnings.append(status.get("message_zh", "第三方数据源暂不可用。"))
    for row in match_rows:
        for key in ("injuries", "lineup", "weather", "news"):
            status = (row.get(key) or {}).get("status")
            if status == "error":
                warnings.append(f"{row.get('match')} {key} 读取异常。")
    return warnings


def _public_api_status(status: dict) -> dict:
    return {key: status.get(key) for key in ("source", "configured", "status", "date", "fixtures_count", "message_zh", "cache")}


def _public_odds_status(status: dict) -> dict:
    return {key: status.get(key) for key in ("source", "configured", "status", "soccer_sports_count", "active_soccer_sports_count", "events_count", "sport_keys_checked", "requests_remaining", "requests_used", "message_zh")}


def _count(rows: list[dict], key: str, status: str) -> int:
    return sum(1 for row in rows if (row.get(key) or {}).get("status") == status)


def _count_signal(rows: list[dict], key: str, statuses: set[str]) -> int:
    return sum(1 for row in rows if (row.get(key) or {}).get("status") in statuses)


def _future_value(future, fallback: dict, *, timeout: int) -> dict:
    if future is None:
        return fallback
    try:
        return future.result(timeout=timeout)
    except Exception:
        return fallback


def _unknown_signal(label: str, message: str) -> dict:
    return {"status": "not_connected", "label_zh": f"{label}未接入", "impact": "unknown", "items": [], "message_zh": message}


def _value(obj, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

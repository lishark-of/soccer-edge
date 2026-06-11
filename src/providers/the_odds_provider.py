from __future__ import annotations

import json
import ssl
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.config.local_env import get_secret, mask_secret
from src.providers.source_cache import cached_json
from src.providers.the_odds_api_client import BASE_URL

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None

PREFERRED_SOCCER_KEYS = [
    "soccer_international_friendlies",
    "soccer_fifa_world_cup",
    "soccer_uefa_nations_league",
    "soccer_conmebol_copa_america",
    "soccer_epl",
]


def get_the_odds_soccer_sports(*, timeout: int = 8, use_cache: bool = True) -> dict:
    key = get_secret("JC_EDGE_THE_ODDS_API_KEY")
    if not key:
        return _not_configured()

    def fetch() -> dict:
        query = urlencode({"apiKey": key})
        request = Request(f"{BASE_URL}/v4/sports/?{query}", headers={"Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
            headers = dict(response.headers.items())
        sports = payload if isinstance(payload, list) else []
        soccer = [item for item in sports if isinstance(item, dict) and str(item.get("key", "")).startswith("soccer_")]
        active = [item for item in soccer if item.get("active", True)]
        return {
            "source": "the_odds_api",
            "configured": True,
            "status": "ok",
            "sports_count": len(sports),
            "soccer_sports_count": len(soccer),
            "active_soccer_sports_count": len(active),
            "soccer_sports": active,
            "requests_remaining": headers.get("x-requests-remaining") or headers.get("X-Requests-Remaining"),
            "requests_used": headers.get("x-requests-used") or headers.get("X-Requests-Used"),
            "message_zh": "The Odds API 足球市场可用，用作海外赔率交叉参考。",
        }

    try:
        if use_cache:
            cache = cached_json("the_odds_api", "soccer_sports", 6 * 60 * 60, fetch)
            data = cache.get("data") or {}
            data["cache"] = {"status": cache.get("status"), "age_seconds": cache.get("age_seconds"), "path": cache.get("path")}
            return data
        return fetch()
    except Exception as exc:  # noqa: BLE001
        return {
            "source": "the_odds_api",
            "configured": True,
            "masked_key": mask_secret(key),
            "status": "error",
            "soccer_sports_count": 0,
            "soccer_sports": [],
            "message_zh": f"The Odds API 足球市场读取失败：{str(exc).splitlines()[0][:160]}",
        }


def get_the_odds_soccer_odds(target_date: str | None, *, max_sports: int = 3, timeout: int = 8, use_cache: bool = True) -> dict:
    key = get_secret("JC_EDGE_THE_ODDS_API_KEY")
    if not key:
        return _not_configured()
    sports_status = get_the_odds_soccer_sports(timeout=timeout, use_cache=use_cache)
    if sports_status.get("status") != "ok":
        return {**sports_status, "events": [], "events_count": 0}
    active_keys = [item.get("key") for item in sports_status.get("soccer_sports", []) if isinstance(item, dict)]
    keys = [key for key in PREFERRED_SOCCER_KEYS if key in active_keys]
    keys.extend([key for key in active_keys if key not in keys])
    keys = keys[:max_sports]
    events: list[dict] = []
    responses: list[dict] = []
    for sport_key in keys:
        cache_key = f"odds_{sport_key}_{target_date or 'all'}"

        def fetch_one(sport_key=sport_key) -> dict:
            query = urlencode({"apiKey": key, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"})
            request = Request(f"{BASE_URL}/v4/sports/{sport_key}/odds/?{query}", headers={"Accept": "application/json"}, method="GET")
            with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
                payload = json.loads(response.read().decode("utf-8"))
                headers = dict(response.headers.items())
            return {"sport_key": sport_key, "payload": payload if isinstance(payload, list) else [], "headers": headers}

        try:
            cache = cached_json("the_odds_api", cache_key, 30 * 60, fetch_one) if use_cache else {"status": "miss", "data": fetch_one()}
            data = cache.get("data") or {}
            rows = _condense_odds_events(data.get("payload") or [], sport_key, target_date)
            events.extend(rows)
            responses.append({"sport_key": sport_key, "cache_status": cache.get("status"), "events": len(rows)})
        except Exception as exc:  # noqa: BLE001
            responses.append({"sport_key": sport_key, "status": "error", "message_zh": str(exc).splitlines()[0][:120]})
    return {
        "source": "the_odds_api",
        "configured": True,
        "status": "ok" if events or responses else "empty",
        "sport_keys_checked": keys,
        "events_count": len(events),
        "events": events,
        "responses": responses,
        "requests_remaining": sports_status.get("requests_remaining"),
        "requests_used": sports_status.get("requests_used"),
        "message_zh": f"The Odds API 已低频检查 {len(keys)} 个足球市场，匹配到 {len(events)} 条候选赔率事件。",
    }


def _condense_odds_events(payload: list[dict], sport_key: str, target_date: str | None) -> list[dict]:
    rows = []
    for item in payload or []:
        commence = str(item.get("commence_time") or "")
        if target_date and commence[:10]:
            if not _within_date_window(commence[:10], target_date):
                continue
        bookmakers = item.get("bookmakers") or []
        best_h2h = _first_h2h(bookmakers)
        rows.append(
            {
                "event_id": item.get("id"),
                "sport_key": sport_key,
                "date": commence[:10],
                "kickoff_at": commence,
                "home_team": item.get("home_team"),
                "away_team": item.get("away_team"),
                "bookmaker_count": len(bookmakers),
                "h2h_odds": best_h2h,
            }
        )
    return rows


def _first_h2h(bookmakers: list[dict]) -> dict:
    for book in bookmakers:
        for market in book.get("markets", []) or []:
            if market.get("key") == "h2h":
                return {"bookmaker": book.get("title"), "outcomes": market.get("outcomes", [])[:3]}
    return {}


def _within_date_window(event_date: str, target_date: str) -> bool:
    try:
        event = datetime.strptime(event_date, "%Y-%m-%d").date()
        target = datetime.strptime(target_date[:10], "%Y-%m-%d").date()
        return target - timedelta(days=1) <= event <= target + timedelta(days=1)
    except ValueError:
        return True


def _not_configured() -> dict:
    return {
        "source": "the_odds_api",
        "configured": False,
        "status": "not_configured",
        "soccer_sports_count": 0,
        "events_count": 0,
        "events": [],
        "message_zh": "未配置 The Odds API key，海外赔率交叉参考保持 unknown。",
    }


def _ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())

from __future__ import annotations

import json
import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.config.local_env import get_secret, mask_secret
from src.providers.api_football_client import BASE_URL
from src.providers.source_cache import cached_json

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None


def get_api_football_fixtures(target_date: str | None, *, timeout: int = 8, use_cache: bool = True) -> dict:
    key = get_secret("JC_EDGE_API_FOOTBALL_KEY")
    if not key:
        return _not_configured()
    date = target_date or ""
    cache_key = f"fixtures_{date or 'unknown'}"

    def fetch() -> dict:
        query = urlencode({"date": date}) if date else ""
        url = f"{BASE_URL}/fixtures" + (f"?{query}" if query else "")
        request = Request(url, headers={"x-apisports-key": key, "Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _condense_payload(payload, date)

    try:
        if use_cache:
            cache = cached_json("api_football", cache_key, 6 * 60 * 60, fetch)
            data = cache.get("data") or {}
            data["cache"] = {"status": cache.get("status"), "age_seconds": cache.get("age_seconds"), "path": cache.get("path")}
            return data
        return fetch()
    except Exception as exc:  # noqa: BLE001
        return {
            "source": "api_football",
            "configured": True,
            "masked_key": mask_secret(key),
            "status": "error",
            "date": date,
            "fixtures": [],
            "message_zh": f"API-Football 赛程读取失败：{str(exc).splitlines()[0][:160]}",
        }


def _condense_payload(payload: dict, date: str) -> dict:
    response = payload.get("response") if isinstance(payload, dict) else []
    rows = []
    for item in response or []:
        if not isinstance(item, dict):
            continue
        fixture = item.get("fixture") or {}
        teams = item.get("teams") or {}
        league = item.get("league") or {}
        venue = fixture.get("venue") or {}
        rows.append(
            {
                "fixture_id": fixture.get("id"),
                "date": str(fixture.get("date") or "")[:10],
                "kickoff_at": fixture.get("date"),
                "timestamp": fixture.get("timestamp"),
                "league": league.get("name"),
                "country": league.get("country"),
                "home_team": (teams.get("home") or {}).get("name"),
                "away_team": (teams.get("away") or {}).get("name"),
                "venue_name": venue.get("name"),
                "venue_city": venue.get("city"),
                "status_short": (fixture.get("status") or {}).get("short"),
            }
        )
    return {
        "source": "api_football",
        "configured": True,
        "masked_key": "已配置",
        "status": "ok",
        "date": date,
        "fixtures_count": len(rows),
        "fixtures": rows,
        "message_zh": f"API-Football 已读取 {len(rows)} 场赛程候选，用于跨源匹配和赛程补充。",
    }


def _not_configured() -> dict:
    return {
        "source": "api_football",
        "configured": False,
        "status": "not_configured",
        "fixtures_count": 0,
        "fixtures": [],
        "message_zh": "未配置 API-Football key，赛程/球队/伤停/阵容补充保持 unknown。",
    }


def _ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())

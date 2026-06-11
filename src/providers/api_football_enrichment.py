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


def get_fixture_enrichment(fixture_id: int | str | None, *, timeout: int = 8, use_cache: bool = True) -> dict:
    if not fixture_id:
        return {
            "source": "api_football",
            "status": "unmatched",
            "injuries": _unmatched_signal("伤停"),
            "lineup": _unmatched_signal("首发"),
            "message_zh": "未匹配到 API-Football fixture_id，伤停和首发保持 unknown。",
        }
    key = get_secret("JC_EDGE_API_FOOTBALL_KEY")
    if not key:
        return {
            "source": "api_football",
            "status": "not_configured",
            "injuries": _unmatched_signal("伤停"),
            "lineup": _unmatched_signal("首发"),
            "message_zh": "未配置 API-Football key，无法读取伤停和首发。",
        }
    injuries = _cached_endpoint("injuries", {"fixture": str(fixture_id)}, ttl_seconds=60 * 60, timeout=timeout, use_cache=use_cache)
    lineups = _cached_endpoint("fixtures/lineups", {"fixture": str(fixture_id)}, ttl_seconds=15 * 60, timeout=timeout, use_cache=use_cache)
    injury_signal = _injury_signal(injuries)
    lineup_signal = _lineup_signal(lineups)
    return {
        "source": "api_football",
        "fixture_id": str(fixture_id),
        "status": "ok" if injuries.get("status") != "error" and lineups.get("status") != "error" else "partial_error",
        "injuries": injury_signal,
        "lineup": lineup_signal,
        "cache": {"injuries": injuries.get("cache"), "lineup": lineups.get("cache")},
        "message_zh": f"伤停：{injury_signal.get('label_zh')}；首发：{lineup_signal.get('label_zh')}。",
    }


def _cached_endpoint(endpoint: str, params: dict[str, str], *, ttl_seconds: int, timeout: int, use_cache: bool) -> dict:
    key = get_secret("JC_EDGE_API_FOOTBALL_KEY")
    if not key:
        return {"status": "not_configured", "response": []}
    cache_key = endpoint.replace("/", "_") + "_" + "_".join(f"{k}_{v}" for k, v in sorted(params.items()))

    def fetch() -> dict:
        query = urlencode(params)
        request = Request(f"{BASE_URL}/{endpoint}?{query}", headers={"x-apisports-key": key, "Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"status": "ok", "response": payload.get("response", []) if isinstance(payload, dict) else []}

    try:
        if use_cache:
            cache = cached_json("api_football_enrichment", cache_key, ttl_seconds, fetch)
            data = cache.get("data") or {"status": "empty", "response": []}
            data["cache"] = {"status": cache.get("status"), "age_seconds": cache.get("age_seconds"), "path": cache.get("path")}
            return data
        return fetch()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "response": [], "message_zh": f"API-Football {endpoint} 读取失败：{str(exc).splitlines()[0][:140]}", "masked_key": mask_secret(key)}


def _injury_signal(payload: dict) -> dict:
    if payload.get("status") == "error":
        return {"status": "error", "label_zh": "读取异常", "impact": "unknown", "items": [], "message_zh": payload.get("message_zh", "伤停读取失败。")}
    rows = []
    for item in payload.get("response", []) or []:
        if not isinstance(item, dict):
            continue
        player = item.get("player") or {}
        team = item.get("team") or {}
        rows.append({"player": player.get("name"), "team": team.get("name"), "reason": item.get("reason"), "type": item.get("type")})
    if rows:
        return {"status": "connected", "label_zh": f"已发现 {len(rows)} 条公开伤停", "impact": "context", "items": rows, "message_zh": "API-Football 返回公开伤停条目。"}
    return {"status": "covered_empty", "label_zh": "未返回公开伤停", "impact": "unknown", "items": [], "message_zh": "API-Football 当前未返回伤停条目；这不等于确认无人缺阵。"}


def _lineup_signal(payload: dict) -> dict:
    if payload.get("status") == "error":
        return {"status": "error", "label_zh": "读取异常", "impact": "unknown", "items": [], "message_zh": payload.get("message_zh", "首发读取失败。")}
    rows = []
    for item in payload.get("response", []) or []:
        if not isinstance(item, dict):
            continue
        team = item.get("team") or {}
        rows.append({
            "team": team.get("name"),
            "formation": item.get("formation"),
            "start_count": len(item.get("startXI") or []),
            "substitute_count": len(item.get("substitutes") or []),
        })
    if rows:
        return {"status": "connected", "label_zh": "已公布首发", "impact": "context", "items": rows, "message_zh": "API-Football 已返回首发阵型和名单数量。"}
    return {"status": "not_available", "label_zh": "首发未公布或未覆盖", "impact": "unknown", "items": [], "message_zh": "首发通常临近开赛才公布；当前没有可靠首发数据。"}


def _unmatched_signal(label: str) -> dict:
    return {"status": "not_connected", "label_zh": f"{label}未接入", "impact": "unknown", "items": [], "message_zh": f"{label}没有可靠数据，系统不会编造。"}


def _ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())

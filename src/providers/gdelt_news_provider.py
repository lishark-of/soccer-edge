from __future__ import annotations

import json
import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.providers.source_cache import cached_json

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

TEAM_EN = {
    "葡萄牙": "Portugal",
    "尼日利亚": "Nigeria",
    "英格兰": "England",
    "哥斯达": "Costa Rica",
    "哥斯达黎加": "Costa Rica",
    "鹿岛鹿角": "Kashima Antlers",
    "弗拉门戈": "Flamengo",
}


def get_match_news(home_team: str | None, away_team: str | None, *, timeout: int = 8, use_cache: bool = True) -> dict:
    if not home_team or not away_team:
        return {"status": "not_connected", "label_zh": "缺少球队名", "impact": "unknown", "items": [], "message_zh": "缺少球队名，无法检索新闻。"}
    query = _query(home_team, away_team)

    def fetch() -> dict:
        params = urlencode({"query": query, "mode": "ArtList", "format": "json", "maxrecords": 8, "sort": "HybridRel"})
        request = Request(f"{GDELT_DOC_URL}?{params}", headers={"Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        articles = payload.get("articles") if isinstance(payload, dict) else []
        return {"status": "ok", "articles": _condense_articles(articles)}

    try:
        cache_key = f"news_{home_team}_{away_team}"
        cache = cached_json("gdelt_news", cache_key, 60 * 60, fetch) if use_cache else {"data": fetch(), "status": "miss"}
        data = cache.get("data") or {}
        articles = data.get("articles") or []
        if articles:
            return {"status": "connected", "label_zh": f"找到 {len(articles)} 条相关新闻", "impact": "context", "items": articles, "cache": {"status": cache.get("status"), "age_seconds": cache.get("age_seconds")}, "message_zh": "GDELT 返回相关新闻标题，仅用于情报提示，不改变概率。"}
        return {"status": "not_found", "label_zh": "未发现可靠新闻", "impact": "unknown", "items": [], "cache": {"status": cache.get("status"), "age_seconds": cache.get("age_seconds")}, "message_zh": "GDELT 当前未返回相关新闻；系统不会编造新闻。"}
    except Exception as exc:  # noqa: BLE001
        reason = str(exc).splitlines()[0][:120]
        if "timed out" in reason.lower() or "handshake" in reason.lower():
            reason = "新闻源暂时没有在限定时间内返回。"
        return {
            "status": "timeout",
            "label_zh": "新闻暂未返回",
            "impact": "unknown",
            "items": [],
            "message_zh": f"GDELT 暂未返回可用新闻：{reason}；系统不会编造新闻。",
        }


def _query(home_team: str, away_team: str) -> str:
    home = TEAM_EN.get(str(home_team), str(home_team))
    away = TEAM_EN.get(str(away_team), str(away_team))
    return f'("{home}" "{away}" football) OR ("{home}" "{away}" soccer) OR ("{home}" injury football) OR ("{away}" injury football)'


def _condense_articles(articles: list[dict]) -> list[dict]:
    rows = []
    seen = set()
    for item in articles or []:
        title = item.get("title")
        url = item.get("url")
        if not title or url in seen:
            continue
        seen.add(url)
        rows.append({"title": title, "source": item.get("sourceCountry") or item.get("domain"), "url": url, "seendate": item.get("seendate"), "language": item.get("language")})
        if len(rows) >= 6:
            break
    return rows


def _ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())

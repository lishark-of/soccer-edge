from __future__ import annotations

import json
import ssl
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.providers.source_cache import cached_json

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

CITY_FALLBACKS = {
    "葡萄牙": "Lisbon",
    "Portugal": "Lisbon",
    "尼日利亚": "Abuja",
    "Nigeria": "Abuja",
    "英格兰": "London",
    "England": "London",
    "哥斯达": "San Jose",
    "哥斯达黎加": "San Jose",
    "Costa Rica": "San Jose",
    "匈牙利": "Budapest",
    "Hungary": "Budapest",
    "哈萨克": "Astana",
    "哈萨克斯坦": "Astana",
    "Kazakhstan": "Astana",
    "鹿岛鹿角": "Kashima",
    "Kashima Antlers": "Kashima",
    "弗拉门戈": "Rio de Janeiro",
    "Flamengo": "Rio de Janeiro",
}

def get_match_weather(
    city: str | None,
    kickoff_at: str | None,
    *,
    home_team: str | None = None,
    away_team: str | None = None,
    timeout: int = 8,
    use_cache: bool = True,
) -> dict:
    resolved = resolve_weather_city(city, home_team, away_team)
    if not resolved.get("city"):
        return {
            "status": "not_connected",
            "label_zh": "缺少城市/球场坐标",
            "impact": "unknown",
            "message_zh": "缺少 venue city 或 match_city，暂不能读取天气；可在 external_signals JSON 里补充 match_city。",
            "items": [],
        }
    city = resolved["city"]
    geo = _geocode_city(city, timeout=timeout, use_cache=use_cache)
    if geo.get("status") != "ok":
        return {"status": "not_connected", "label_zh": "城市坐标未匹配", "impact": "unknown", "message_zh": geo.get("message_zh", "城市坐标读取失败。"), "items": []}
    forecast = _forecast(geo["latitude"], geo["longitude"], kickoff_at, city, timeout=timeout, use_cache=use_cache)
    if forecast.get("status") != "ok":
        return {"status": "error", "label_zh": "天气读取异常", "impact": "unknown", "message_zh": forecast.get("message_zh", "天气读取失败。"), "items": []}
    item = forecast.get("weather") or {}
    weather_status = "fallback_estimated" if resolved.get("source") == "team_country_fallback" else "confirmed"
    return {
        "status": weather_status,
        "label_zh": "天气兜底估算" if weather_status == "fallback_estimated" else "天气已确认",
        "impact": _weather_impact(item),
        "city": city,
        "city_source": resolved.get("source"),
        "confidence": "low" if weather_status == "fallback_estimated" else "high",
        "items": [item],
        "message_zh": _weather_message(item, resolved),
    }


def resolve_weather_city(city: str | None, home_team: str | None = None, away_team: str | None = None) -> dict:
    if city:
        return {"city": str(city), "source": "venue_city", "message_zh": "使用赛程返回的球场城市。"}
    for team in (home_team, away_team):
        if team and CITY_FALLBACKS.get(str(team)):
            return {
                "city": CITY_FALLBACKS[str(team)],
                "source": "team_country_fallback",
                "message_zh": f"缺少球场城市，暂用 {team} 的国家/球队城市兜底；如需更准确天气，请在 external_signals JSON 补充 match_city。",
            }
    return {"city": None, "source": "missing", "message_zh": "缺少城市。"}


def _geocode_city(city: str, *, timeout: int, use_cache: bool) -> dict:
    def fetch() -> dict:
        query = urlencode({"name": city, "count": 1, "language": "zh", "format": "json"})
        request = Request(f"{GEOCODE_URL}?{query}", headers={"Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        results = payload.get("results") if isinstance(payload, dict) else []
        if not results:
            return {"status": "empty", "message_zh": f"Open-Meteo 未找到城市坐标：{city}"}
        first = results[0]
        return {"status": "ok", "name": first.get("name"), "country": first.get("country"), "latitude": first.get("latitude"), "longitude": first.get("longitude")}
    try:
        cache = cached_json("weather", f"geocode_{city}", 30 * 24 * 60 * 60, fetch) if use_cache else {"data": fetch(), "status": "miss"}
        data = cache.get("data") or {}
        data["cache"] = {"status": cache.get("status"), "age_seconds": cache.get("age_seconds")}
        return data
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message_zh": f"Open-Meteo 城市坐标读取失败：{str(exc).splitlines()[0][:140]}"}


def _forecast(lat, lon, kickoff_at: str | None, city: str, *, timeout: int, use_cache: bool) -> dict:
    target_date = str(kickoff_at or "")[:10] or datetime.now().date().isoformat()

    def fetch() -> dict:
        query = urlencode({
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability,precipitation,wind_speed_10m",
            "timezone": "auto",
            "start_date": target_date,
            "end_date": target_date,
        })
        request = Request(f"{FORECAST_URL}?{query}", headers={"Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _pick_weather(payload, kickoff_at, city)
    try:
        cache = cached_json("weather", f"forecast_{city}_{target_date}", 2 * 60 * 60, fetch) if use_cache else {"data": fetch(), "status": "miss"}
        data = cache.get("data") or {}
        data["cache"] = {"status": cache.get("status"), "age_seconds": cache.get("age_seconds")}
        return data
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message_zh": f"Open-Meteo 天气读取失败：{str(exc).splitlines()[0][:140]}"}


def _pick_weather(payload: dict, kickoff_at: str | None, city: str) -> dict:
    hourly = payload.get("hourly") if isinstance(payload, dict) else {}
    times = hourly.get("time") or []
    if not times:
        return {"status": "empty", "message_zh": "Open-Meteo 未返回小时级天气。"}
    kickoff_hour = str(kickoff_at or "")[:13]
    idx = 0
    if kickoff_hour:
        for i, value in enumerate(times):
            if str(value).startswith(kickoff_hour):
                idx = i
                break
    item = {
        "city": city,
        "time": times[idx],
        "temperature_c": _at(hourly.get("temperature_2m"), idx),
        "precipitation_probability": _at(hourly.get("precipitation_probability"), idx),
        "precipitation_mm": _at(hourly.get("precipitation"), idx),
        "wind_speed_kmh": _at(hourly.get("wind_speed_10m"), idx),
    }
    return {"status": "ok", "weather": item}


def _weather_impact(item: dict) -> str:
    rain_prob = float(item.get("precipitation_probability") or 0)
    wind = float(item.get("wind_speed_kmh") or 0)
    if rain_prob >= 65 or wind >= 35:
        return "medium"
    if rain_prob >= 35 or wind >= 22:
        return "small"
    return "low"


def _weather_message(item: dict, resolved: dict) -> str:
    suffix = resolved.get("message_zh") or ""
    return f"天气：{item.get('city')} {item.get('time')}，温度 {item.get('temperature_c')}°C，降雨概率 {item.get('precipitation_probability')}%，风速 {item.get('wind_speed_kmh')} km/h。{suffix}"


def _at(values, index: int):
    try:
        return values[index]
    except Exception:
        return None


def _ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())

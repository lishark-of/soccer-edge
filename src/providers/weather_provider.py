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


def get_match_weather(city: str | None, kickoff_at: str | None, *, timeout: int = 8, use_cache: bool = True) -> dict:
    if not city:
        return {"status": "not_connected", "label_zh": "缺少城市/球场坐标", "impact": "unknown", "message_zh": "API-Football 未提供 venue city，暂不能读取天气。", "items": []}
    geo = _geocode_city(city, timeout=timeout, use_cache=use_cache)
    if geo.get("status") != "ok":
        return {"status": "not_connected", "label_zh": "城市坐标未匹配", "impact": "unknown", "message_zh": geo.get("message_zh", "城市坐标读取失败。"), "items": []}
    forecast = _forecast(geo["latitude"], geo["longitude"], kickoff_at, city, timeout=timeout, use_cache=use_cache)
    if forecast.get("status") != "ok":
        return {"status": "error", "label_zh": "天气读取异常", "impact": "unknown", "message_zh": forecast.get("message_zh", "天气读取失败。"), "items": []}
    item = forecast.get("weather") or {}
    return {"status": "connected", "label_zh": "天气已接入", "impact": _weather_impact(item), "city": city, "items": [item], "message_zh": _weather_message(item)}


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


def _weather_message(item: dict) -> str:
    return f"天气：{item.get('city')} {item.get('time')}，温度 {item.get('temperature_c')}°C，降雨概率 {item.get('precipitation_probability')}%，风速 {item.get('wind_speed_kmh')} km/h。"


def _at(values, index: int):
    try:
        return values[index]
    except Exception:
        return None


def _ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())

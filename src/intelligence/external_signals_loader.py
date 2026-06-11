from __future__ import annotations

import json
from pathlib import Path
from typing import Any

UNKNOWN_SIGNAL = {"status": "not_connected", "impact": "unknown", "items": []}
SUPPORTED_KEYS = ["injuries", "lineup", "weather", "news", "travel", "motivation", "neutral_ground", "tournament_importance"]


def load_external_signals(path: str | None = None) -> dict[str, dict]:
    signals, _status = load_external_signals_with_status(path)
    return signals


def load_external_signals_with_status(path: str | None = None) -> tuple[dict[str, dict], dict]:
    if not path:
        return {}, {
            "source_type": "not_provided",
            "path_provided": False,
            "path_label": None,
            "load_status": "not_provided",
            "signals_loaded": 0,
            "invalid_items": 0,
            "matched_keys": [],
            "message_zh": "未提供外部情报 JSON；新闻、伤停、首发、天气、旅行、战意保持 unknown。",
        }
    path_obj = Path(path)
    path_label = path_obj.name
    try:
        raw = json.loads(path_obj.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, _status(path_label, "read_error", 0, 0, [], "外部情报 JSON 不存在；系统不会编造情报。")
    except json.JSONDecodeError:
        return {}, _status(path_label, "parse_error", 0, 0, [], "外部情报 JSON 格式无法解析；系统不会编造情报。")
    except Exception:
        return {}, _status(path_label, "read_error", 0, 0, [], "外部情报 JSON 无法读取；系统不会编造情报。")

    items = _items(raw)
    signals: dict[str, dict] = {}
    invalid = 0
    for item in items:
        if not isinstance(item, dict):
            invalid += 1
            continue
        normalized = normalize_external_signal(item)
        keys = _keys(normalized)
        if not keys:
            invalid += 1
            continue
        for key in keys:
            signals[key] = normalized
    return signals, _status(
        path_label,
        "loaded",
        len({id(v) for v in signals.values()}),
        invalid,
        sorted(signals.keys()),
        "已读取用户提供的本地 JSON 情报；仅用于可信度和观察解释，不联网、不编造、不写文件。",
    )


def normalize_external_signal(item: dict[str, Any]) -> dict:
    lineup = item.get("lineup")
    if lineup is None and item.get("lineup_status") is not None:
        lineup = {"status": item.get("lineup_status")}
    news = item.get("news")
    if news is None and item.get("news_summary") is not None:
        news = item.get("news_summary")
    return {
        "match_id": item.get("match_id"),
        "match_num": item.get("match_num") or item.get("match_no"),
        "match_no": item.get("match_no") or item.get("match_num"),
        "home_team": item.get("home_team"),
        "away_team": item.get("away_team"),
        "injuries": _signal(item.get("injuries"), "伤停"),
        "lineup": _signal(lineup, "首发"),
        "weather": _signal(item.get("weather"), "天气"),
        "news": _signal(news, "新闻面"),
        "travel": _signal(item.get("travel"), "旅行"),
        "motivation": _signal(item.get("motivation"), "战意"),
        "neutral_ground": _signal(item.get("neutral_ground"), "中立场"),
        "tournament_importance": _signal(item.get("tournament_importance"), "赛事重要性"),
        "source": "user_json",
    }


def signal_or_unknown(payload: dict | None, key: str) -> dict:
    if not payload:
        return dict(UNKNOWN_SIGNAL)
    value = payload.get(key)
    if isinstance(value, dict) and value.get("status"):
        return value
    return _signal(value, key)


def preview_external_signals(path: str | None, date: str | None = None) -> dict:
    signals, status = load_external_signals_with_status(path)
    fields = {key: 0 for key in SUPPORTED_KEYS}
    for item in {id(v): v for v in signals.values()}.values():
        for key in SUPPORTED_KEYS:
            if (item.get(key) or {}).get("status") == "connected":
                fields[key] += 1
    supplied = [key for key, count in fields.items() if count > 0]
    missing = [key for key, count in fields.items() if count <= 0]
    return {
        "preview_version": "phase2q_external_signals_preview_v0",
        "date": date,
        "status": status,
        "signals_count": status.get("signals_loaded", 0),
        "supplied_fields": supplied,
        "missing_fields": missing,
        "field_coverage": fields,
        "signals": list({id(v): v for v in signals.values()}.values()),
        "message_zh": status.get("message_zh"),
        "disclaimer": "本地情报 JSON 只用于补齐可信度和解释，不联网、不编造、不构成投注建议。",
    }


def _items(raw: Any) -> list[Any]:
    if isinstance(raw, dict) and isinstance(raw.get("matches"), list):
        return raw["matches"]
    if isinstance(raw, list):
        return raw
    return [raw]


def _keys(item: dict) -> list[str]:
    keys = []
    for key in (item.get("match_id"), item.get("match_num"), item.get("match_no")):
        if key:
            keys.append(str(key))
    home = item.get("home_team")
    away = item.get("away_team")
    if home and away:
        keys.append(f"{home}__{away}")
    return list(dict.fromkeys(keys))


def _signal(value: Any, label: str) -> dict:
    if value is None or value == "" or value == [] or value == {} or value == "unknown":
        return {"status": "not_connected", "impact": "unknown", "items": [], "message_zh": f"{label}未提供，保持 unknown。"}
    if isinstance(value, dict) and str(value.get("status", "")).lower() in {"unknown", "not_connected"}:
        return {"status": "not_connected", "impact": value.get("impact", "unknown"), "items": [], "message_zh": f"{label}提供为 unknown。"}
    items = value if isinstance(value, list) else [value]
    return {"status": "connected", "impact": "context", "items": items, "message_zh": f"{label}由本地 JSON 提供。"}


def _status(path_label: str, load_status: str, signals_loaded: int, invalid_items: int, keys: list[str], message_zh: str) -> dict:
    return {
        "source_type": "user_json",
        "path_provided": True,
        "path_label": path_label,
        "load_status": load_status,
        "signals_loaded": signals_loaded,
        "invalid_items": invalid_items,
        "matched_keys": keys,
        "message_zh": message_zh,
    }

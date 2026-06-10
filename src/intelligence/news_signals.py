from __future__ import annotations

import json
from pathlib import Path

UNKNOWN_SIGNAL = {"status": "not_connected", "impact": "unknown", "items": []}


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
            "message_zh": "未提供外部情报 JSON；新闻、伤停、首发、天气、战意保持 unknown。",
        }
    path_obj = Path(path)
    path_label = path_obj.name
    try:
        raw_text = path_obj.read_text(encoding="utf-8")
    except Exception:
        return {}, _external_status(path_label, "read_error", 0, 0, "外部情报 JSON 无法读取；系统不会编造情报。")
    try:
        raw = json.loads(raw_text)
    except Exception:
        return {}, _external_status(path_label, "parse_error", 0, 0, "外部情报 JSON 格式无法解析；系统不会编造情报。")
    items = raw if isinstance(raw, list) else [raw]
    signals = {}
    invalid_items = 0
    for item in items:
        if isinstance(item, dict) and item.get("match_id"):
            signals[str(item["match_id"])] = item
        else:
            invalid_items += 1
    return signals, _external_status(
        path_label,
        "loaded",
        len(signals),
        invalid_items,
        "已读取用户提供的本地 JSON 情报；仅用于解释信心，不参与真实下单。",
    )


def _external_status(path_label: str, load_status: str, signals_loaded: int, invalid_items: int, message_zh: str) -> dict:
    return {
        "source_type": "user_json",
        "path_provided": True,
        "path_label": path_label,
        "load_status": load_status,
        "signals_loaded": signals_loaded,
        "invalid_items": invalid_items,
        "message_zh": message_zh,
    }


def signal_or_unknown(payload: dict | None, key: str) -> dict:
    if not payload or key not in payload:
        return dict(UNKNOWN_SIGNAL)
    value = payload.get(key)
    if not value:
        return dict(UNKNOWN_SIGNAL)
    return {"status": "connected", "impact": "context", "items": value if isinstance(value, list) else [value]}

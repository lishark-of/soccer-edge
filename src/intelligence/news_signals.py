from __future__ import annotations

import json
from pathlib import Path

UNKNOWN_SIGNAL = {"status": "not_connected", "impact": "unknown", "items": []}


def load_external_signals(path: str | None = None) -> dict[str, dict]:
    if not path:
        return {}
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    items = raw if isinstance(raw, list) else [raw]
    signals = {}
    for item in items:
        if isinstance(item, dict) and item.get("match_id"):
            signals[str(item["match_id"])] = item
    return signals


def signal_or_unknown(payload: dict | None, key: str) -> dict:
    if not payload or key not in payload:
        return dict(UNKNOWN_SIGNAL)
    value = payload.get(key)
    if not value:
        return dict(UNKNOWN_SIGNAL)
    return {"status": "connected", "impact": "context", "items": value if isinstance(value, list) else [value]}

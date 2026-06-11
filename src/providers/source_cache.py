from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable, Any

CACHE_ROOT = Path("data/cache")


def cached_json(namespace: str, key: str, ttl_seconds: int, fetcher: Callable[[], Any]) -> dict:
    path = _cache_path(namespace, key)
    now = time.time()
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            age = now - float(payload.get("cached_at", 0))
            if age <= ttl_seconds:
                return {"status": "hit", "age_seconds": round(age, 1), "path": str(path), "data": payload.get("data")}
        except Exception:
            pass
    data = fetcher()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cached_at": now, "data": data}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "miss", "age_seconds": 0, "path": str(path), "data": data}


def _cache_path(namespace: str, key: str) -> Path:
    safe_key = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in key)
    return CACHE_ROOT / namespace / f"{safe_key}.json"

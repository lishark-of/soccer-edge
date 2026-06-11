from __future__ import annotations

import json
import ssl
from urllib.request import Request, urlopen

from src.config.local_env import get_secret, mask_secret

try:  # certifi is bundled in the local Python used by this project.
    import certifi
except Exception:  # pragma: no cover - fallback for minimal Python installs
    certifi = None


BASE_URL = "https://v3.football.api-sports.io"


def verify_api_football(timeout: int = 8) -> dict:
    key = get_secret("JC_EDGE_API_FOOTBALL_KEY")
    if not key:
        return {
            "source": "api_football",
            "configured": False,
            "status": "not_configured",
            "message_zh": "未配置 JC_EDGE_API_FOOTBALL_KEY。",
        }
    request = Request(
        f"{BASE_URL}/status",
        headers={"x-apisports-key": key, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - return safe status for UI
        return {
            "source": "api_football",
            "configured": True,
            "masked_key": mask_secret(key),
            "status": "error",
            "message_zh": f"API-Football 验证失败：{str(exc).splitlines()[0][:160]}",
        }
    response = payload.get("response") if isinstance(payload, dict) else {}
    return {
        "source": "api_football",
        "configured": True,
        "masked_key": mask_secret(key),
        "status": "ok",
        "host": BASE_URL,
        "account": _safe_pick(response, ["account"]),
        "subscription": _safe_pick(response, ["subscription"]),
        "requests": _safe_pick(response, ["requests"]),
        "message_zh": "API-Football key 可用；可用于赛程、球队、阵容/伤停可用性检测。",
    }


def _ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def _safe_pick(value: object, keys: list[str]) -> object:
    if not isinstance(value, dict):
        return {}
    return {key: value.get(key) for key in keys if key in value}

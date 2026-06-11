from __future__ import annotations

import json
import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.config.local_env import get_secret, mask_secret

try:  # certifi is bundled in the local Python used by this project.
    import certifi
except Exception:  # pragma: no cover - fallback for minimal Python installs
    certifi = None


BASE_URL = "https://api.the-odds-api.com"


def verify_the_odds_api(timeout: int = 8) -> dict:
    key = get_secret("JC_EDGE_THE_ODDS_API_KEY")
    if not key:
        return {
            "source": "the_odds_api",
            "configured": False,
            "status": "not_configured",
            "message_zh": "未配置 JC_EDGE_THE_ODDS_API_KEY。",
        }
    query = urlencode({"apiKey": key})
    request = Request(f"{BASE_URL}/v4/sports/?{query}", headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
            headers = dict(response.headers.items())
    except Exception as exc:  # noqa: BLE001 - return safe status for UI
        return {
            "source": "the_odds_api",
            "configured": True,
            "masked_key": mask_secret(key),
            "status": "error",
            "message_zh": f"The Odds API 验证失败：{str(exc).splitlines()[0][:160]}",
        }
    sports = payload if isinstance(payload, list) else []
    soccer_count = sum(1 for item in sports if isinstance(item, dict) and "soccer" in str(item.get("key", "")))
    return {
        "source": "the_odds_api",
        "configured": True,
        "masked_key": mask_secret(key),
        "status": "ok",
        "host": BASE_URL,
        "sports_count": len(sports),
        "soccer_sports_count": soccer_count,
        "requests_remaining": headers.get("x-requests-remaining") or headers.get("X-Requests-Remaining"),
        "requests_used": headers.get("x-requests-used") or headers.get("X-Requests-Used"),
        "message_zh": "The Odds API key 可用；可用于国际赔率交叉参考，不替代中国竞彩官方赔率。",
    }


def _ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())

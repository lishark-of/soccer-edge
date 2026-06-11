from __future__ import annotations

from src.providers.api_football_client import verify_api_football
from src.providers.the_odds_api_client import verify_the_odds_api


def verify_third_party_source(source: str) -> dict:
    key = source.strip().lower().replace("-", "_")
    if key in {"api_football", "api_sports"}:
        return verify_api_football()
    if key in {"the_odds_api", "odds_api"}:
        return verify_the_odds_api()
    return {
        "source": key or "unknown",
        "status": "unsupported",
        "message_zh": "暂不支持该数据源验证。",
    }

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"


@dataclass(frozen=True)
class DeepSeekConfig:
    enabled: bool
    provider: str
    api_key_present: bool
    base_url: str
    model: str
    timeout_seconds: float
    max_tokens: int


def load_deepseek_config() -> DeepSeekConfig:
    return DeepSeekConfig(
        enabled=_truthy(os.environ.get("FOOTBALL_JC_LLM_ENABLED", "false")),
        provider=os.environ.get("FOOTBALL_JC_LLM_PROVIDER", "deepseek").strip() or "deepseek",
        api_key_present=bool(get_deepseek_api_key()),
        base_url=(os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL).rstrip("/"),
        model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        timeout_seconds=_float_env("DEEPSEEK_TIMEOUT_SECONDS", 20.0),
        max_tokens=_int_env("DEEPSEEK_MAX_TOKENS", 600),
    )


def get_deepseek_api_key() -> str | None:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key or not key.strip():
        return None
    return key.strip()


def llm_status_payload() -> dict:
    config = load_deepseek_config()
    return {
        "provider": config.provider,
        "enabled": config.enabled,
        "api_key_present": config.api_key_present,
        "base_url_configured": bool(config.base_url),
        "model": config.model,
        "external_calls_default": False,
        "status": _status(config),
    }


def _status(config: DeepSeekConfig) -> str:
    if not config.enabled:
        return "disabled"
    if config.provider != "deepseek":
        return "unsupported_provider"
    if not config.api_key_present:
        return "missing_api_key"
    return "ready"


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _float_env(name: str, default: float) -> float:
    try:
        value = float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default

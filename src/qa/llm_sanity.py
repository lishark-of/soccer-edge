from __future__ import annotations

from src.explain.deepseek_config import load_deepseek_config
from src.qa.checks import QaCheckResult


SECRET_MARKERS = ["sk-", "DEEPSEEK_API_KEY=", "Authorization", "Bearer "]


def check_llm_disabled_by_default() -> list[QaCheckResult]:
    config = load_deepseek_config()
    passed = (config.enabled is False) or (
        config.enabled is True and config.provider == "deepseek" and config.api_key_present is True
    )
    return [
        QaCheckResult(
            "llm.disabled_by_default",
            passed,
            message="LLM/DeepSeek explainer is either disabled by default or explicitly enabled with a valid visible configuration",
            details={"enabled": config.enabled, "provider": config.provider, "model": config.model},
        )
    ]


def check_no_api_key_exposure(text: str) -> list[QaCheckResult]:
    found = [marker for marker in SECRET_MARKERS if marker in str(text)]
    return [QaCheckResult("llm.no_api_key_exposure", not found, message="responses do not expose API key material", details={"markers": found})]


def check_deepseek_status_response(status: dict) -> list[QaCheckResult]:
    text = str(status)
    results = check_no_api_key_exposure(text)
    results.append(
        QaCheckResult(
            "llm.status_shape",
            "api_key_present" in status and "enabled" in status and "provider" in status,
            message="DeepSeek status exposes only safe configuration fields",
        )
    )
    return results

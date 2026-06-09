from __future__ import annotations

import os


class LlmExplainerUnavailable(RuntimeError):
    pass


def is_llm_explainer_enabled() -> bool:
    return os.environ.get("LLM_EXPLAINER_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def explain_with_llm(prompt: str, context: dict | None = None) -> str:
    if not is_llm_explainer_enabled():
        raise LlmExplainerUnavailable(
            "LLM explainer is disabled by default. Phase 2-G does not call DeepSeek or any external API."
        )
    raise LlmExplainerUnavailable(
        "LLM explainer integration is a stub in Phase 2-G and performs no external calls."
    )

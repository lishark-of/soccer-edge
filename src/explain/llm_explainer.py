from __future__ import annotations

from src.explain.deepseek_config import load_deepseek_config
from src.explain.deepseek_explainer import explain_with_optional_deepseek


class LlmExplainerUnavailable(RuntimeError):
    pass


def is_llm_explainer_enabled() -> bool:
    return load_deepseek_config().enabled


def explain_with_llm(prompt: str, context: dict | None = None) -> str:
    if not is_llm_explainer_enabled():
        raise LlmExplainerUnavailable(
            "LLM explainer is disabled by default. Phase 2-H does not call DeepSeek unless explicitly enabled."
        )
    payload = {"outcome_label": "解释", "model_prob": None, "fair_prob": None, "edge": None, "ev": None, "risk_level": "unknown", "prompt": prompt}
    result = explain_with_optional_deepseek("candidate", payload, {**(context or {}), "provider": "deepseek"})
    if result.get("provider") != "deepseek":
        raise LlmExplainerUnavailable("LLM explainer fell back to local explanation")
    return str(result.get("text", ""))

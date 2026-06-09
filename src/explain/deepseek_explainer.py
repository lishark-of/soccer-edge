from __future__ import annotations

from src.explain.deepseek_client import DeepSeekClient, DeepSeekClientError
from src.explain.deepseek_config import load_deepseek_config
from src.explain.local_explainer import explain_backtest_metrics, explain_candidate
from src.explain.prompt_builder import build_backtest_explanation_prompt, build_candidate_explanation_prompt, build_calibration_explanation_prompt
from src.explain.safety import enforce_safe_explanation, validate_explanation_safety


def explain_candidate_with_deepseek(candidate: dict, context: dict | None = None) -> dict:
    return explain_with_optional_deepseek("candidate", candidate, context)


def explain_backtest_with_deepseek(report: dict, context: dict | None = None) -> dict:
    return explain_with_optional_deepseek("backtest", report, context)


def explain_with_optional_deepseek(kind: str, payload: dict, context: dict | None = None) -> dict:
    context = dict(context or {})
    requested = context.get("provider", context.get("explain_mode", "auto"))
    fallback = _local_text(kind, payload)
    if requested == "local":
        return _result("local", False, "loaded", fallback, [])
    config = load_deepseek_config()
    if not config.enabled:
        return _result("local", False, "disabled", fallback, ["DeepSeek explainer disabled; used local explanation"])
    if config.provider != "deepseek":
        return _result("local", True, "fallback_local", fallback, ["configured LLM provider is unsupported; used local explanation"])
    if not config.api_key_present:
        return _result("local", True, "missing_api_key", fallback, ["DeepSeek API key missing; used local explanation"])
    try:
        client = context.get("client") or DeepSeekClient(config=config, transport=context.get("transport"))
        messages = _messages(kind, payload, context)
        text = client.explain(messages)
    except DeepSeekClientError as exc:
        return _result("local", True, "error", fallback, [f"DeepSeek explainer failed: {str(exc)[:160]}; used local explanation"])
    issues = validate_explanation_safety(text)
    if issues:
        return _result("local", True, "fallback_local", fallback, ["DeepSeek output failed safety filter; used local explanation"] + issues)
    return _result("deepseek", True, "loaded", enforce_safe_explanation(text, fallback), [])


def _messages(kind: str, payload: dict, context: dict) -> list[dict]:
    if kind == "candidate":
        return build_candidate_explanation_prompt(payload, context)
    if kind == "backtest":
        return build_backtest_explanation_prompt(payload, context)
    if kind == "calibration":
        return build_calibration_explanation_prompt(payload, context)
    return build_candidate_explanation_prompt(payload, context)


def _local_text(kind: str, payload: dict) -> str:
    if kind == "backtest":
        return " ".join(explain_backtest_metrics(payload.get("metrics", payload)))
    if kind == "calibration":
        return "校准分箱用于观察预测概率与实际频率是否匹配。概率模型不保证结果，回测结果不保证未来表现。"
    return explain_candidate(payload)


def _result(provider: str, enabled: bool, status: str, text: str, warnings: list[str]) -> dict:
    return {
        "provider": provider,
        "enabled": enabled,
        "status": status,
        "text": text,
        "warnings": list(warnings),
    }

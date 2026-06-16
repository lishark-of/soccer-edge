from __future__ import annotations

from src.explain.deepseek_client import DeepSeekClient, DeepSeekClientError
from src.explain.deepseek_config import load_deepseek_config
from src.explain.deepseek_runtime import update_runtime_status
from src.explain.local_explainer import explain_backtest_metrics, explain_candidate
from src.explain.prompt_builder import build_backtest_explanation_prompt, build_candidate_explanation_prompt, build_calibration_explanation_prompt, build_combo_research_prompt
from src.explain.safety import enforce_safe_explanation, validate_explanation_safety


def explain_candidate_with_deepseek(candidate: dict, context: dict | None = None) -> dict:
    return explain_with_optional_deepseek("candidate", candidate, context)


def explain_backtest_with_deepseek(report: dict, context: dict | None = None) -> dict:
    return explain_with_optional_deepseek("backtest", report, context)


def explain_with_optional_deepseek(kind: str, payload: dict, context: dict | None = None) -> dict:
    context = dict(context or {})
    requested = str(context.get("provider", context.get("explain_mode", "auto")) or "auto").strip().lower()
    fallback = _local_text(kind, payload)
    if requested == "local":
        return _result(
            "local",
            False,
            "local_only",
            fallback,
            [],
            provider_requested=requested,
            provider_resolved="local",
            ds_status="local_only",
            ds_attempted=False,
            ds_completed=False,
            ds_error_code="",
            token_in=None,
            token_out=None,
            token_total=None,
            fallback_reason="已按本地模式生成摘要，不调用 DeepSeek。",
        )
    config = load_deepseek_config()
    if not config.enabled:
        return _fallback_result(requested, "disabled", fallback, ["DeepSeek explainer disabled; used local explanation"], "DeepSeek 解释层未启用，已回退本地摘要。", enabled=False)
    if config.provider != "deepseek":
        return _fallback_result(requested, "unsupported_provider", fallback, ["configured LLM provider is unsupported; used local explanation"], "当前解释层 provider 不是 DeepSeek，已回退本地摘要。")
    if not config.api_key_present:
        return _fallback_result(requested, "missing_api_key", fallback, ["DeepSeek API key missing; used local explanation"], "未检测到 DeepSeek API Key，已回退本地摘要。")
    try:
        client = context.get("client") or DeepSeekClient(config=config, transport=context.get("transport"))
        messages = _messages(kind, payload, context)
        response = client.complete(
            messages,
            max_tokens_override=context.get("max_tokens_override"),
            timeout_seconds_override=context.get("timeout_seconds_override"),
        )
        text = str(response.get("text") or "")
    except DeepSeekClientError as exc:
        return _fallback_result(
            requested,
            "error",
            fallback,
            [f"DeepSeek explainer failed: {str(exc)[:160]}; used local explanation"],
            exc.user_message_zh,
            ds_attempted=True,
            ds_error_code=exc.code,
        )
    safe_text = enforce_safe_explanation(text, fallback)
    issues = validate_explanation_safety(safe_text)
    if issues:
        return _fallback_result(
            requested,
            "safety_fallback",
            fallback,
            ["DeepSeek output failed safety filter; used local explanation"] + issues,
            "DeepSeek 输出未通过安全过滤，已回退本地摘要。",
            ds_attempted=True,
            ds_error_code="safety_filter",
        )
    return _result(
        "deepseek",
        True,
        "loaded",
        safe_text,
        [],
        provider_requested=requested,
        provider_resolved="deepseek",
        ds_status="loaded",
        ds_attempted=True,
        ds_completed=True,
        ds_error_code="",
        token_in=response.get("token_in"),
        token_out=response.get("token_out"),
        token_total=response.get("token_total"),
        fallback_reason="",
    )


def _messages(kind: str, payload: dict, context: dict) -> list[dict]:
    if kind == "candidate":
        return build_candidate_explanation_prompt(payload, context)
    if kind == "backtest":
        return build_backtest_explanation_prompt(payload, context)
    if kind == "calibration":
        return build_calibration_explanation_prompt(payload, context)
    if kind == "combo_research":
        return build_combo_research_prompt(payload, context)
    return build_candidate_explanation_prompt(payload, context)


def _local_text(kind: str, payload: dict) -> str:
    if kind == "backtest":
        return " ".join(explain_backtest_metrics(payload.get("metrics", payload)))
    if kind == "calibration":
        return "校准分箱用于观察预测概率与实际频率是否匹配。概率模型不保证结果，回测结果不保证未来表现。"
    if kind == "combo_research":
        return "组合研究摘要：先看单关质量，再看 2串1 是否通过可信度、赔率覆盖、相关性和命中率纪律。若未通过，不应强行组合。"
    return explain_candidate(payload)


def _fallback_result(
    requested: str,
    status: str,
    text: str,
    warnings: list[str],
    fallback_reason: str,
    *,
    enabled: bool = True,
    ds_attempted: bool = False,
    ds_error_code: str = "",
) -> dict:
    return _result(
        "local",
        enabled,
        status,
        text,
        warnings,
        provider_requested=requested,
        provider_resolved="local",
        ds_status=status,
        ds_attempted=ds_attempted,
        ds_completed=False,
        ds_error_code=ds_error_code,
        token_in=None,
        token_out=None,
        token_total=None,
        fallback_reason=fallback_reason,
    )


def _result(
    provider: str,
    enabled: bool,
    status: str,
    text: str,
    warnings: list[str],
    *,
    provider_requested: str,
    provider_resolved: str,
    ds_status: str,
    ds_attempted: bool,
    ds_completed: bool,
    ds_error_code: str,
    token_in,
    token_out,
    token_total,
    fallback_reason: str,
) -> dict:
    ds_status_zh = _runtime_status_zh(ds_status)
    status_zh = _runtime_status_zh(status)
    display_status_zh = _display_status_zh(provider_resolved, ds_status, ds_completed, fallback_reason)
    update_runtime_status(
        provider_requested=provider_requested,
        provider_target="deepseek" if provider_requested in {"auto", "deepseek"} else provider_resolved,
        provider_resolved=provider_resolved,
        ds_status=ds_status,
        ds_status_zh=ds_status_zh,
        ds_attempted=ds_attempted,
        ds_completed=ds_completed,
        ds_error_code=ds_error_code,
        fallback_reason=fallback_reason,
        token_in=token_in,
        token_out=token_out,
        token_total=token_total,
    )
    return {
        "provider": provider,
        "enabled": enabled,
        "status": status,
        "status_zh": status_zh,
        "text": text,
        "warnings": list(warnings),
        "provider_requested": provider_requested,
        "provider_resolved": provider_resolved,
        "ds_status": ds_status,
        "ds_status_zh": ds_status_zh,
        "ds_attempted": bool(ds_attempted),
        "ds_completed": bool(ds_completed),
        "ds_error_code": ds_error_code,
        "token_in": token_in,
        "token_out": token_out,
        "token_total": token_total,
        "fallback_reason": fallback_reason,
        "display_status_zh": display_status_zh,
    }


def _runtime_status_zh(status: str) -> str:
    return {
        "loaded": "DS Pro 已参与",
        "ready": "DS Pro 可用",
        "local_only": "仅本地摘要",
        "not_requested": "未请求 AI 研究",
        "disabled": "DS 未启用",
        "unsupported_provider": "Provider 不受支持",
        "missing_api_key": "缺少 API Key",
        "error": "DS 请求失败",
        "safety_fallback": "安全过滤后回退本地摘要",
    }.get(str(status or ""), "状态未知")


def _display_status_zh(provider_resolved: str, ds_status: str, ds_completed: bool, fallback_reason: str) -> str:
    if provider_resolved == "deepseek" and ds_completed:
        return "DS Pro 已参与本次研究。"
    if fallback_reason:
        return fallback_reason
    return _runtime_status_zh(ds_status)

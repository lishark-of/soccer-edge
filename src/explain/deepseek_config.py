from __future__ import annotations

import os
from dataclasses import dataclass

from src.config.local_env import load_local_env
from src.explain.deepseek_runtime import get_runtime_status


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_MAX_INPUT_TOKENS = 24000
DEFAULT_MAX_OUTPUT_TOKENS = 4000


@dataclass(frozen=True)
class DeepSeekConfig:
    enabled: bool
    provider: str
    api_key_present: bool
    base_url: str
    model: str
    timeout_seconds: float
    max_tokens: int
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS


def load_deepseek_config() -> DeepSeekConfig:
    load_local_env()
    return DeepSeekConfig(
        enabled=_truthy(_first_env("JC_EDGE_DEEPSEEK_ENABLED", "FOOTBALL_JC_LLM_ENABLED", default="false")),
        provider=(_first_env("JC_EDGE_LLM_PROVIDER", "FOOTBALL_JC_LLM_PROVIDER", default="deepseek").strip() or "deepseek"),
        api_key_present=bool(get_deepseek_api_key()),
        base_url=(_first_env("JC_EDGE_DEEPSEEK_BASE_URL", "DEEPSEEK_BASE_URL", default=DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL).rstrip("/"),
        model=_first_env("JC_EDGE_DEEPSEEK_MODEL", "DEEPSEEK_MODEL", default=DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        timeout_seconds=_float_env(("JC_EDGE_DEEPSEEK_TIMEOUT_SECONDS", "DEEPSEEK_TIMEOUT_SECONDS"), 20.0),
        max_tokens=_int_env(("JC_EDGE_DEEPSEEK_MAX_OUTPUT_TOKENS", "DEEPSEEK_MAX_TOKENS"), DEFAULT_MAX_OUTPUT_TOKENS),
        max_input_tokens=_int_env(("JC_EDGE_DEEPSEEK_MAX_INPUT_TOKENS",), DEFAULT_MAX_INPUT_TOKENS),
    )


def get_deepseek_api_key() -> str | None:
    load_local_env()
    key = _first_env("JC_EDGE_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY", default="")
    if not key or not key.strip():
        return None
    return key.strip()


def llm_status_payload() -> dict:
    config = load_deepseek_config()
    status = _status(config)
    ready_for_auto = status == "ready"
    runtime = get_runtime_status()
    status_detail_zh = _status_detail_zh(status, runtime)
    fallback_reason = _effective_fallback_reason_zh(status, runtime)
    ai_research_status = _ai_research_status(status, runtime)
    return {
        "provider": config.provider,
        "enabled": config.enabled,
        "api_key_present": config.api_key_present,
        "base_url_configured": bool(config.base_url),
        "model": config.model,
        "max_input_tokens": config.max_input_tokens,
        "max_output_tokens": config.max_tokens,
        "external_calls_default": False,
        "status": status,
        "status_zh": _status_zh(status),
        "status_detail_zh": status_detail_zh,
        "config_status_zh": _config_status_zh(status, config),
        "runtime_notice_zh": _runtime_notice_zh(runtime),
        "next_step_zh": _next_step_zh(status, runtime),
        "ready_for_auto": ready_for_auto,
        "provider_resolved": "deepseek" if ready_for_auto else "local",
        "fallback_reason": fallback_reason,
        "ai_research_status": ai_research_status,
        "runtime_status": runtime.get("ds_status", "not_requested"),
        "runtime_status_zh": runtime.get("ds_status_zh", "未请求 AI 研究"),
        "ds_attempted": runtime.get("ds_attempted", False),
        "ds_completed": runtime.get("ds_completed", False),
        "ds_error_code": runtime.get("ds_error_code", ""),
        "last_attempt_at": runtime.get("last_attempt_at", ""),
        "last_provider_requested": runtime.get("provider_requested", ""),
        "last_error_code": runtime.get("ds_error_code", ""),
        "last_error_label_zh": runtime.get("error_label_zh", ""),
        "last_error_message_zh": runtime.get("fallback_reason", ""),
        "last_provider_target": runtime.get("provider_target", ""),
        "last_provider_resolved": runtime.get("provider_resolved", ""),
        "token_in": runtime.get("token_in"),
        "token_out": runtime.get("token_out"),
        "token_total": runtime.get("token_total"),
        "last_token_in": runtime.get("token_in"),
        "last_token_out": runtime.get("token_out"),
        "last_token_total": runtime.get("token_total"),
        "decision_chain": [
            {
                "step": "enabled",
                "passed": config.enabled,
                "label_zh": "DS 开关",
                "detail_zh": "已启用" if config.enabled else "未启用",
            },
            {
                "step": "provider",
                "passed": config.provider == "deepseek",
                "label_zh": "Provider",
                "detail_zh": "当前为 DeepSeek" if config.provider == "deepseek" else f"当前为 {config.provider}",
            },
            {
                "step": "api_key",
                "passed": config.api_key_present,
                "label_zh": "API Key",
                "detail_zh": "已检测到 Key" if config.api_key_present else "未检测到 Key",
            },
        ],
        "safe_usage": "optional_explainer_only",
        "safe_usage_zh": "只允许用于解释层、复盘和研究摘要，不改写概率和组合筛选。",
    }


def _status(config: DeepSeekConfig) -> str:
    if not config.enabled:
        return "disabled"
    if config.provider != "deepseek":
        return "unsupported_provider"
    if not config.api_key_present:
        return "missing_api_key"
    return "ready"


def _status_zh(status: str) -> str:
    return {
        "disabled": "未启用",
        "unsupported_provider": "Provider 不受支持",
        "missing_api_key": "缺少 API Key",
        "ready": "可自动研究",
    }.get(status, "状态未知")


def _fallback_reason_zh(status: str) -> str:
    return {
        "disabled": "DeepSeek 开关未启用，auto 会回退本地摘要。",
        "unsupported_provider": "当前解释层 provider 不是 DeepSeek，auto 会回退本地摘要。",
        "missing_api_key": "未检测到 DeepSeek API Key，auto 会回退本地摘要。",
        "ready": "",
    }.get(status, "DeepSeek 当前未就绪，auto 会回退本地摘要。")


def _effective_fallback_reason_zh(status: str, runtime: dict) -> str:
    runtime_reason = str(runtime.get("fallback_reason") or "").strip()
    if runtime_reason and (runtime.get("ds_attempted") or runtime.get("ds_status") == "cached"):
        return runtime_reason
    return "" if status == "ready" else _fallback_reason_zh(status)


def _status_detail_zh(status: str, runtime: dict) -> str:
    if status == "disabled":
        return "DeepSeek 开关未启用。"
    if status == "unsupported_provider":
        return "当前 provider 不是 DeepSeek。"
    if status == "missing_api_key":
        return "未检测到 DeepSeek API Key。"
    if runtime.get("ds_status") == "cached":
        if runtime.get("fallback_reason") or runtime.get("ds_error_code"):
            return "本轮 DS 实时请求失败，当前已复用最近一次成功的 DS 研究结果。"
        token_total = runtime.get("token_total")
        if token_total is not None:
            return f"当前正在复用最近一次成功的 DS 研究结果，累计 token {token_total}。"
        return "当前正在复用最近一次成功的 DS 研究结果，未重复调用 DS Pro。"
    if runtime.get("ds_completed"):
        token_total = runtime.get("token_total")
        if token_total is not None:
            return f"最近一次 DS Pro 调用成功，累计 token {token_total}。"
        return "最近一次 DS Pro 调用成功。"
    error_label = runtime.get("error_label_zh") or ""
    fallback = runtime.get("fallback_reason") or ""
    if error_label and fallback:
        return f"{error_label}：{fallback}"
    if fallback:
        return str(fallback)
    return "DeepSeek 已就绪，等待本次自动研究触发。"


def _config_status_zh(status: str, config: DeepSeekConfig) -> str:
    if status == "disabled":
        return "DeepSeek 开关未启用。"
    if status == "unsupported_provider":
        return f"当前 provider 为 {config.provider}，不是 DeepSeek。"
    if status == "missing_api_key":
        return "尚未检测到 DeepSeek API Key。"
    return f"DeepSeek 已就绪，当前模型 {config.model}。"


def _runtime_notice_zh(runtime: dict) -> str:
    if runtime.get("ds_status") == "cached":
        if runtime.get("fallback_reason") or runtime.get("ds_error_code"):
            return "本轮 DS 请求失败，已复用最近一次成功的 DS 研究结果。"
        return "已复用最近一次成功的 DS 研究结果，本轮未重复调用 DS Pro。"
    if runtime.get("ds_completed"):
        return "本轮 DS 已成功返回，可直接查看 AI 研究摘要与 token 消耗。"
    if runtime.get("ds_attempted"):
        label = runtime.get("error_label_zh") or runtime.get("ds_error_code") or "异常"
        return f"本轮 DS 已自动尝试，但未成功返回；当前原因：{label}。"
    return "本轮还没有自动研究记录。"


def _next_step_zh(status: str, runtime: dict) -> str:
    if status == "disabled":
        return "先在本地 Key 安全配置中启用 DeepSeek，再刷新今日观察。"
    if status == "unsupported_provider":
        return "把解释层 provider 切回 DeepSeek，再刷新今日观察。"
    if status == "missing_api_key":
        return "先补 DeepSeek API Key，再刷新今日观察，auto 会自动研究。"
    if runtime.get("ds_status") == "cached":
        if not (runtime.get("fallback_reason") or runtime.get("ds_error_code")):
            return "当前可直接查看缓存研究；如需获取最新解释，可手动刷新今日观察或赛前优化。"
        return "当前可先查看缓存研究；如需最新解释，可稍后刷新，若持续失败请检查 Key、额度或网络。"
    if runtime.get("ds_completed"):
        return "本轮已成功返回，可直接对照 AI 研究摘要、被拒原因和 token 消耗。"
    if runtime.get("ds_attempted"):
        return "已自动尝试；如仍回退，请查看最近一次异常并再次刷新今日观察。"
    return "刷新今日观察或赛前优化后，会自动触发 DS 研究。"


def _ai_research_status(status: str, runtime: dict) -> dict:
    runtime_status = str(runtime.get("ds_status") or "not_requested")
    error_code = str(runtime.get("ds_error_code") or "")
    error_label = str(runtime.get("error_label_zh") or "")
    if runtime_status == "loaded" and runtime.get("ds_completed"):
        return {
            "status": "done",
            "label_zh": "DS Pro 已参与",
            "error_code": "",
            "error_label_zh": "",
            "summary_zh": _runtime_notice_zh(runtime),
        }
    if runtime_status == "cached" and runtime.get("ds_completed"):
        return {
            "status": "cached",
            "label_zh": "已复用 DS 研究",
            "error_code": error_code,
            "error_label_zh": error_label,
            "summary_zh": _runtime_notice_zh(runtime),
        }
    if runtime.get("ds_attempted"):
        return {
            "status": "fallback",
            "label_zh": _fallback_label_zh(error_code, error_label),
            "error_code": error_code,
            "error_label_zh": error_label,
            "summary_zh": _effective_fallback_reason_zh(status, runtime) or _runtime_notice_zh(runtime),
        }
    if status == "ready":
        return {
            "status": "ready",
            "label_zh": "等待自动研究",
            "error_code": "",
            "error_label_zh": "",
            "summary_zh": _next_step_zh(status, runtime),
        }
    return {
        "status": "not_configured",
        "label_zh": _config_label_zh(status),
        "error_code": status,
        "error_label_zh": _config_label_zh(status),
        "summary_zh": _config_status_zh(status, load_deepseek_config()),
    }


def _fallback_label_zh(error_code: str, error_label: str) -> str:
    return {
        "invalid_api_key": "Key 无效",
        "insufficient_balance": "额度不足",
        "access_denied": "权限不足",
        "rate_limited": "请求过频",
        "request_timeout": "请求超时",
        "network_error": "请求失败",
        "output_budget_exhausted": "输出上限不足",
        "reasoning_only_response": "未返回最终正文",
        "provider_unavailable": "服务暂不可用",
        "endpoint_not_found": "接口不可用",
        "invalid_json": "返回格式异常",
        "unsupported_payload": "请求内容不受支持",
        "empty_content": "返回为空",
        "safety_filter": "安全过滤回退",
    }.get(error_code, error_label or "已回退本地摘要")


def _config_label_zh(status: str) -> str:
    return {
        "disabled": "未启用",
        "unsupported_provider": "Provider 不受支持",
        "missing_api_key": "缺少 API Key",
        "ready": "等待自动研究",
    }.get(status, "待配置")


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value is not None and str(value).strip():
            return str(value)
    return default


def _float_env(names: str | tuple[str, ...], default: float) -> float:
    if isinstance(names, str):
        raw = os.environ.get(names, default)
    else:
        raw = _first_env(*names, default=str(default))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _int_env(names: str | tuple[str, ...], default: int) -> int:
    if isinstance(names, str):
        raw = os.environ.get(names, default)
    else:
        raw = _first_env(*names, default=str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default

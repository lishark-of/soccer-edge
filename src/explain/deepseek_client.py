from __future__ import annotations

import json
import socket
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.explain.deepseek_config import DeepSeekConfig, get_deepseek_api_key, load_deepseek_config


class DeepSeekClientError(RuntimeError):
    def __init__(self, message: str, code: str = "request_failed", user_message_zh: str | None = None):
        super().__init__(message)
        self.code = code
        self.user_message_zh = user_message_zh or _user_message(code, message)


Transport = Callable[[str, dict[str, str], dict[str, Any], float], dict | str | bytes]


class DeepSeekClient:
    def __init__(self, config: DeepSeekConfig | None = None, transport: Transport | None = None):
        self.config = config or load_deepseek_config()
        self.transport = transport

    def explain(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        *,
        max_tokens_override: int | None = None,
        timeout_seconds_override: float | None = None,
    ) -> str:
        return str(
            self.complete(
                messages,
                temperature=temperature,
                max_tokens_override=max_tokens_override,
                timeout_seconds_override=timeout_seconds_override,
            ).get("text")
            or ""
        ).strip()

    def complete(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        *,
        max_tokens_override: int | None = None,
        timeout_seconds_override: float | None = None,
    ) -> dict:
        if not self.config.enabled:
            raise DeepSeekClientError("DeepSeek explainer is disabled", code="disabled")
        if self.config.provider != "deepseek":
            raise DeepSeekClientError("configured LLM provider is not supported", code="unsupported_provider")
        api_key = get_deepseek_api_key()
        if not api_key:
            raise DeepSeekClientError("DeepSeek API key is missing", code="missing_api_key")
        max_tokens = _positive_int_or_default(max_tokens_override, self.config.max_tokens)
        timeout_seconds = _positive_float_or_default(timeout_seconds_override, self.config.timeout_seconds)
        body = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        }
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        try:
            raw = self.transport(url, headers, body, timeout_seconds) if self.transport else _urllib_transport(url, headers, body, timeout_seconds)
            payload = _decode_payload(raw)
            error_payload = payload.get("error") or {}
            if error_payload:
                error_message = str(error_payload.get("message") or error_payload.get("code") or "DeepSeek API returned an error")
                raise DeepSeekClientError(error_message, code=_api_error_code(error_payload))
            choice = payload.get("choices", [{}])[0]
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            content = message.get("content")
            reasoning_content = message.get("reasoning_content")
            finish_reason = choice.get("finish_reason") if isinstance(choice, dict) else None
        except (TimeoutError, socket.timeout) as exc:
            raise DeepSeekClientError(f"DeepSeek request timed out: {_safe_error(exc)}", code="request_timeout") from exc
        except DeepSeekClientError:
            raise
        except Exception as exc:
            message = _safe_error(exc).lower()
            if "timed out" in message or "timeout" in message:
                raise DeepSeekClientError(f"DeepSeek request timed out: {_safe_error(exc)}", code="request_timeout") from exc
            raise DeepSeekClientError(f"DeepSeek response handling failed: {_safe_error(exc)}") from exc
        if not isinstance(content, str) or not content.strip():
            if isinstance(reasoning_content, str) and reasoning_content.strip():
                if str(finish_reason or "").lower() == "length":
                    raise DeepSeekClientError(
                        "DeepSeek reasoning consumed the output budget before final content was returned",
                        code="output_budget_exhausted",
                    )
                raise DeepSeekClientError(
                    "DeepSeek response only returned reasoning_content without final content",
                    code="reasoning_only_response",
                )
            raise DeepSeekClientError("DeepSeek response did not include explanation content", code="empty_content")
        prompt_tokens, completion_tokens, total_tokens = _extract_usage(payload)
        return {
            "text": content.strip(),
            "model": str(payload.get("model") or self.config.model),
            "token_in": prompt_tokens,
            "token_out": completion_tokens,
            "token_total": total_tokens,
            "response_id": payload.get("id"),
        }


def _urllib_transport(url: str, headers: dict[str, str], body: dict[str, Any], timeout: float) -> bytes:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except (TimeoutError, socket.timeout) as exc:
        raise DeepSeekClientError(f"DeepSeek request timed out: {_safe_error(exc)}", code="request_timeout") from exc
    except HTTPError as exc:
        raise DeepSeekClientError(f"DeepSeek HTTP error: {exc.code}", code=_http_error_code(exc.code)) from exc
    except URLError as exc:
        if "timed out" in _safe_error(exc).lower():
            raise DeepSeekClientError(f"DeepSeek request timed out: {_safe_error(exc)}", code="request_timeout") from exc
        raise DeepSeekClientError(f"DeepSeek network error: {_safe_error(exc)}", code="network_error") from exc


def _decode_payload(raw: dict | str | bytes) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DeepSeekClientError("DeepSeek response was not valid JSON", code="invalid_json") from exc
    raise DeepSeekClientError("DeepSeek transport returned unsupported payload type", code="unsupported_payload")


def _extract_usage(payload: dict) -> tuple[int | None, int | None, int | None]:
    usage = payload.get("usage") or {}
    prompt_tokens = _int_or_none(usage.get("prompt_tokens"))
    completion_tokens = _int_or_none(usage.get("completion_tokens"))
    total_tokens = _int_or_none(usage.get("total_tokens"))
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    return prompt_tokens, completion_tokens, total_tokens


def _int_or_none(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _positive_int_or_default(value, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _positive_float_or_default(value, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _http_error_code(status_code: int) -> str:
    if status_code == 401:
        return "invalid_api_key"
    if status_code == 402:
        return "insufficient_balance"
    if status_code == 403:
        return "access_denied"
    if status_code == 404:
        return "endpoint_not_found"
    if status_code == 408:
        return "request_timeout"
    if status_code == 429:
        return "rate_limited"
    if status_code >= 500:
        return "provider_unavailable"
    return f"http_{status_code}"


def _api_error_code(error_payload: dict) -> str:
    code = str(error_payload.get("code") or "").strip().lower()
    if code:
        return code.replace(" ", "_")
    return "api_error"


def _user_message(code: str, fallback: str) -> str:
    mapping = {
        "disabled": "DeepSeek 解释层未启用，已改用本地摘要。",
        "unsupported_provider": "当前解释层 provider 不是 DeepSeek，已改用本地摘要。",
        "missing_api_key": "未检测到 DeepSeek API Key，已改用本地摘要。",
        "invalid_api_key": "DeepSeek API Key 无效或已失效，已改用本地摘要。",
        "insufficient_balance": "DeepSeek 额度不足，已改用本地摘要。",
        "access_denied": "DeepSeek 当前请求被拒绝，已改用本地摘要。",
        "endpoint_not_found": "DeepSeek 接口地址不可用，已改用本地摘要。",
        "request_timeout": "DeepSeek 请求超时，已改用本地摘要。",
        "rate_limited": "DeepSeek 请求过于频繁，已改用本地摘要。",
        "provider_unavailable": "DeepSeek 服务暂时不可用，已改用本地摘要。",
        "network_error": "DeepSeek 网络连接失败，已改用本地摘要。",
        "output_budget_exhausted": "DeepSeek 已开始推理，但输出上限不足，已自动回退或重试本地摘要。",
        "reasoning_only_response": "DeepSeek 只返回了推理草稿，未返回最终正文，已改用本地摘要。",
        "invalid_json": "DeepSeek 返回内容不可解析，已改用本地摘要。",
        "unsupported_payload": "DeepSeek 返回格式不受支持，已改用本地摘要。",
        "empty_content": "DeepSeek 未返回有效解释内容，已改用本地摘要。",
        "api_error": "DeepSeek 返回了错误响应，已改用本地摘要。",
        "request_failed": "DeepSeek 调用失败，已改用本地摘要。",
    }
    return mapping.get(code, f"DeepSeek 调用失败，已改用本地摘要。原始原因：{fallback[:120]}")


def _safe_error(exc: Exception) -> str:
    return str(exc).replace("\n", " ")[:180] or exc.__class__.__name__

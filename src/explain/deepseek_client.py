from __future__ import annotations

import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.explain.deepseek_config import DeepSeekConfig, get_deepseek_api_key, load_deepseek_config


class DeepSeekClientError(RuntimeError):
    pass


Transport = Callable[[str, dict[str, str], dict[str, Any], float], dict | str | bytes]


class DeepSeekClient:
    def __init__(self, config: DeepSeekConfig | None = None, transport: Transport | None = None):
        self.config = config or load_deepseek_config()
        self.transport = transport

    def explain(self, messages: list[dict], temperature: float = 0.2) -> str:
        if not self.config.enabled:
            raise DeepSeekClientError("DeepSeek explainer is disabled")
        if self.config.provider != "deepseek":
            raise DeepSeekClientError("configured LLM provider is not supported")
        api_key = get_deepseek_api_key()
        if not api_key:
            raise DeepSeekClientError("DeepSeek API key is missing")
        body = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        }
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        try:
            raw = self.transport(url, headers, body, self.config.timeout_seconds) if self.transport else _urllib_transport(url, headers, body, self.config.timeout_seconds)
            payload = _decode_payload(raw)
            content = payload.get("choices", [{}])[0].get("message", {}).get("content")
        except DeepSeekClientError:
            raise
        except Exception as exc:
            raise DeepSeekClientError(f"DeepSeek response handling failed: {_safe_error(exc)}") from exc
        if not isinstance(content, str) or not content.strip():
            raise DeepSeekClientError("DeepSeek response did not include explanation content")
        return content.strip()


def _urllib_transport(url: str, headers: dict[str, str], body: dict[str, Any], timeout: float) -> bytes:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as exc:
        raise DeepSeekClientError(f"DeepSeek HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise DeepSeekClientError(f"DeepSeek network error: {_safe_error(exc)}") from exc


def _decode_payload(raw: dict | str | bytes) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DeepSeekClientError("DeepSeek response was not valid JSON") from exc
    raise DeepSeekClientError("DeepSeek transport returned unsupported payload type")


def _safe_error(exc: Exception) -> str:
    return str(exc).replace("\n", " ")[:180] or exc.__class__.__name__

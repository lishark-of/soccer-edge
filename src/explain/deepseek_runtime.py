from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from threading import Lock


_LOCK = Lock()
_STATE = {
    "last_attempt_at": "",
    "provider_requested": "",
    "provider_target": "",
    "provider_resolved": "",
    "ds_status": "not_requested",
    "ds_status_zh": "未请求 AI 研究",
    "ds_attempted": False,
    "ds_completed": False,
    "ds_error_code": "",
    "error_label_zh": "",
    "fallback_reason": "",
    "token_in": None,
    "token_out": None,
    "token_total": None,
}


def update_runtime_status(
    *,
    provider_requested: str,
    provider_target: str,
    provider_resolved: str,
    ds_status: str,
    ds_status_zh: str,
    ds_attempted: bool,
    ds_completed: bool,
    ds_error_code: str = "",
    fallback_reason: str = "",
    token_in=None,
    token_out=None,
    token_total=None,
) -> None:
    with _LOCK:
        _STATE.update(
            {
                "last_attempt_at": datetime.now().isoformat(timespec="seconds"),
                "provider_requested": str(provider_requested or ""),
                "provider_target": str(provider_target or ""),
                "provider_resolved": str(provider_resolved or ""),
                "ds_status": str(ds_status or "unknown"),
                "ds_status_zh": str(ds_status_zh or "状态未知"),
                "ds_attempted": bool(ds_attempted),
                "ds_completed": bool(ds_completed),
                "ds_error_code": str(ds_error_code or ""),
                "error_label_zh": _error_label_zh(ds_error_code),
                "fallback_reason": str(fallback_reason or ""),
                "token_in": _as_int_or_none(token_in),
                "token_out": _as_int_or_none(token_out),
                "token_total": _as_int_or_none(token_total),
            }
        )
        _persist_state(_STATE)


def get_runtime_status() -> dict:
    with _LOCK:
        persisted = _load_persisted_state()
        if persisted:
            return dict({**_STATE, **persisted})
        return dict(_STATE)


def reset_runtime_status(*, delete_persisted: bool = True) -> None:
    with _LOCK:
        _STATE.update(
            {
                "last_attempt_at": "",
                "provider_requested": "",
                "provider_target": "",
                "provider_resolved": "",
                "ds_status": "not_requested",
                "ds_status_zh": "未请求 AI 研究",
                "ds_attempted": False,
                "ds_completed": False,
                "ds_error_code": "",
                "error_label_zh": "",
                "fallback_reason": "",
                "token_in": None,
                "token_out": None,
                "token_total": None,
            }
        )
        if delete_persisted:
            _delete_persisted_state()


def _as_int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _error_label_zh(code: str) -> str:
    return {
        "invalid_api_key": "Key 无效",
        "insufficient_balance": "额度不足",
        "access_denied": "权限不足",
        "rate_limited": "请求过频",
        "request_timeout": "请求超时",
        "network_error": "请求失败",
        "provider_unavailable": "服务不可用",
        "endpoint_not_found": "接口不可用",
        "invalid_json": "返回格式异常",
        "unsupported_payload": "请求内容不受支持",
        "empty_content": "返回为空",
        "safety_filter": "安全过滤回退",
    }.get(str(code or ""), "")


def _status_path() -> Path:
    raw = str(os.environ.get("JC_EDGE_RUNTIME_STATUS_PATH") or "").strip()
    if raw:
        return Path(raw)
    return Path(tempfile.gettempdir()) / "jc_edge_ds_runtime_status.json"


def _persist_state(state: dict) -> None:
    path = _status_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except OSError:
        return


def _load_persisted_state() -> dict:
    path = _status_path()
    try:
        if not path.exists():
            return {}
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        "last_attempt_at": str(raw.get("last_attempt_at") or ""),
        "provider_requested": str(raw.get("provider_requested") or ""),
        "provider_target": str(raw.get("provider_target") or ""),
        "provider_resolved": str(raw.get("provider_resolved") or ""),
        "ds_status": str(raw.get("ds_status") or "not_requested"),
        "ds_status_zh": str(raw.get("ds_status_zh") or "未请求 AI 研究"),
        "ds_attempted": bool(raw.get("ds_attempted")),
        "ds_completed": bool(raw.get("ds_completed")),
        "ds_error_code": str(raw.get("ds_error_code") or ""),
        "error_label_zh": str(raw.get("error_label_zh") or ""),
        "fallback_reason": str(raw.get("fallback_reason") or ""),
        "token_in": _as_int_or_none(raw.get("token_in")),
        "token_out": _as_int_or_none(raw.get("token_out")),
        "token_total": _as_int_or_none(raw.get("token_total")),
    }


def _delete_persisted_state() -> None:
    path = _status_path()
    try:
        if path.exists():
            path.unlink()
    except OSError:
        return

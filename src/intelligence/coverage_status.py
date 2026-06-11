from __future__ import annotations

STATUS_ZH = {
    "confirmed": "已确认",
    "checked_empty": "已检查但未返回",
    "fallback_estimated": "兜底估算",
    "not_connected": "未接入",
    "user_supplied": "用户补充",
    "unknown": "未知",
    "error": "查询失败",
}

CONFIDENCE_ZH = {
    "high": "高",
    "medium": "中",
    "medium_low": "中低",
    "low": "低",
    "unknown": "未知",
}


def normalize_coverage_status(status: str | None) -> str:
    value = str(status or "unknown")
    if value in STATUS_ZH:
        return value
    if value in {"connected", "matched", "ok", "available"}:
        return "confirmed"
    if value in {"covered_empty", "not_available", "not_found", "basic_only", "empty"}:
        return "checked_empty"
    if value in {"timeout"}:
        return "error"
    if value in {"not_configured", "unmatched", "missing"}:
        return "not_connected"
    if value in {"", "None"}:
        return "unknown"
    return value if value in STATUS_ZH else "unknown"


def status_zh(status: str | None) -> str:
    return STATUS_ZH.get(normalize_coverage_status(status), str(status or "未知"))


def confidence_for_status(status: str | None, *, fallback_source: str | None = None) -> str:
    normalized = normalize_coverage_status(status)
    if normalized == "confirmed":
        return "high"
    if normalized == "user_supplied":
        return "medium"
    if normalized == "checked_empty":
        return "medium_low"
    if normalized == "fallback_estimated":
        return "low" if fallback_source == "team_country_fallback" else "medium_low"
    if normalized in {"not_connected", "unknown"}:
        return "unknown"
    return "low"


def confidence_zh(status: str | None, *, fallback_source: str | None = None) -> str:
    return CONFIDENCE_ZH[confidence_for_status(status, fallback_source=fallback_source)]


def is_confirmed(status: str | None) -> bool:
    return normalize_coverage_status(status) in {"confirmed", "user_supplied"}


def is_partial(status: str | None) -> bool:
    return normalize_coverage_status(status) in {"checked_empty", "fallback_estimated"}


def is_missing(status: str | None) -> bool:
    return normalize_coverage_status(status) in {"not_connected", "unknown", "error"}

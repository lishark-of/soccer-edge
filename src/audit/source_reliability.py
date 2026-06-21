from __future__ import annotations


def build_source_reliability(preview: dict, status: dict | None = None) -> dict:
    """Audit match-data reliability for user-facing and professional-score views."""
    preview = preview or {}
    status = status or preview.get("data_source_status") or {}
    existing = preview.get("source_health")
    if isinstance(existing, dict) and existing.get("reliability_score") is not None:
        return _normalize_existing(existing, preview, status)

    attempts = preview.get("attempts", []) or []
    scan_window = preview.get("scan_window") if isinstance(preview.get("scan_window"), dict) else {}
    matches_count = _int(preview.get("matches_count"))
    provider_used = str(preview.get("provider_used") or preview.get("provider") or "unknown")
    fallback_used = bool(preview.get("fallback_used")) or provider_used in {"mock", "fallback", "fixture"}
    warnings = list(preview.get("warnings", []) or preview.get("provider_warnings", []) or [])
    scanned_dates = [item.get("date") for item in attempts if isinstance(item, dict) and item.get("date")]
    successful_attempts = [item for item in attempts if isinstance(item, dict) and _int(item.get("matches_count")) > 0]

    attempt_count = len(attempts)
    sporttery_attempts = 0
    fallback_attempts = 0
    empty_attempts = 0
    warning_attempts = 0
    for item in attempts:
        if not isinstance(item, dict):
            continue
        item_provider = str(item.get("provider_used") or item.get("provider") or "unknown")
        item_status = str(item.get("status") or "")
        item_warnings = item.get("warnings") or item.get("provider_warnings") or []
        if item_provider == "sporttery":
            sporttery_attempts += 1
        if item_provider in {"mock", "fallback", "fixture"} or item_status in {"fallback", "mock", "fallback_empty"} or bool(item.get("fallback_used")):
            fallback_attempts += 1
        if _int(item.get("matches_count")) == 0:
            empty_attempts += 1
        if item_warnings:
            warning_attempts += 1

    if attempt_count == 0:
        if provider_used == "sporttery" and matches_count > 0 and not warnings:
            sporttery_attempts = 1
            attempt_count = 1
        elif fallback_used:
            fallback_attempts = 1
            attempt_count = 1
        elif matches_count == 0:
            empty_attempts = 1
            attempt_count = 1

    scan_complete = bool(scan_window.get("complete")) or attempt_count == 1
    all_attempts_stable = (
        attempt_count > 0
        and scan_complete
        and fallback_attempts == 0
        and warning_attempts == 0
        and sporttery_attempts == attempt_count
        and provider_used == "sporttery"
        and matches_count > 0
    )
    if all_attempts_stable:
        health = "stable"
        message = "Sporttery 当前可读取，扫描窗口未发现回退或异常提醒。"
    elif provider_used == "sporttery" and matches_count > 0:
        health = "degraded"
        message = "Sporttery 当前可读取，但扫描窗口或数据提醒显示仍需复核稳定性。"
    elif fallback_used:
        health = "fallback"
        message = "当前包含 mock/fallback/fixture 数据，只适合流程演示或纸面学习。"
    elif matches_count == 0:
        health = "empty"
        message = "扫描范围内暂未读取到可售比赛。"
    else:
        health = "unknown"
        message = "数据源状态不够清晰。"

    score_payload = _score_source(
        health=health,
        attempt_count=attempt_count,
        sporttery_attempts=sporttery_attempts,
        fallback_attempts=fallback_attempts,
        empty_attempts=empty_attempts,
        warning_attempts=warning_attempts + (1 if warnings else 0),
        scan_complete=scan_complete,
    )
    degraded_reason = _degraded_reason(fallback_attempts, empty_attempts, warning_attempts, warnings)
    return {
        "version": "source_reliability_v1",
        "health": health,
        "provider_used": provider_used,
        "selected_date": preview.get("selected_date") or preview.get("date"),
        "matches_count": matches_count,
        "scanned_dates": scanned_dates,
        "scan_window": scan_window,
        "successful_attempts": len(successful_attempts) or (1 if matches_count > 0 else 0),
        "attempt_count": attempt_count,
        "sporttery_attempts": sporttery_attempts,
        "fallback_attempts": fallback_attempts,
        "empty_attempts": empty_attempts,
        "warning_attempts": warning_attempts + (1 if warnings else 0),
        "all_attempts_stable": all_attempts_stable,
        "partial_fallback_used": fallback_used or fallback_attempts > 0,
        "fallback_used": fallback_used,
        "warning_count": len(warnings),
        "warnings": warnings,
        "status": status.get("status", "unknown"),
        "message_zh": message,
        "degraded_reason_zh": degraded_reason,
        "reliability_score": score_payload["score"],
        "reliability_label_zh": score_payload["label_zh"],
        "reliability_reason_zh": score_payload["reason_zh"],
        "decision_guide_zh": score_payload["decision_guide_zh"],
        "source_action_items": score_payload["action_items"],
        "professional_score_cap": _professional_cap(score_payload["score"], health, provider_used),
        "component_detail_zh": _component_detail(provider_used, health, score_payload["score"], degraded_reason),
        "recovery_hint_zh": "如显示 fallback/empty，请稍后刷新或查看竞彩足球页；系统不会把回退数据伪装成 Sporttery。",
        "scan_summary_zh": _scan_summary(scan_window, scanned_dates),
    }


def _normalize_existing(existing: dict, preview: dict, status: dict) -> dict:
    score = _int(existing.get("reliability_score"))
    provider = str(existing.get("provider_used") or preview.get("provider_used") or "unknown")
    health = str(existing.get("health") or "unknown")
    payload = dict(existing)
    payload.setdefault("version", "source_reliability_v1")
    payload.setdefault("provider_used", provider)
    payload.setdefault("status", status.get("status", "unknown"))
    payload.setdefault("professional_score_cap", _professional_cap(score, health, provider))
    payload.setdefault("component_detail_zh", _component_detail(provider, health, score, payload.get("degraded_reason_zh", "")))
    payload.setdefault("source_action_items", [])
    payload.setdefault("reliability_reason_zh", "基于已有 source_health 字段复用。")
    return payload


def _score_source(*, health: str, attempt_count: int, sporttery_attempts: int, fallback_attempts: int, empty_attempts: int, warning_attempts: int, scan_complete: bool) -> dict:
    if attempt_count <= 0:
        score = 0
    else:
        sporttery_ratio = sporttery_attempts / attempt_count
        fallback_penalty = fallback_attempts / attempt_count * 35
        empty_penalty = empty_attempts / attempt_count * 15
        warning_penalty = warning_attempts / attempt_count * 20
        completeness_bonus = 10 if scan_complete else 0
        score = round(max(0, min(100, sporttery_ratio * 90 + completeness_bonus - fallback_penalty - empty_penalty - warning_penalty)))
    if health == "stable" and score >= 90:
        label = "高"
        guide = "可优先查看真实数据观察信号，但仍需结合缺失情报和风险纪律。"
    elif health in {"stable", "degraded"} and score >= 60:
        label = "中"
        guide = "可查看观察信号，同时重点确认扫描窗口内是否有回退日期。"
    elif health == "fallback":
        label = "回退"
        guide = "当前含 mock/fallback 数据，只适合演示流程和纸面学习。"
    else:
        label = "低"
        guide = "数据源证据不足，优先刷新或改看模拟/回测页面。"
    return {
        "score": score,
        "label_zh": label,
        "reason_zh": "基于 Sporttery 成功比例、回退次数、空结果、提醒数量和扫描完整性计算。",
        "decision_guide_zh": guide,
        "action_items": [
            f"扫描窗口内 Sporttery 成功 {sporttery_attempts}/{attempt_count} 天。",
            f"回退 {fallback_attempts} 天，空结果 {empty_attempts} 天，提醒 {warning_attempts} 天。",
            "如果评级不是“高”，先修数据源稳定性，再评价模型好坏。",
        ],
    }


def _professional_cap(score: int, health: str, provider: str) -> int:
    if provider in {"mock", "fallback", "fixture"} or health == "fallback":
        return 64
    if score < 45:
        return 72
    if score < 70:
        return 82
    if score < 85:
        return 90
    return 95


def _component_detail(provider: str, health: str, score: int, degraded_reason: str) -> str:
    return f"数据源可靠性 {score}/100，provider={provider}，状态={health}。{degraded_reason or '扫描窗口未发现明显异常。'}"


def _degraded_reason(fallback_attempts: int, empty_attempts: int, warning_attempts: int, warnings: list) -> str:
    reasons = []
    if fallback_attempts:
        reasons.append(f"扫描窗口内有 {fallback_attempts} 天使用 mock/fallback。")
    if empty_attempts:
        reasons.append(f"扫描窗口内有 {empty_attempts} 天空结果。")
    if warning_attempts or warnings:
        reasons.append(f"存在 {warning_attempts + len(warnings)} 条数据源提醒。")
    return " ".join(reasons) or "扫描窗口未发现回退或异常提醒。"


def _scan_summary(scan_window: dict, scanned_dates: list[str]) -> str:
    if scan_window:
        start = scan_window.get("start_date", "unknown")
        end = scan_window.get("end_date", "unknown")
        days = scan_window.get("days_checked", len(scanned_dates))
        complete = "完整" if scan_window.get("complete") else "不完整"
        return f"扫描窗口：{start} 至 {end}，共 {days} 天，状态：{complete}。"
    if scanned_dates:
        return "扫描日期：" + "、".join(scanned_dates)
    return "尚未记录扫描窗口。"


def _int(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0

from __future__ import annotations

from src.view_models.intelligence_view import build_intelligence_view


def build_next_available_view(preview: dict) -> dict:
    view = build_intelligence_view(preview)
    status = preview.get("data_source_status", {}) or {}
    view.update(
        {
            "title": "今日观察",
            "selected_date": preview.get("selected_date") or preview.get("date"),
            "provider_used": preview.get("provider_used", "unknown"),
            "matches_count": preview.get("matches_count", 0),
            "data_source_status": status,
            "source_health": _source_health(preview, status),
            "attempts": preview.get("attempts", []),
            "top_observations": preview.get("top_observations", {}),
            "top_rejected_2x1": _top_rejected_combos(preview, "parlay_2x1", 5),
            "top_rejected_3x1": _top_rejected_combos(preview, "parlay_3x1", 5),
            "max_risk_tip": _max_risk_tip(preview),
        }
    )
    return view


def _source_health(preview: dict, status: dict) -> dict:
    attempts = preview.get("attempts", []) or []
    scan_window = preview.get("scan_window") if isinstance(preview.get("scan_window"), dict) else {}
    matches_count = int(preview.get("matches_count", 0) or 0)
    provider_used = str(preview.get("provider_used") or "unknown")
    fallback_used = bool(preview.get("fallback_used"))
    warnings = list(preview.get("warnings", []) or preview.get("provider_warnings", []) or [])
    scanned_dates = [item.get("date") for item in attempts if isinstance(item, dict) and item.get("date")]
    successful_attempts = [
        item for item in attempts
        if isinstance(item, dict) and int(item.get("matches_count", 0) or 0) > 0
    ]
    attempt_count = len(attempts)
    sporttery_attempts = 0
    fallback_attempts = 0
    empty_attempts = 0
    warning_attempts = 0
    degraded_reasons: list[str] = []
    for item in attempts:
        if not isinstance(item, dict):
            continue
        item_provider = str(item.get("provider_used") or item.get("provider") or "unknown")
        item_matches = int(item.get("matches_count", 0) or 0)
        item_status = str(item.get("status") or "")
        item_warnings = item.get("warnings") or item.get("provider_warnings") or []
        if item_provider == "sporttery":
            sporttery_attempts += 1
        if item_provider == "mock" or item_status in {"fallback", "mock"} or bool(item.get("fallback_used")):
            fallback_attempts += 1
        if item_matches == 0:
            empty_attempts += 1
        if item_warnings:
            warning_attempts += 1
    partial_fallback_used = fallback_used or fallback_attempts > 0
    all_attempts_stable = (
        attempt_count > 0
        and bool(scan_window.get("complete"))
        and fallback_attempts == 0
        and warning_attempts == 0
        and sporttery_attempts == attempt_count
    )
    if fallback_attempts:
        degraded_reasons.append(f"扫描窗口内有 {fallback_attempts} 天使用 mock/fallback。")
    if warning_attempts:
        degraded_reasons.append(f"扫描窗口内有 {warning_attempts} 天存在数据源提醒。")
    if empty_attempts and matches_count == 0:
        degraded_reasons.append(f"扫描窗口内有 {empty_attempts} 天没有读取到可售比赛。")
    degraded_reason_zh = " ".join(degraded_reasons) or "扫描窗口未发现回退或异常提醒。"
    if provider_used == "sporttery" and matches_count > 0 and all_attempts_stable:
        health = "stable"
        message = "Sporttery 当前可读取，完整扫描窗口未发现回退或异常提醒。"
    elif provider_used == "sporttery" and matches_count > 0:
        health = "degraded"
        message = "选中日期可读取 Sporttery，但扫描窗口内存在回退、空结果或数据源提醒，请查看扫描日期明细。"
    elif fallback_used or provider_used == "mock":
        health = "fallback"
        message = "Sporttery 当前不可用或未返回可售比赛，已使用本地示例回退。"
    elif matches_count == 0:
        health = "empty"
        message = "扫描范围内暂未读取到可售比赛。"
    else:
        health = "unknown"
        message = "数据源状态不明确，请查看数据源提醒。"
    return {
        "health": health,
        "provider_used": provider_used,
        "selected_date": preview.get("selected_date") or preview.get("date"),
        "matches_count": matches_count,
        "scanned_dates": scanned_dates,
        "scan_window": scan_window,
        "successful_attempts": len(successful_attempts),
        "attempt_count": attempt_count,
        "sporttery_attempts": sporttery_attempts,
        "fallback_attempts": fallback_attempts,
        "empty_attempts": empty_attempts,
        "warning_attempts": warning_attempts,
        "all_attempts_stable": all_attempts_stable,
        "partial_fallback_used": partial_fallback_used,
        "fallback_used": fallback_used,
        "warning_count": len(warnings),
        "warnings": warnings,
        "status": status.get("status", "unknown"),
        "message_zh": message,
        "degraded_reason_zh": degraded_reason_zh,
        "recovery_hint_zh": "如显示 fallback/empty，请稍后刷新，或查看竞彩足球页的数据源提醒；系统不会把回退数据伪装成 Sporttery。",
        "scan_summary_zh": _scan_summary(scan_window, scanned_dates),
    }


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


def _top_rejected_combos(preview: dict, key: str, limit: int) -> list[dict]:
    rankings = ((preview.get("optimizer") or {}).get("candidate_rankings") or {}).get(key) or []
    rows = [item for item in rankings if isinstance(item, dict) and not item.get("selected")]
    return [_combo_reject_row(item) for item in rows[:limit]]


def _combo_reject_row(item: dict) -> dict:
    return {
        "type": {"parlay_2x1": "2串1", "parlay_3x1": "3串1"}.get(str(item.get("type")), str(item.get("type") or "")),
        "legs": item.get("legs") or item.get("match") or "",
        "odds": _num(item.get("odds")),
        "model_prob": _pct(item.get("model_prob")),
        "market_prob": _pct(item.get("market_prob")),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        "risk_level": item.get("risk_level", ""),
        "status": item.get("status", "未入选"),
        "reject_reason": item.get("reject_reason", "未通过组合纪律。"),
    }


def _pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _signed_pct(value) -> str:
    try:
        return f"{float(value) * 100:+.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _num(value) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "N/A"


def _max_risk_tip(preview: dict) -> str:
    portfolio = (preview.get("optimizer", {}).get("selected_portfolio", {}) or {})
    if portfolio.get("parlay_3x1"):
        return "当前包含 3串1 纸面组合观察，风险最高，请重点查看组合风险。"
    if portfolio.get("parlay_2x1"):
        return "当前包含 2串1 纸面组合观察，串关会放大不确定性。"
    if portfolio.get("singles"):
        return "当前仅有单关观察通过约束，组合观察未通过风险纪律。"
    return "当前没有通过约束的观察信号，严格交易纪律显示无观察价值。"

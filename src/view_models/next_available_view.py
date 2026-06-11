from __future__ import annotations

from src.audit.credibility import audit_credibility
from src.audit.trader_review import build_trader_review
from src.intelligence.signal_explainer import explain_combo_discipline
from src.optimizer.best_parlay import build_best_parlay_summary
from src.view_models.intelligence_view import build_intelligence_view


def build_next_available_view(preview: dict) -> dict:
    view = build_intelligence_view(preview)
    status = preview.get("data_source_status", {}) or {}
    top_rejected_2x1 = _top_rejected_combos(preview, "parlay_2x1", 5)
    top_rejected_3x1 = _top_rejected_combos(preview, "parlay_3x1", 5)
    top_2x1 = view.get("top_2x1", []) or []
    top_2x1_display = top_2x1 if top_2x1 else top_rejected_2x1[:3]
    optimizer = preview.get("optimizer", {}) or {}
    credibility = audit_credibility(preview, optimizer)
    best_parlay = optimizer.get("best_parlay_summary") or build_best_parlay_summary(optimizer)
    trader_review = build_trader_review(preview, optimizer)
    view.update(
        {
            "title": "今日观察",
            "selected_date": preview.get("selected_date") or preview.get("date"),
            "provider_used": preview.get("provider_used", "unknown"),
            "matches_count": preview.get("matches_count", 0),
            "data_source_status": status,
            "source_health": _source_health(preview, status),
            "reliability_summary": preview.get("reliability_summary", {}),
            "intelligence_completeness": preview.get("intelligence_completeness", {}),
            "source_coverage_cards": view.get("source_coverage_cards", []),
            "match_coverage_table": view.get("match_coverage_table", []),
            "attempts": preview.get("attempts", []),
            "top_observations": preview.get("top_observations", {}),
            "top_2x1_display": top_2x1_display,
            "top_2x1_display_mode": "selected" if top_2x1 else "nearest_rejected",
            "top_2x1_empty_explanation": _top_2x1_empty_explanation(top_rejected_2x1),
            "top_rejected_2x1": top_rejected_2x1,
            "top_rejected_3x1": top_rejected_3x1,
            "credibility_audit": credibility,
            "best_parlay_summary": best_parlay,
            "trader_review": trader_review,
            "strict_trader_conclusion": trader_review.get("final_call_zh"),
            "max_risk_tip": _max_risk_tip(preview),
            "operation_entry": _operation_entry(preview),
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
    reliability = _source_reliability(
        health=health,
        attempt_count=attempt_count,
        sporttery_attempts=sporttery_attempts,
        fallback_attempts=fallback_attempts,
        empty_attempts=empty_attempts,
        warning_attempts=warning_attempts,
        scan_complete=bool(scan_window.get("complete")),
    )
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
        "reliability_score": reliability["score"],
        "reliability_label_zh": reliability["label_zh"],
        "reliability_reason_zh": reliability["reason_zh"],
        "decision_guide_zh": reliability["decision_guide_zh"],
        "source_action_items": reliability["action_items"],
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


def _source_reliability(
    *,
    health: str,
    attempt_count: int,
    sporttery_attempts: int,
    fallback_attempts: int,
    empty_attempts: int,
    warning_attempts: int,
    scan_complete: bool,
) -> dict:
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
        guide = "可优先查看 Sporttery 观察信号，但仍需结合缺失情报和风险纪律。"
    elif health in {"stable", "degraded"} and score >= 60:
        label = "中"
        guide = "可查看观察信号，同时重点确认扫描窗口内是否有回退日期。"
    elif health == "fallback":
        label = "回退"
        guide = "当前含 mock/fallback 数据，只适合演示流程，不应把它当作 Sporttery 实盘数据。"
    else:
        label = "低"
        guide = "数据源证据不足，优先刷新或改看模拟/回测页面，不要强行解读观察信号。"
    actions = [
        f"扫描窗口内 Sporttery 成功 {sporttery_attempts}/{attempt_count} 天。",
        f"回退 {fallback_attempts} 天，空结果 {empty_attempts} 天，提醒 {warning_attempts} 天。",
        "如果评级不是“高”，请查看竞彩足球页的数据源明细和 provider_used。",
    ]
    return {
        "score": score,
        "label_zh": label,
        "reason_zh": f"基于扫描完整性、Sporttery 成功比例、回退次数、空结果和提醒数量计算。",
        "decision_guide_zh": guide,
        "action_items": actions,
    }


def _top_rejected_combos(preview: dict, key: str, limit: int) -> list[dict]:
    rankings = ((preview.get("optimizer") or {}).get("candidate_rankings") or {}).get(key) or []
    rows = [item for item in rankings if isinstance(item, dict) and not item.get("selected")]
    return [_combo_reject_row(item) for item in rows[:limit]]


def _top_2x1_empty_explanation(rows: list[dict]) -> str:
    if not rows:
        return "当前没有可排序的 2串1 候选；系统不会为了凑组合而降低纪律。"
    first_reason = rows[0].get("reject_reason") or "未通过组合纪律。"
    return f"当前没有 2串1 入选；下方展示最接近的候选和被拒原因。首要原因：{first_reason}"


def _combo_reject_row(item: dict) -> dict:
    row = {
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
    row.update(explain_combo_discipline(item))
    return row


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


def _operation_entry(preview: dict) -> dict:
    portfolio = (preview.get("optimizer", {}).get("selected_portfolio", {}) or {})
    singles = len(portfolio.get("singles") or [])
    parlay2 = len(portfolio.get("parlay_2x1") or [])
    parlay3 = len(portfolio.get("parlay_3x1") or [])
    if singles or parlay2 or parlay3:
        summary = f"当前纸面观察包含单关 {singles}、2串1 {parlay2}、3串1 {parlay3}。可进入模拟走盘查看历史资金曲线。"
    else:
        summary = "当前没有通过约束的组合观察；仍可进入模拟走盘查看历史策略为什么赚/亏。"
    return {
        "title": "回测表现怎么看",
        "summary": summary,
        "metrics": [
            "资金曲线：观察纸面本金随时间变化。",
            "最大回撤：观察最差阶段的资金压力。",
            "玩法贡献：拆分单关、2串1、3串1 对盈亏的贡献。",
            "盈亏归因：解释为什么赚/亏，而不是只看最终金额。",
        ],
        "action_label": "查看模拟走盘",
        "target_view": "operation",
        "disclaimer": "模拟经营不代表未来表现，也不构成任何购买指令。",
    }

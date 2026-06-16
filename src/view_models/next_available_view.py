from __future__ import annotations

from src.audit.credibility import audit_credibility
from src.audit.trader_review import build_trader_review
from src.explain.deepseek_config import llm_status_payload
from src.intelligence.signal_explainer import explain_combo_discipline
from src.learning.home_learning_view import build_home_learning_panel
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
    llm_status = llm_status_payload()
    ai_layer = _ai_research_layer(best_parlay, llm_status)
    daily_2x1 = best_parlay.get("daily_2x1_candidate") or {}
    daily_3x1 = best_parlay.get("daily_3x1_candidate") or {}
    trader_review = build_trader_review(preview, optimizer)
    learning_panel = build_home_learning_panel()
    daily_2x1_display = top_2x1 if top_2x1 else _candidate_list(daily_2x1, top_rejected_2x1[:3])
    daily_3x1_display = _candidate_list(daily_3x1, top_rejected_3x1[:3])
    long_run_score = _long_run_score(
        preview=preview,
        view=view,
        source_health=_source_health(preview, status),
        gate=preview.get("credibility_gate", {}) or {},
        learning_panel=learning_panel,
        has_combo_context=bool(daily_2x1_display or daily_3x1_display or top_rejected_2x1 or top_rejected_3x1),
    )
    view.update(
        {
            "title": "明日预观察",
            "selected_date": preview.get("selected_date") or preview.get("date"),
            "provider_used": preview.get("provider_used", "unknown"),
            "matches_count": preview.get("matches_count", 0),
            "prematch_workflow": preview.get("prematch_workflow", {}),
            "workflow_cards": _workflow_cards(preview.get("prematch_workflow", {})),
            "learning_panel": learning_panel,
            "daily_learning_summary_zh": learning_panel.get("latest_daily_summary_zh", ""),
            "window_learning_summaries_zh": learning_panel.get("window_summaries_zh", []),
            "daily_learning_digest": learning_panel.get("daily_digest", {}),
            "window_learning_digests": learning_panel.get("window_digests", []),
            "daily_learning_report": learning_panel.get("daily_report", {}),
            "window_learning_reports": learning_panel.get("window_reports", []),
            "daily_learning_metrics": learning_panel.get("daily_metrics", []),
            "window_learning_metrics": learning_panel.get("window_metrics", []),
            "data_source_status": status,
            "source_health": _source_health(preview, status),
            "long_run_score": long_run_score,
            "reliability_summary": preview.get("reliability_summary", {}),
            "intelligence_completeness": preview.get("intelligence_completeness", {}),
            "coverage_notes": preview.get("coverage_notes", []),
            "source_coverage_cards": view.get("source_coverage_cards", []),
            "match_coverage_table": view.get("match_coverage_table", []),
            "attempts": preview.get("attempts", []),
            "top_observations": preview.get("top_observations", {}),
            "top_2x1_display": daily_2x1_display,
            "top_3x1_display": daily_3x1_display,
            "top_2x1_display_mode": "selected" if top_2x1 else "nearest_rejected",
            "top_2x1_empty_explanation": _top_2x1_empty_explanation(top_rejected_2x1, preview.get("prematch_workflow", {})),
            "top_3x1_empty_explanation": _top_3x1_empty_explanation(top_rejected_3x1, preview.get("prematch_workflow", {})),
            "top_rejected_2x1": top_rejected_2x1,
            "top_rejected_3x1": top_rejected_3x1,
            "credibility_audit": credibility,
            "best_parlay_summary": best_parlay,
            "combo_user_board": best_parlay.get("user_combo_board", {}),
            "llm_status": llm_status,
            "ai_research_layer": ai_layer,
            "ai_research_status": _ai_research_status(ai_layer),
            "combo_gate_summary_zh": _combo_gate_summary(credibility, optimizer, best_parlay),
            "trader_review": trader_review,
            "strict_trader_conclusion": trader_review.get("final_call_zh"),
            "max_risk_tip": _max_risk_tip(preview),
            "operation_entry": _operation_entry(preview),
            "warnings": _filtered_next_available_warnings(preview, view),
        }
    )
    return view


def _long_run_score(
    *,
    preview: dict,
    view: dict,
    source_health: dict,
    gate: dict,
    learning_panel: dict,
    has_combo_context: bool,
) -> dict:
    provider_used = str(preview.get("provider_used") or "")
    matches_count = int(preview.get("matches_count") or 0)
    source_score = _clamp_score(
        source_health.get("reliability_score")
        if matches_count > 0 and provider_used != "mock"
        else 45 if provider_used == "mock" else 15
    )
    singles = view.get("top_singles") or []
    totals = view.get("top_total_goals") or []
    scores = view.get("top_scores") or []
    rejected = ((preview.get("optimizer") or {}).get("candidate_rankings") or {}).get("parlay_2x1") or []
    signal_score = _clamp_score(
        (46 if singles else 0)
        + min(18, len(singles) * 6)
        + (16 if totals else 0)
        + (12 if scores else 0)
        + (8 if rejected else 0)
    )
    gate_name = str(gate.get("combo_gate") or "")
    combo_learning = learning_panel.get("combo_discipline_learning") if isinstance(learning_panel.get("combo_discipline_learning"), dict) else {}
    combo_bonus = _safe_int(combo_learning.get("score_bonus")) or 0
    combo_score = _clamp_score(
        92 if gate_name == "open"
        else 78 if gate_name == "restricted"
        else 70 if gate_name == "closed"
        else 62 if has_combo_context
        else 25
    )
    combo_score = _clamp_score(combo_score + combo_bonus)
    combo_detail = gate.get("label_zh") or gate.get("reason_zh") or "等待门控结论"
    if combo_learning.get("review_count"):
        combo_detail = f"{combo_detail}；被拒组合复盘 {combo_learning.get('review_count')} 条"
    ai_layer = _ai_research_layer((preview.get("optimizer") or {}).get("best_parlay_summary") or {})
    ai_score = _clamp_score(92 if ai_layer.get("enabled") else 45)
    history_cards = learning_panel.get("history_cards") or []
    settled_count = _first_int_from_cards(history_cards, "累计样本")
    learning_todo = learning_panel.get("learning_todo") or {}
    clv_count = _safe_int(learning_todo.get("clv_count")) or 0
    pack_ready = bool(learning_todo.get("pack_ready"))
    feedback_files = _first_int_from_cards(history_cards, "学习文件")
    learning_score = _learning_score(
        learning_todo.get("current_score"),
        settled_count=settled_count,
        clv_count=clv_count,
        feedback_files=feedback_files,
        pack_ready=pack_ready,
    )
    learning_detail = _learning_detail(
        settled_count=settled_count,
        clv_count=clv_count,
        feedback_files=feedback_files,
        pack_ready=pack_ready,
    )
    items = [
        {
            "label": "数据源",
            "score": source_score,
            "detail": f"{provider_used or 'auto'} · {matches_count} 场" if source_score >= 80 else "未拿到高可靠真实可售比赛",
            "next": "优先保持 Sporttery 主数据稳定，并记录 fallback/缓存状态。",
        },
        {
            "label": "Top信号",
            "score": signal_score,
            "detail": f"单关 {len(singles)} 条，含进球/比分参考" if singles else "暂无单关候选",
            "next": "补赔率覆盖、校准样本和临场复核，让 Top 信号更少但更硬。",
        },
        {
            "label": "组合纪律",
            "score": combo_score,
            "detail": combo_detail,
            "next": combo_learning.get("message_zh") or "不要强行串联；先提高单腿可信度、降低相关性和长冷风险。",
        },
        {
            "label": "AI研究",
            "score": ai_score,
            "detail": "DS Pro 已配置，可自动研究" if ai_layer.get("enabled") else "本地摘要可用，DS Pro 未开启",
            "next": "让 DS Pro 自动总结被拒原因、赔率覆盖和赛后学习点。",
        },
        {
            "label": "赛后学习",
            "score": learning_score,
            "detail": learning_detail,
            "next": learning_todo.get("next_action_zh") or "长期提升靠赛后比分、收盘赔率、CLV 和概率校准样本。",
        },
    ]
    weights = [0.22, 0.22, 0.20, 0.18, 0.18]
    total = _clamp_score(sum(item["score"] * weights[index] for index, item in enumerate(items)))
    weakest = sorted(items, key=lambda item: item["score"])[0]
    score_roadmap = _score_roadmap(items)
    label = "可用" if total >= 80 else "可观察" if total >= 60 else "准备中"
    return {
        "version": "long_run_score_v1",
        "score": total,
        "label_zh": label,
        "items": items,
        "weakest_item": weakest,
        "score_roadmap": score_roadmap,
        "next_action_zh": f"当前最低分：{weakest['label']}，下一步：{weakest['next']}",
        "meaning_zh": "这是长期改进分，不是胜率；用于决定下一轮优先补数据、补学习样本还是优化组合纪律。",
    }


def _score_roadmap(items: list[dict]) -> list[dict]:
    roadmap = [
        {
            "rank": index + 1,
            "label": item.get("label"),
            "score": _clamp_score(item.get("score")),
            "detail": item.get("detail", ""),
            "next": item.get("next", ""),
        }
        for index, item in enumerate(sorted(items, key=lambda row: _clamp_score(row.get("score"))))
        if _clamp_score(item.get("score")) < 90
    ]
    return roadmap[:3]


def _learning_score(current_score, *, settled_count: int, clv_count: int, feedback_files: int, pack_ready: bool) -> int:
    if current_score is not None:
        base = _clamp_score(current_score)
    else:
        base = 58
    if pack_ready:
        base = max(base, 65)
    if feedback_files > 1 or settled_count > 0:
        base = max(base, 72)
    if clv_count > 0:
        base = max(base, 78)
    if settled_count >= 30 and clv_count >= 20:
        base = max(base, 88)
    return _clamp_score(base)


def _learning_detail(*, settled_count: int, clv_count: int, feedback_files: int, pack_ready: bool) -> str:
    parts = []
    if settled_count:
        parts.append(f"已结算 {settled_count} 条")
    if clv_count:
        parts.append(f"CLV {clv_count} 项")
    if feedback_files:
        parts.append(f"学习文件 {feedback_files} 个")
    if not parts and pack_ready:
        return "学习包已准备，等待赛后比分和收盘赔率"
    if not parts:
        return "赛后可对照结果继续校准"
    return "，".join(parts)


def _clamp_score(value) -> int:
    try:
        num = float(value)
    except (TypeError, ValueError):
        num = 0.0
    return max(0, min(100, round(num)))


def _safe_int(value) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _first_int_from_cards(cards: list[dict], label: str) -> int:
    for card in cards:
        if str(card.get("label")) == label:
            try:
                return int(float(card.get("value") or 0))
            except (TypeError, ValueError):
                return 0
    return 0


def _candidate_list(primary: dict, fallback: list[dict]) -> list[dict]:
    if primary and primary.get("status") != "empty" and (primary.get("legs") or primary.get("match")):
        return [primary]
    return fallback or []


def _ai_research_layer(best_parlay: dict, status: dict | None = None) -> dict:
    status = status or llm_status_payload()
    enabled = bool(status.get("enabled") and status.get("api_key_present") and status.get("status") == "ready")
    board = best_parlay.get("user_combo_board") or {}
    runtime_status = status.get("runtime_status", "not_requested")
    detail = status.get("status_detail_zh") or status.get("fallback_reason") or ""
    if runtime_status == "loaded":
        title_zh = "DS Pro 已参与研究"
        message_zh = "本轮已完成 DS Pro 解释，可直接查看候选、被拒原因、token 消耗和赛后学习点。"
    elif runtime_status == "cached":
        title_zh = "已复用最近一次 DS 研究"
        message_zh = "本轮实时请求未成功，但已复用最近一次成功的 DS 研究结果，避免首页直接退回纯本地摘要。"
    elif status.get("ds_attempted"):
        title_zh = "AI 研究已回退本地摘要"
        message_zh = detail or "本轮已自动尝试 DS，但未成功返回，当前继续显示本地研究摘要。"
    elif enabled:
        title_zh = "AI 研究增强待触发"
        message_zh = "DeepSeek 可用于赛前资料、赔率逻辑和组合纪律解释；概率和组合筛选仍由本地模型决定。"
    else:
        title_zh = "AI 研究增强未开启"
        message_zh = detail or "当前不消耗 DeepSeek token；App 先用本地赔率学习、概率校准和组合纪律给出结论。"
    return {
        "provider": status.get("provider", "deepseek"),
        "enabled": enabled,
        "status": status.get("status", "disabled"),
        "status_zh": status.get("status_zh", status.get("status", "unknown")),
        "runtime_status": runtime_status,
        "runtime_status_zh": status.get("runtime_status_zh", "未请求 AI 研究"),
        "ds_attempted": bool(status.get("ds_attempted")),
        "ds_completed": bool(status.get("ds_completed")),
        "ds_error_code": status.get("ds_error_code", ""),
        "display_status_zh": detail or ("DS Pro 已参与本次研究。" if status.get("runtime_status") == "loaded" else ""),
        "last_error_code": status.get("last_error_code", ""),
        "last_error_label_zh": status.get("last_error_label_zh", ""),
        "last_error_message_zh": status.get("last_error_message_zh", ""),
        "last_provider_requested": status.get("last_provider_requested", ""),
        "last_provider_target": status.get("last_provider_target", ""),
        "last_provider_resolved": status.get("last_provider_resolved", ""),
        "last_token_in": status.get("last_token_in"),
        "last_token_out": status.get("last_token_out"),
        "last_token_total": status.get("last_token_total"),
        "fallback_reason": status.get("fallback_reason", ""),
        "config_status_zh": status.get("config_status_zh", ""),
        "runtime_notice_zh": status.get("runtime_notice_zh", ""),
        "next_step_zh": status.get("next_step_zh", ""),
        "ai_research_status": status.get("ai_research_status", {}),
        "safe_usage": status.get("safe_usage", "optional_explainer_only"),
        "title_zh": title_zh,
        "message_zh": message_zh,
        "research_prompt_zh": board.get("ai_research_prompt_zh", "开启后用于解释强观察组合和被拒原因。"),
        "not_used_for_zh": "不参与真实下单，不直接改写概率，不绕过可信度门控。",
    }


def _ai_research_status(ai_layer: dict) -> dict:
    direct = ai_layer.get("ai_research_status")
    if isinstance(direct, dict) and direct.get("status"):
        return direct
    runtime_status = str(ai_layer.get("runtime_status") or "")
    config_status = str(ai_layer.get("status") or "")
    attempted = bool(ai_layer.get("ds_attempted"))
    completed = bool(ai_layer.get("ds_completed"))
    error_code = str(ai_layer.get("ds_error_code") or ai_layer.get("last_error_code") or "")
    error_label = str(ai_layer.get("last_error_label_zh") or "")
    if runtime_status == "loaded" and completed:
        return {
            "status": "done",
            "label_zh": "DS Pro 已参与",
            "error_code": "",
            "error_label_zh": "",
            "summary_zh": ai_layer.get("runtime_notice_zh") or ai_layer.get("display_status_zh") or "本轮已完成 DS Pro 研究。",
        }
    if runtime_status == "cached" and completed:
        return {
            "status": "cached",
            "label_zh": "已复用 DS 研究",
            "error_code": error_code,
            "error_label_zh": error_label,
            "summary_zh": ai_layer.get("runtime_notice_zh") or ai_layer.get("display_status_zh") or "本轮已复用最近一次成功的 DS 研究结果。",
        }
    if attempted:
        return {
            "status": "fallback",
            "label_zh": _fallback_label_zh(error_code, error_label),
            "error_code": error_code,
            "error_label_zh": error_label,
            "summary_zh": _fallback_summary_zh(ai_layer, error_code, error_label),
        }
    if config_status == "ready":
        return {
            "status": "ready",
            "label_zh": "等待自动研究",
            "error_code": "",
            "error_label_zh": "",
            "summary_zh": ai_layer.get("next_step_zh") or ai_layer.get("message_zh") or "刷新今日观察后会自动触发 DS 研究。",
        }
    if config_status in {"missing_api_key", "disabled", "unsupported_provider"}:
        return {
            "status": "not_configured",
            "label_zh": "DS 待配置",
            "error_code": config_status,
            "error_label_zh": _config_label_zh(config_status),
            "summary_zh": ai_layer.get("config_status_zh") or "请先检查 DeepSeek 开关、Provider 和 Key。",
        }
    return {
        "status": "unknown",
        "label_zh": "待检查",
        "error_code": error_code,
        "error_label_zh": error_label,
        "summary_zh": ai_layer.get("message_zh") or ai_layer.get("config_status_zh") or "当前还没有自动研究记录。",
    }


def _fallback_label_zh(error_code: str, error_label: str) -> str:
    if error_code == "invalid_api_key":
        return "Key 无效"
    if error_code == "insufficient_balance":
        return "额度不足"
    if error_code == "rate_limited":
        return "请求过频"
    if error_code == "request_timeout":
        return "请求超时"
    if error_code == "output_budget_exhausted":
        return "输出上限不足"
    if error_code == "reasoning_only_response":
        return "未返回最终正文"
    if error_code in {"provider_unavailable", "endpoint_not_found"}:
        return "服务暂不可用"
    if error_code == "network_error":
        return "请求失败"
    if error_label:
        return error_label
    return "已回退本地摘要"


def _fallback_summary_zh(ai_layer: dict, error_code: str, error_label: str) -> str:
    explicit = str(ai_layer.get("fallback_reason") or ai_layer.get("runtime_notice_zh") or "").strip()
    if explicit:
        return explicit
    if error_code == "invalid_api_key":
        return "DeepSeek Key 无效，当前已回退本地摘要。请更新本地 DS Key 后再刷新。"
    if error_code == "insufficient_balance":
        return "DeepSeek 额度不足，当前已回退本地摘要。可补充额度后再刷新。"
    if error_code == "rate_limited":
        return "DeepSeek 请求过频，当前已回退本地摘要。请稍后再试。"
    if error_code == "request_timeout":
        return "DeepSeek 请求超时，当前已回退本地摘要。可稍后重试。"
    if error_code == "output_budget_exhausted":
        return "DeepSeek 已开始推理，但输出上限不足；当前已回退本地摘要，并建议提高输出预算后重试。"
    if error_code == "reasoning_only_response":
        return "DeepSeek 只返回了推理草稿，未返回最终正文；当前已回退本地摘要。"
    if error_code in {"provider_unavailable", "endpoint_not_found"}:
        return "DeepSeek 服务暂不可用，当前已回退本地摘要。"
    if error_code == "network_error":
        return "DeepSeek 网络请求失败，当前已回退本地摘要。"
    if error_label:
        return f"{error_label}，当前已回退本地摘要。"
    return "本轮已自动尝试 DS，但当前回退为本地摘要。"


def _config_label_zh(config_status: str) -> str:
    if config_status == "missing_api_key":
        return "缺少 API Key"
    if config_status == "disabled":
        return "未启用"
    if config_status == "unsupported_provider":
        return "Provider 不受支持"
    return "待配置"


def _combo_gate_summary(credibility: dict, optimizer: dict, best_parlay: dict) -> str:
    gate = credibility.get("credibility_gate", {}) or {}
    reason = (
        optimizer.get("no_combo_reason")
        or best_parlay.get("no_combo_reason")
        or gate.get("reason_zh")
        or "当前暂无明确组合结论。"
    )
    label = gate.get("label_zh") or gate.get("combo_gate") or "待评估"
    return f"{label}：{reason}"


def _filtered_next_available_warnings(preview: dict, view: dict) -> list[str]:
    raw = list(view.get("warnings", []) or preview.get("warnings", []) or [])
    filtered = []
    for item in raw:
        text = str(item or "").strip()
        if not text:
            continue
        if "sporttery provider failed:" in text and "fallback to mock" in text:
            continue
        filtered.append(text)
    return filtered


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


def _top_2x1_empty_explanation(rows: list[dict], workflow: dict) -> str:
    prefix = ""
    if str(workflow.get("stage") or "").startswith("t_plus_"):
        prefix = "T+1/提前预观察阶段不强行给最终串联；"
    if not rows:
        return prefix + "当前没有可排序的 2串1 候选；系统不会为了凑组合而降低纪律。"
    first_reason = rows[0].get("reject_reason") or "未通过组合纪律。"
    return f"{prefix}当前没有 2串1 入选；下方展示最接近的候选和被拒原因。首要原因：{first_reason}"


def _top_3x1_empty_explanation(rows: list[dict], workflow: dict) -> str:
    prefix = ""
    if str(workflow.get("stage") or "").startswith("t_plus_"):
        prefix = "T+1/提前预观察阶段，3串1 只能作为最高风险纸面候选；"
    if not rows:
        return prefix + "当前没有可排序的 3串1 候选；系统不会为了凑高赔率组合而降低纪律。"
    first_reason = rows[0].get("reject_reason") or "未通过 3串1 组合纪律。"
    return f"{prefix}每日展示最接近的 3串1 候选，但默认不升级为强观察。首要原因：{first_reason}"


def _workflow_cards(workflow: dict) -> list[dict]:
    if not workflow:
        return []
    pending = workflow.get("pending_confirmations") or []
    return [
        {"label": "阶段", "value": workflow.get("stage_label_zh", "预观察"), "help": workflow.get("headline_zh", "")},
        {"label": "观察日期", "value": workflow.get("selected_date", "N/A"), "help": f"距离今天 {workflow.get('days_until_match', 'N/A')} 天。"},
        {"label": "待确认", "value": len(pending), "help": "首发、终盘赔率、伤停更新、临场天气和新闻/战意需要赛日复核。"},
        {"label": "组合口径", "value": "候选池", "help": workflow.get("combo_policy_zh", "")},
    ]


def _combo_reject_row(item: dict) -> dict:
    value = _combo_value_fields(item)
    row = {
        "type": {"parlay_2x1": "2串1", "parlay_3x1": "3串1"}.get(str(item.get("type")), str(item.get("type") or "")),
        "legs": item.get("legs") or item.get("match") or "",
        "odds": _num(item.get("odds")),
        "model_prob": _pct(item.get("model_prob")),
        "market_prob": _pct(item.get("market_prob")),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        **value,
        "risk_level": item.get("risk_level", ""),
        "status": item.get("status", "未入选"),
        "reject_reason": item.get("reject_reason", "未通过组合纪律。"),
    }
    row.update(explain_combo_discipline(item))
    return row


def _combo_value_fields(item: dict) -> dict:
    odds = _float(item.get("odds") or item.get("combo_odds"))
    prob = _float(item.get("model_prob") or item.get("combo_prob"))
    if odds is None or odds <= 1 or prob is None:
        return {
            "break_even_prob": "N/A",
            "safety_margin": "N/A",
            "combo_decision_label_zh": "等待赔率",
            "combo_action_zh": "组合缺少有效赔率或概率，先不做价值判断。",
            "combo_value_reading_zh": "组合需要赔率、概率和相关性折扣后才能判断。",
            "combo_parlay_policy_zh": "不进入串联。",
        }
    break_even = 1.0 / odds
    margin = prob - break_even
    if margin < 0:
        label = "未覆盖赔率"
        action = "暂不组合。"
        policy = "组合概率低于盈亏线，不进入串联。"
    elif prob < 0.20:
        label = "命中率偏低"
        action = "只作风险观察，不作为优先组合。"
        policy = "组合命中概率低于 20%，不适合作为核心串联。"
    elif margin >= 0.05:
        label = "组合余量尚可"
        action = "可进入候选池，但还要看可信度门控和每腿质量。"
        policy = "仅作为纸面组合候选，需继续复核情报和终盘赔率。"
    else:
        label = "组合余量偏薄"
        action = "等待赔率或情报补强。"
        policy = "一般不进入串联。"
    return {
        "break_even_prob": _pct(break_even),
        "safety_margin": _signed_pct(margin),
        "combo_decision_label_zh": label,
        "combo_action_zh": action,
        "combo_value_reading_zh": f"组合赔率 {odds:.2f} 至少需要 {break_even:.1%} 同时命中；模型扣相关性后约 {prob:.1%}，安全边际 {margin:+.1%}。",
        "combo_parlay_policy_zh": policy,
    }


def _float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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

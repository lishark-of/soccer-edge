from __future__ import annotations

import hashlib
import json

from src.explain.deepseek_config import llm_status_payload
from src.explain.deepseek_explainer import explain_with_optional_deepseek
from src.explain.deepseek_runtime import update_runtime_status
from src.learning.history import build_learning_history
from src.learning.odds_education import build_odds_learning_view
from src.optimizer.best_parlay import build_best_parlay_summary


def build_ai_combo_research(
    optimizer_result: dict,
    *,
    run_ai: bool = False,
    ai_provider: str = "local",
) -> dict:
    best_parlay = optimizer_result.get("best_parlay_summary") or build_best_parlay_summary(optimizer_result)
    board = best_parlay.get("user_combo_board", {}) or {}
    learning_history = build_learning_history()
    odds_learning = build_odds_learning_view(learning_history)
    packet = _research_packet(optimizer_result, best_parlay, board, learning_history, odds_learning)
    token_budget = _token_budget(packet, llm_status_payload())
    local_summary = _local_summary(packet)
    llm_status = llm_status_payload()
    resolved_ai_provider = _resolve_ai_provider(ai_provider, llm_status)
    ai_result = {
        "provider": "local",
        "enabled": False,
        "status": "not_requested" if not run_ai else llm_status.get("status", "disabled"),
        "status_zh": _runtime_status_zh("not_requested" if not run_ai else llm_status.get("status", "disabled")),
        "text": local_summary,
        "warnings": [] if not run_ai else [_fallback_warning(ai_provider, llm_status)],
        "provider_requested": ai_provider,
        "provider_resolved": resolved_ai_provider,
        "ds_status": "not_requested" if not run_ai else llm_status.get("status", "disabled"),
        "ds_status_zh": _runtime_status_zh("not_requested" if not run_ai else llm_status.get("status", "disabled")),
        "ds_attempted": False,
        "ds_completed": False,
        "ds_error_code": "",
        "token_in": None,
        "token_out": None,
        "token_total": None,
        "fallback_reason": "" if not run_ai else llm_status.get("fallback_reason", "") or _fallback_warning(ai_provider, llm_status),
        "display_status_zh": "当前未请求 AI 研究。" if not run_ai else llm_status.get("fallback_reason", "") or _fallback_warning(ai_provider, llm_status),
    }
    should_run = run_ai and resolved_ai_provider == "deepseek"
    if should_run:
        ai_result = explain_with_optional_deepseek(
            "combo_research",
            packet,
            {
                "provider": "deepseek",
                "language": "zh-CN",
                "audience": "普通使用者",
                "max_tokens_override": _combo_research_output_cap(llm_status),
                "timeout_seconds_override": _combo_research_timeout_seconds(compact=False),
            },
        )
        primary_retry_result = _retry_primary_if_needed(packet, ai_result, llm_status)
        if primary_retry_result:
            primary_retry_failed = bool(primary_retry_result.get("primary_retry_failed"))
            if not primary_retry_failed and primary_retry_result.get("provider") == "deepseek" and primary_retry_result.get("status") == "loaded":
                ai_result = {
                    **primary_retry_result,
                    "display_status_zh": "首次请求未返回可用正文后已自动重试并成功返回。",
                    "primary_retry": {
                        "attempted": True,
                        "provider": primary_retry_result.get("provider"),
                        "status": primary_retry_result.get("status"),
                        "success": True,
                        "token_in": primary_retry_result.get("token_in"),
                        "token_out": primary_retry_result.get("token_out"),
                        "token_total": primary_retry_result.get("token_total"),
                        "ds_error_code": primary_retry_result.get("ds_error_code", ""),
                        "fallback_reason": primary_retry_result.get("fallback_reason", ""),
                        "message_zh": "首次请求未返回可用正文，已自动按原研究包重试并成功返回。",
                    },
                }
            else:
                ai_result = {
                    **ai_result,
                    "primary_retry": {
                        "attempted": True,
                        "provider": primary_retry_result.get("provider", "local"),
                        "status": primary_retry_result.get("status", "unknown"),
                        "success": False,
                        "token_in": primary_retry_result.get("token_in"),
                        "token_out": primary_retry_result.get("token_out"),
                        "token_total": primary_retry_result.get("token_total"),
                        "ds_error_code": primary_retry_result.get("ds_error_code", ""),
                        "fallback_reason": primary_retry_result.get("fallback_reason", ""),
                        "message_zh": "首次请求未返回可用正文，已自动按原研究包重试一次，但仍未成功。",
                    },
                    "warnings": (ai_result.get("warnings") or []) + (primary_retry_result.get("warnings") or []),
                }
        timeout_retry_result = _retry_timeout_if_needed(packet, ai_result, llm_status)
        if timeout_retry_result:
            timeout_retry_failed = bool(timeout_retry_result.get("timeout_retry_failed"))
            if not timeout_retry_failed and timeout_retry_result.get("provider") == "deepseek" and timeout_retry_result.get("status") == "loaded":
                ai_result = {
                    **timeout_retry_result,
                    "display_status_zh": "首次请求异常后已自动切换轻量研究并成功返回。",
                    "timeout_retry": {
                        "attempted": True,
                        "provider": timeout_retry_result.get("provider"),
                        "status": timeout_retry_result.get("status"),
                        "success": True,
                        "token_in": timeout_retry_result.get("token_in"),
                        "token_out": timeout_retry_result.get("token_out"),
                        "token_total": timeout_retry_result.get("token_total"),
                        "ds_error_code": timeout_retry_result.get("ds_error_code", ""),
                        "fallback_reason": timeout_retry_result.get("fallback_reason", ""),
                        "message_zh": "首次请求未返回可用正文，已自动缩成轻量研究包补试并成功返回。",
                    },
                }
            else:
                ai_result = {
                    **ai_result,
                    "timeout_retry": {
                        "attempted": True,
                        "provider": timeout_retry_result.get("provider", "local"),
                        "status": timeout_retry_result.get("status", "unknown"),
                        "success": False,
                        "token_in": timeout_retry_result.get("token_in"),
                        "token_out": timeout_retry_result.get("token_out"),
                        "token_total": timeout_retry_result.get("token_total"),
                        "ds_error_code": timeout_retry_result.get("ds_error_code", ""),
                        "fallback_reason": timeout_retry_result.get("fallback_reason", ""),
                        "message_zh": "首次请求未返回可用正文后已自动切轻量研究包补试，但仍未成功，继续回退本地摘要。",
                    },
                    "warnings": (ai_result.get("warnings") or []) + (timeout_retry_result.get("warnings") or []),
                }
        retry_result = _retry_structured_notes_if_needed(packet, ai_result)
        if retry_result:
            retry_failed = bool(retry_result.get("structured_retry_failed"))
            ai_result = {
                **ai_result,
                "text": (
                    (ai_result.get("text", "") + ("\n\n" + retry_result.get("text", "") if not retry_failed else "")).strip()
                ),
                "structured_retry": {
                    "attempted": True,
                    "provider": retry_result.get("provider"),
                    "status": retry_result.get("status"),
                    "success": not retry_failed,
                    "token_in": retry_result.get("token_in"),
                    "token_out": retry_result.get("token_out"),
                    "token_total": retry_result.get("token_total"),
                    "ds_error_code": retry_result.get("ds_error_code", ""),
                    "fallback_reason": retry_result.get("fallback_reason", ""),
                    "message_zh": (
                        "DS Pro 首次未返回可解析结构化块，已自动短重试一次并补齐 JSON。"
                        if not retry_failed
                        else "DS Pro 首次未返回可解析结构化块；短重试仍未补齐，已使用本地结构化兜底。"
                    ),
                },
                "warnings": (ai_result.get("warnings") or []) + (retry_result.get("warnings") or []),
        }
    ds_completed = ai_result.get("provider") == "deepseek" and ai_result.get("status") == "loaded"
    structured_notes = _merge_ds_structured_notes(_structured_notes(packet, ai_result, local_summary), ai_result.get("text", ""), packet)
    coverage_retry_result = _retry_top_coverage_if_needed(packet, structured_notes) if should_run and ds_completed else {}
    if coverage_retry_result:
        coverage_retry_failed = bool(coverage_retry_result.get("structured_coverage_retry_failed"))
        ai_result = {
            **ai_result,
            "text": (
                (ai_result.get("text", "") + ("\n\n" + coverage_retry_result.get("text", "") if not coverage_retry_failed else "")).strip()
            ),
                "structured_coverage_retry": {
                    "attempted": True,
                    "provider": coverage_retry_result.get("provider"),
                    "status": coverage_retry_result.get("status"),
                    "success": not coverage_retry_failed,
                    "token_in": coverage_retry_result.get("token_in"),
                    "token_out": coverage_retry_result.get("token_out"),
                    "token_total": coverage_retry_result.get("token_total"),
                    "ds_error_code": coverage_retry_result.get("ds_error_code", ""),
                    "fallback_reason": coverage_retry_result.get("fallback_reason", ""),
                    "message_zh": (
                        "DS 结构化 JSON 已存在，但部分 Top 卡片缺少逐场笔记；已自动短重试补洞。"
                        if not coverage_retry_failed
                    else "DS 结构化 JSON 已存在，但 Top 覆盖补洞重试未成功；缺口继续使用本地解释兜底。"
                ),
            },
            "warnings": (ai_result.get("warnings") or []) + (coverage_retry_result.get("warnings") or []),
        }
        structured_notes = _merge_ds_structured_notes(_structured_notes(packet, ai_result, local_summary), ai_result.get("text", ""), packet)
    quality_retry_result = _retry_quality_if_needed(packet, structured_notes) if should_run and ds_completed else {}
    if quality_retry_result:
        quality_retry_failed = bool(quality_retry_result.get("structured_quality_retry_failed"))
        ai_result = {
            **ai_result,
            "text": (
                (ai_result.get("text", "") + ("\n\n" + quality_retry_result.get("text", "") if not quality_retry_failed else "")).strip()
            ),
                "structured_quality_retry": {
                    "attempted": True,
                    "provider": quality_retry_result.get("provider"),
                    "status": quality_retry_result.get("status"),
                    "success": not quality_retry_failed,
                    "token_in": quality_retry_result.get("token_in"),
                    "token_out": quality_retry_result.get("token_out"),
                    "token_total": quality_retry_result.get("token_total"),
                    "ds_error_code": quality_retry_result.get("ds_error_code", ""),
                    "fallback_reason": quality_retry_result.get("fallback_reason", ""),
                    "message_zh": (
                        "DS 结构化 JSON 已存在，但质量分不足；已自动短重试补强使用者结论。"
                        if not quality_retry_failed
                    else "DS 结构化 JSON 质量分不足；质量修复重试未成功，继续使用现有结构化结果。"
                ),
            },
            "warnings": (ai_result.get("warnings") or []) + (quality_retry_result.get("warnings") or []),
        }
        structured_notes = _merge_ds_structured_notes(_structured_notes(packet, ai_result, local_summary), ai_result.get("text", ""), packet)
    ai_result.setdefault("status_zh", _runtime_status_zh(str(ai_result.get("status") or "")))
    ai_result.setdefault("ds_status_zh", _runtime_status_zh(str(ai_result.get("ds_status") or ai_result.get("status") or "")))
    ai_result.setdefault(
        "display_status_zh",
        "DS Pro 已参与本次研究。" if ai_result.get("ds_completed") else str(ai_result.get("fallback_reason") or ai_result.get("ds_status_zh") or ai_result.get("status_zh") or ""),
    )
    telemetry = _research_telemetry(ai_result, llm_status, ai_provider, resolved_ai_provider, run_ai, should_run)
    update_runtime_status(
        provider_requested=telemetry.get("provider_requested", ai_provider),
        provider_target=telemetry.get("provider_target", resolved_ai_provider),
        provider_resolved=telemetry.get("provider_resolved", resolved_ai_provider),
        ds_status=telemetry.get("ds_status", ai_result.get("status", "unknown")),
        ds_status_zh=_runtime_status_zh(telemetry.get("ds_status", ai_result.get("status", "unknown"))),
        ds_attempted=telemetry.get("ds_attempted", False),
        ds_completed=telemetry.get("ds_completed", False),
        ds_error_code=telemetry.get("ds_error_code", ""),
        fallback_reason=telemetry.get("fallback_reason", ""),
        token_in=telemetry.get("token_in"),
        token_out=telemetry.get("token_out"),
        token_total=telemetry.get("token_total"),
    )
    post_llm_status = llm_status_payload()
    cost_ledger = _ai_cost_ledger(ai_result, token_budget, structured_notes, should_run, telemetry)
    return {
        "research_version": "phase2u_ai_combo_research_v0",
        "run_ai": bool(run_ai),
        "run_ai_executed": bool(should_run),
        "provider_requested": ai_provider,
        "provider_target": resolved_ai_provider,
        "provider_resolved": telemetry.get("provider_resolved", resolved_ai_provider),
        "ds_attempted": telemetry.get("ds_attempted", False),
        "ds_completed": telemetry.get("ds_completed", False),
        "ds_status": telemetry.get("ds_status", ai_result.get("status", "unknown")),
        "ds_status_zh": _runtime_status_zh(telemetry.get("ds_status", ai_result.get("status", "unknown"))),
        "ds_error_code": telemetry.get("ds_error_code", ""),
        "token_in": telemetry.get("token_in"),
        "token_out": telemetry.get("token_out"),
        "token_total": telemetry.get("token_total"),
        "fallback_reason": telemetry.get("fallback_reason", ""),
        "display_status_zh": _display_status_zh(telemetry, ai_result),
        "timeout_retry": ai_result.get("timeout_retry", {}),
        "ai_provider_requested": ai_provider,
        "ai_provider_target": resolved_ai_provider,
        "ai_provider_resolved": telemetry.get("provider_resolved", resolved_ai_provider),
        "auto_policy": _auto_policy(ai_provider, resolved_ai_provider, llm_status),
        "auto_execution_plan": _auto_execution_plan(ai_provider, resolved_ai_provider, ds_completed, llm_status),
        "auto_mode_semantics_zh": "auto 不是单纯数据源 fallback，而是自动读取 T+1 可售比赛、自动跑本地优化器、自动调用 DS Pro 研究层，并把研究摘要保存到本地学习记录；DS Pro 只做解释、质检和复盘，不改写概率或组合筛选。",
        "llm_status": post_llm_status,
        "ai_research_status": post_llm_status.get("ai_research_status", {}),
        "config_status_zh": post_llm_status.get("config_status_zh", ""),
        "runtime_notice_zh": post_llm_status.get("runtime_notice_zh", ""),
        "next_step_zh": post_llm_status.get("next_step_zh", ""),
        "token_budget": token_budget,
        "research_packet": packet,
        "local_summary_zh": local_summary,
        "ai_summary": ai_result,
        "structured_notes": structured_notes,
        "ai_cost_ledger": cost_ledger,
        "ds_telemetry": telemetry,
        "display_cards": _display_cards(packet, ai_result),
        "token_learning_zh": "auto 模式会在刷新明日预观察后自动调用 DeepSeek Pro；同类组合可用 research_cache_key 复盘和对账。若 DeepSeek 不可用，会回退本地摘要。",
        "safety_zh": "AI 研究层只解释强观察组合、被拒原因和风险，不参与真实下单，不绕过可信度门控，也不直接改写概率。",
        "disclaimer": "仅用于观察信号、纸面模拟和风险诊断，不构成投注建议。",
    }


def _ai_cost_ledger(ai_result: dict, token_budget: dict, structured_notes: dict, should_run: bool, telemetry: dict) -> dict:
    calls: list[dict] = []
    if should_run:
        calls.append(
            {
                "step": "full_research",
                "provider": ai_result.get("provider", "local"),
                "status": ai_result.get("status", "unknown"),
                "reason_zh": "auto 模式首次调用 DS Pro，生成完整研究解释并要求附带结构化 JSON。",
            }
        )
    timeout_retry = ai_result.get("timeout_retry") or {}
    if timeout_retry.get("attempted"):
        calls.append(
            {
                "step": "timeout_retry",
                "provider": timeout_retry.get("provider", "deepseek"),
                "status": timeout_retry.get("status", "unknown"),
                "success": bool(timeout_retry.get("success")),
                "reason_zh": timeout_retry.get("message_zh", "首次请求未返回可用正文后，自动切换轻量研究包补试一次。"),
            }
        )
    retry = ai_result.get("structured_retry") or {}
    if retry.get("attempted"):
        calls.append(
            {
                "step": "structured_json_retry",
                "provider": retry.get("provider", "deepseek"),
                "status": retry.get("status", "unknown"),
                "success": bool(retry.get("success")),
                "reason_zh": retry.get("message_zh", "首次结构化 JSON 缺失，自动短重试补齐。"),
            }
        )
    coverage_retry = ai_result.get("structured_coverage_retry") or {}
    if coverage_retry.get("attempted"):
        calls.append(
            {
                "step": "top_coverage_retry",
                "provider": coverage_retry.get("provider", "deepseek"),
                "status": coverage_retry.get("status", "unknown"),
                "success": bool(coverage_retry.get("success")),
                "reason_zh": coverage_retry.get("message_zh", "结构化 JSON 未覆盖全部 Top 卡片，自动短重试补洞。"),
            }
        )
    quality_retry = ai_result.get("structured_quality_retry") or {}
    if quality_retry.get("attempted"):
        calls.append(
            {
                "step": "quality_retry",
                "provider": quality_retry.get("provider", "deepseek"),
                "status": quality_retry.get("status", "unknown"),
                "success": bool(quality_retry.get("success")),
                "reason_zh": quality_retry.get("message_zh", "结构化 JSON 质量分不足，自动短重试补强使用者结论。"),
            }
        )
    ds_calls = sum(1 for call in calls if call.get("provider") == "deepseek")
    max_auto_calls = 4
    max_input = int(token_budget.get("max_input_tokens") or 0)
    max_output = int(token_budget.get("max_output_tokens") or 0)
    per_call_upper_bound = max_input + max_output
    billable_upper_bound = per_call_upper_bound * ds_calls
    actual_total = telemetry.get("token_total")
    actual_input = telemetry.get("token_in")
    actual_output = telemetry.get("token_out")
    return {
        "version": "ai_cost_ledger_v0",
        "call_count": len(calls),
        "deepseek_call_count": ds_calls,
        "max_auto_deepseek_calls": max_auto_calls,
        "within_auto_budget": ds_calls <= max_auto_calls,
        "calls": calls,
        "actual_input_tokens": actual_input,
        "actual_output_tokens": actual_output,
        "actual_total_tokens": actual_total,
        "estimated_input_tokens": token_budget.get("estimated_input_tokens"),
        "max_input_tokens": token_budget.get("max_input_tokens"),
        "max_output_tokens_per_call": token_budget.get("max_output_tokens"),
        "per_call_upper_bound_tokens": per_call_upper_bound,
        "estimated_upper_bound_tokens": billable_upper_bound,
        "estimate_policy_zh": "这是按每次调用输入上限 + 输出上限估算的保守上界，不是 DeepSeek 实际账单；真实消耗以服务商账单为准。",
        "structured_quality_score": (structured_notes.get("quality_audit") or {}).get("score"),
        "message_zh": _ai_cost_message(ds_calls, structured_notes, actual_total),
    }


def _ai_cost_message(ds_calls: int, structured_notes: dict, actual_total_tokens) -> str:
    quality = structured_notes.get("quality_audit") or {}
    if ds_calls <= 0:
        return "本次未调用 DS Pro，使用本地结构化摘要，不消耗外部 AI token。"
    if ds_calls == 1:
        token_text = f"；实际 token {actual_total_tokens}" if actual_total_tokens is not None else ""
        return f"本次调用 DS Pro 1 次{token_text}；结构化质量 {quality.get('grade', 'N/A')} / {quality.get('score', 'N/A')}。"
    token_text = f"；累计实际 token {actual_total_tokens}" if actual_total_tokens is not None else ""
    return f"本次调用 DS Pro {ds_calls} 次{token_text}，包含结构化修复/Top 覆盖补洞；结构化质量 {quality.get('grade', 'N/A')} / {quality.get('score', 'N/A')}。"


def _research_telemetry(
    ai_result: dict,
    llm_status: dict,
    requested_provider: str,
    resolved_provider: str,
    run_ai: bool,
    should_run: bool,
) -> dict:
    calls = [ai_result]
    calls.extend(
        item
        for item in (
            ai_result.get("timeout_retry"),
            ai_result.get("structured_retry"),
            ai_result.get("structured_coverage_retry"),
            ai_result.get("structured_quality_retry"),
        )
        if isinstance(item, dict)
    )
    deepseek_calls = [call for call in calls if str(call.get("provider") or "") == "deepseek"]
    token_in = _sum_tokens(deepseek_calls, "token_in")
    token_out = _sum_tokens(deepseek_calls, "token_out")
    token_total = _sum_tokens(deepseek_calls, "token_total")
    ds_status = str(ai_result.get("ds_status") or ("not_requested" if not run_ai else llm_status.get("status", "unknown")))
    fallback_reason = str(ai_result.get("fallback_reason") or "")
    if not fallback_reason and run_ai and resolved_provider != "deepseek":
        fallback_reason = str(llm_status.get("fallback_reason") or _fallback_warning(requested_provider, llm_status))
    ds_completed = bool(ai_result.get("ds_completed")) or (str(ai_result.get("provider")) == "deepseek" and str(ai_result.get("status")) == "loaded")
    if ds_completed:
        fallback_reason = ""
    error_code = str(ai_result.get("ds_error_code") or "")
    if not error_code and not ds_completed:
        for call in calls[1:]:
            if call.get("ds_error_code"):
                error_code = str(call.get("ds_error_code") or "")
                break
    return {
        "provider_requested": requested_provider,
        "provider_target": resolved_provider,
        "provider_resolved": str(ai_result.get("provider_resolved") or ai_result.get("provider") or resolved_provider),
        "run_ai_requested": bool(run_ai),
        "run_ai_executed": bool(should_run),
        "ds_status": ds_status,
        "ds_attempted": bool(ai_result.get("ds_attempted")) or bool(should_run),
        "ds_completed": ds_completed,
        "ds_error_code": error_code,
        "token_in": token_in,
        "token_out": token_out,
        "token_total": token_total if token_total is not None else (token_in + token_out if token_in is not None and token_out is not None else None),
        "fallback_reason": fallback_reason,
        "deepseek_call_count": len(deepseek_calls),
    }


def _runtime_status_zh(status: str) -> str:
    return {
        "loaded": "DS Pro 已参与",
        "cached": "已复用最近一次 DS 研究",
        "ready": "DS Pro 可用",
        "not_requested": "未请求 AI 研究",
        "local_only": "仅本地摘要",
        "disabled": "DS 未启用",
        "unsupported_provider": "Provider 不受支持",
        "missing_api_key": "缺少 API Key",
        "error": "DS 请求失败",
        "safety_fallback": "安全过滤后回退本地摘要",
    }.get(str(status or ""), "状态未知")


def _display_status_zh(telemetry: dict, ai_result: dict) -> str:
    if telemetry.get("ds_completed"):
        return "DS Pro 已参与本次研究。"
    if telemetry.get("fallback_reason"):
        return str(telemetry.get("fallback_reason"))
    if not telemetry.get("run_ai_requested"):
        return "当前未请求 AI 研究。"
    return str(ai_result.get("ds_status_zh") or ai_result.get("status_zh") or "状态未知")


def _sum_tokens(calls: list[dict], field: str) -> int | None:
    values = []
    for call in calls:
        try:
            value = int(call.get(field))
        except (TypeError, ValueError):
            continue
        values.append(value)
    if not values:
        return None
    return sum(values)


def _retry_structured_notes_if_needed(packet: dict, ai_result: dict) -> dict:
    if ai_result.get("provider") != "deepseek" or ai_result.get("status") != "loaded":
        return {}
    if _extract_structured_notes_json(ai_result.get("text", "")):
        return {}
    retry_packet = _structured_retry_packet(packet, ai_result.get("text", ""))
    retry = explain_with_optional_deepseek(
        "combo_research",
        retry_packet,
        {
            "provider": "deepseek",
            "language": "zh-CN",
            "audience": "普通使用者",
            "repair_structured_json_only": True,
        },
    )
    if retry.get("provider") == "deepseek" and retry.get("status") == "loaded" and _extract_structured_notes_json(retry.get("text", "")):
        return retry
    return {
        **retry,
        "structured_retry_failed": True,
    }


def _retry_primary_if_needed(packet: dict, ai_result: dict, llm_status: dict) -> dict:
    if ai_result.get("provider") == "deepseek" and ai_result.get("status") == "loaded":
        return {}
    if not ai_result.get("ds_attempted"):
        return {}
    error_code = str(ai_result.get("ds_error_code") or "")
    if error_code not in {"empty_content", "output_budget_exhausted", "reasoning_only_response", "invalid_json", "unsupported_payload", "request_timeout", "network_error", "provider_unavailable"}:
        return {}
    retry = explain_with_optional_deepseek(
        "combo_research",
        packet,
        {
            "provider": "deepseek",
            "language": "zh-CN",
            "audience": "普通使用者",
            "max_tokens_override": _combo_research_retry_output_cap(llm_status, error_code, compact=False),
            "timeout_seconds_override": _combo_research_timeout_seconds(compact=False),
        },
    )
    if retry.get("provider") == "deepseek" and retry.get("status") == "loaded":
        return retry
    return {
        **retry,
        "primary_retry_failed": True,
    }


def _retry_timeout_if_needed(packet: dict, ai_result: dict, llm_status: dict) -> dict:
    if ai_result.get("provider") == "deepseek" and ai_result.get("status") == "loaded":
        return {}
    if not ai_result.get("ds_attempted"):
        return {}
    error_code = str(ai_result.get("ds_error_code") or "")
    if error_code in {"disabled", "unsupported_provider", "missing_api_key", "invalid_api_key", "insufficient_balance", "access_denied", "endpoint_not_found"}:
        return {}
    retry_packet = _compact_timeout_retry_packet(packet)
    retry = explain_with_optional_deepseek(
        "combo_research",
        retry_packet,
        {
            "provider": "deepseek",
            "language": "zh-CN",
            "audience": "普通使用者",
            "max_tokens_override": _combo_research_retry_output_cap(llm_status, error_code, compact=True),
            "timeout_seconds_override": _combo_research_timeout_seconds(compact=True),
        },
    )
    if retry.get("provider") == "deepseek" and retry.get("status") == "loaded":
        return retry
    return {
        **retry,
        "timeout_retry_failed": True,
    }


def _compact_timeout_retry_packet(packet: dict) -> dict:
    return {
        "timeout_compact_retry_only": True,
        "task_zh": "首次请求超时，只保留普通使用者最关心的结论：今天该先看什么、为什么不串、下一步补什么情报。",
        "selected_date": packet.get("selected_date"),
        "provider_used": packet.get("provider_used"),
        "combo_gate": packet.get("combo_gate"),
        "best_single": _trim_candidate(packet.get("best_single")),
        "daily_2x1_candidate": _trim_candidate(packet.get("daily_2x1_candidate")),
        "daily_3x1_candidate": _trim_candidate(packet.get("daily_3x1_candidate")),
        "best_risk_adjusted_combo": _trim_candidate(packet.get("best_risk_adjusted_combo")),
        "nearest_rejected_combos": [_trim_candidate(row) for row in (packet.get("nearest_rejected_combos") or [])[:3]],
        "learning_history_summary": {
            "settled_count": (packet.get("learning_history_summary") or {}).get("settled_count"),
            "hit_rate": (packet.get("learning_history_summary") or {}).get("hit_rate"),
            "brier_score": (packet.get("learning_history_summary") or {}).get("brier_score"),
            "log_loss": (packet.get("learning_history_summary") or {}).get("log_loss"),
            "lessons": ((packet.get("learning_history_summary") or {}).get("lessons") or [])[:2],
        },
        "missing_signals": (packet.get("missing_signals") or [])[:8],
    }


def _trim_candidate(item: dict | None) -> dict:
    row = item or {}
    return {
        "status": row.get("status"),
        "match": row.get("match"),
        "legs": row.get("legs"),
        "odds": row.get("odds"),
        "model_prob": row.get("model_prob"),
        "market_prob": row.get("market_prob"),
        "ev": row.get("ev"),
        "edge": row.get("edge"),
        "confidence_score": row.get("confidence_score"),
        "risk_level": row.get("risk_level"),
        "reject_reason": row.get("reject_reason"),
        "selected_reason_zh": row.get("selected_reason_zh"),
        "opposing_factors_zh": row.get("opposing_factors_zh"),
        "best_parlay_quality": row.get("best_parlay_quality"),
        "longshot_warning": row.get("longshot_warning"),
    }


def _compact_board(board: dict | None) -> dict:
    row = board or {}
    return {
        "headline_zh": row.get("headline_zh"),
        "gate_label_zh": row.get("gate_label_zh"),
        "user_verdict_zh": row.get("user_verdict_zh"),
        "primary_action_zh": row.get("primary_action_zh"),
        "nearest_rejected_reason_zh": row.get("nearest_rejected_reason_zh"),
        "what_to_check_next": (row.get("what_to_check_next") or [])[:4],
        "ai_research_prompt_zh": row.get("ai_research_prompt_zh"),
    }


def _compact_closing_review(review: dict | None) -> dict:
    row = review or {}
    return {
        "title_zh": row.get("title_zh"),
        "target_zh": row.get("target_zh"),
        "current_value_zh": row.get("current_value_zh"),
        "why_zh": row.get("why_zh"),
        "green_light_zh": row.get("green_light_zh"),
        "downgrade_zh": row.get("downgrade_zh"),
        "status_zh": row.get("status_zh"),
    }


def _combo_research_output_cap(llm_status: dict, compact: bool = False) -> int:
    configured = int(llm_status.get("max_output_tokens") or 4000)
    target = 520 if compact else 900
    return max(320, min(configured, target))


def _combo_research_retry_output_cap(llm_status: dict, error_code: str, compact: bool = False) -> int:
    configured = int(llm_status.get("max_output_tokens") or 4000)
    if error_code == "output_budget_exhausted":
        target = 900 if compact else 1600
        return max(480, min(configured, target))
    return _combo_research_output_cap(llm_status, compact=compact)


def _combo_research_timeout_seconds(compact: bool = False) -> float:
    return 32.0 if compact else 45.0


def _structured_retry_packet(packet: dict, first_text: object) -> dict:
    return {
        "repair_structured_json_only": True,
        "task_zh": "只补充 STRUCTURED_NOTES_JSON，不要重复长分析。",
        "first_text_preview": str(first_text or "")[:1200],
        "selected_date": packet.get("selected_date"),
        "provider_used": packet.get("provider_used"),
        "combo_gate": packet.get("combo_gate"),
        "best_single": packet.get("best_single"),
        "daily_2x1_candidate": packet.get("daily_2x1_candidate"),
        "daily_3x1_candidate": packet.get("daily_3x1_candidate"),
        "best_risk_adjusted_combo": packet.get("best_risk_adjusted_combo"),
        "nearest_rejected_combos": packet.get("nearest_rejected_combos", [])[:5],
        "missing_signals": packet.get("missing_signals", []),
    }


def _retry_top_coverage_if_needed(packet: dict, structured_notes: dict) -> dict:
    quality = structured_notes.get("quality_audit") or {}
    top_coverage = quality.get("top_card_coverage") or {}
    missing_targets = top_coverage.get("missing_targets") or []
    if structured_notes.get("structured_source") != "deepseek_structured" or not missing_targets:
        return {}
    retry_packet = _coverage_retry_packet(packet, missing_targets, structured_notes)
    retry = explain_with_optional_deepseek(
        "combo_research",
        retry_packet,
        {
            "provider": "deepseek",
            "language": "zh-CN",
            "audience": "普通使用者",
            "repair_structured_json_only": True,
        },
    )
    parsed = _extract_structured_notes_json(retry.get("text", ""))
    if retry.get("provider") == "deepseek" and retry.get("status") == "loaded" and parsed.get("match_notes"):
        return retry
    return {
        **retry,
        "structured_coverage_retry_failed": True,
    }


def _retry_quality_if_needed(packet: dict, structured_notes: dict) -> dict:
    quality = structured_notes.get("quality_audit") or {}
    score = int(quality.get("score") or 0)
    if structured_notes.get("structured_source") != "deepseek_structured" or score >= 80:
        return {}
    retry_packet = _quality_retry_packet(packet, structured_notes)
    retry = explain_with_optional_deepseek(
        "combo_research",
        retry_packet,
        {
            "provider": "deepseek",
            "language": "zh-CN",
            "audience": "普通使用者",
            "repair_structured_json_only": True,
        },
    )
    parsed = _extract_structured_notes_json(retry.get("text", ""))
    if retry.get("provider") == "deepseek" and retry.get("status") == "loaded" and parsed:
        return retry
    return {
        **retry,
        "structured_quality_retry_failed": True,
    }


def _quality_retry_packet(packet: dict, structured_notes: dict) -> dict:
    return {
        "repair_structured_json_only": True,
        "quality_repair_only": True,
        "task_zh": "只补强 STRUCTURED_NOTES_JSON 的可读性和使用者动作，不要重复长分析。",
        "existing_quality_audit": structured_notes.get("quality_audit", {}),
        "existing_daily_summary_zh": structured_notes.get("daily_summary_zh"),
        "selected_date": packet.get("selected_date"),
        "provider_used": packet.get("provider_used"),
        "combo_gate": packet.get("combo_gate"),
        "best_single": packet.get("best_single"),
        "daily_2x1_candidate": packet.get("daily_2x1_candidate"),
        "daily_3x1_candidate": packet.get("daily_3x1_candidate"),
        "best_risk_adjusted_combo": packet.get("best_risk_adjusted_combo"),
        "nearest_rejected_combos": packet.get("nearest_rejected_combos", [])[:5],
        "missing_signals": packet.get("missing_signals", []),
    }


def _coverage_retry_packet(packet: dict, missing_targets: list, structured_notes: dict) -> dict:
    return {
        "repair_structured_json_only": True,
        "coverage_repair_only": True,
        "task_zh": "只为缺失 Top 项补充 match_notes，不要重复长分析。",
        "missing_top_targets": missing_targets[:8],
        "existing_daily_summary_zh": structured_notes.get("daily_summary_zh"),
        "selected_date": packet.get("selected_date"),
        "provider_used": packet.get("provider_used"),
        "combo_gate": packet.get("combo_gate"),
        "best_single": packet.get("best_single"),
        "daily_2x1_candidate": packet.get("daily_2x1_candidate"),
        "daily_3x1_candidate": packet.get("daily_3x1_candidate"),
        "best_risk_adjusted_combo": packet.get("best_risk_adjusted_combo"),
        "nearest_rejected_combos": packet.get("nearest_rejected_combos", [])[:5],
        "missing_signals": packet.get("missing_signals", []),
    }


def _resolve_ai_provider(ai_provider: str, llm_status: dict) -> str:
    requested = str(ai_provider or "local").strip().lower()
    if requested == "auto":
        ready = bool(
            llm_status.get("enabled")
            and llm_status.get("api_key_present")
            and llm_status.get("provider") == "deepseek"
            and llm_status.get("status") == "ready"
        )
        return "deepseek" if ready else "local"
    if requested == "deepseek":
        return "deepseek"
    return "local"


def _auto_policy(requested: str, resolved: str, llm_status: dict) -> dict:
    return {
        "mode": "auto_ds_pro" if str(requested or "").lower() == "auto" else str(requested or "local"),
        "requested_provider": requested,
        "resolved_provider": resolved,
        "will_call_deepseek": resolved == "deepseek",
        "llm_status": llm_status.get("status", "unknown"),
        "message_zh": (
            "auto 已解析为 DeepSeek Pro：本次会自动调用 DS Pro 做研究解释。"
            if resolved == "deepseek"
            else "auto 已回退为本地摘要：DS Pro 未就绪或未启用。"
        ),
        "scope_zh": "AI 只做研究解释、被拒原因总结和赛后学习提示，不改写概率、EV、候选筛选或可信度门控。",
    }


def _auto_execution_plan(requested: str, resolved: str, ds_completed: bool, llm_status: dict) -> dict:
    auto_mode = str(requested or "").strip().lower() == "auto"
    return {
        "mode": "auto_ds_pro" if auto_mode else str(requested or "local"),
        "steps": [
            {
                "name": "读取 T+1 可售比赛",
                "status": "done",
                "message_zh": "由首页 next-available 流程自动选择今日/明日/未来 1-3 天可售比赛。",
            },
            {
                "name": "本地概率与组合纪律",
                "status": "done",
                "message_zh": "Poisson/xG、赔率去水、可信度门控、冷门惩罚和串关联动先在本地完成。",
            },
            {
                "name": "DS Pro 研究解释",
                "status": "done" if ds_completed else "fallback",
                "message_zh": (
                    "DeepSeek Pro 已参与解释、质检和复盘摘要。"
                    if ds_completed
                    else f"DS Pro 未参与或未完成，当前状态：{llm_status.get('status', 'unknown')}；已回退本地摘要。"
                ),
            },
            {
                "name": "本地学习记录",
                "status": "done",
                "message_zh": "研究摘要会保存到浏览器本地记录，方便赛后对照，但不会上传或写入真实交易计划。",
            },
        ],
        "will_consume_tokens": resolved == "deepseek",
        "token_policy_zh": "只有 auto 解析为 DeepSeek Pro 且 key 可用时才消耗 token；否则不消耗 token。",
    }


def _fallback_warning(requested: str, llm_status: dict) -> str:
    if str(requested or "").lower() == "auto":
        return "auto AI 研究未调用 DeepSeek Pro，已使用本地研究摘要。"
    return "AI 研究层未执行或未就绪，已使用本地研究摘要。"


def _research_packet(
    optimizer_result: dict,
    best_parlay: dict,
    board: dict,
    learning_history: dict,
    odds_learning: dict,
) -> dict:
    gate = best_parlay.get("credibility_gate") or optimizer_result.get("credibility_gate") or {}
    return {
        "task_zh": "判断今天是否存在可研究组合；如果没有，解释为什么不应强行组合。",
        "date": optimizer_result.get("date"),
        "selected_date": optimizer_result.get("selected_date") or optimizer_result.get("date"),
        "next_available_locked": bool(optimizer_result.get("next_available_locked")),
        "date_lock_zh": optimizer_result.get("date_lock_zh", ""),
        "provider_used": optimizer_result.get("provider_used"),
        "matches_analyzed": optimizer_result.get("matches_analyzed"),
        "risk_profile": optimizer_result.get("risk_profile"),
        "combo_gate": gate,
        "user_combo_board": _compact_board(board),
        "closing_line_review": _compact_closing_review(board.get("closing_line_review", {})),
        "best_single": _trim_candidate(best_parlay.get("best_single", {})),
        "best_2x1": _trim_candidate(best_parlay.get("best_2x1", {})),
        "best_3x1": _trim_candidate(best_parlay.get("best_3x1_if_allowed", {})),
        "daily_2x1_candidate": _trim_candidate(best_parlay.get("daily_2x1_candidate", {})),
        "daily_3x1_candidate": _trim_candidate(best_parlay.get("daily_3x1_candidate", {})),
        "best_risk_adjusted_combo": _trim_candidate(best_parlay.get("best_risk_adjusted_combo", {})),
        "nearest_rejected_combos": [_trim_candidate(row) for row in (best_parlay.get("rejected_combos") or [])[:3]],
        "learning_history_summary": {
            "settled_count": learning_history.get("settled_count"),
            "hit_rate": learning_history.get("hit_rate"),
            "brier_score": learning_history.get("brier_score"),
            "log_loss": learning_history.get("log_loss"),
            "daily_summary_zh": learning_history.get("latest_daily_summary_zh", ""),
            "window_summaries_zh": (learning_history.get("window_summaries_zh") or [])[:2],
            "calibration_bins": (learning_history.get("calibration_bins") or [])[:3],
            "bucket_rows": (learning_history.get("bucket_rows") or [])[:3],
            "lessons": (learning_history.get("lessons") or [])[:2],
        },
        "odds_learning_rules": (odds_learning.get("plain_language_rules") or [])[:4],
        "combo_learning_rules": (odds_learning.get("lightweight_learning_path") or [])[:4],
        "missing_signals": (optimizer_result.get("missing_signals") or [])[:8],
    }


def _local_summary(packet: dict) -> str:
    board = packet.get("user_combo_board", {}) or {}
    gate = packet.get("combo_gate", {}) or {}
    best2 = packet.get("best_2x1", {}) or {}
    daily2 = packet.get("daily_2x1_candidate", {}) or {}
    daily3 = packet.get("daily_3x1_candidate", {}) or {}
    best_single = packet.get("best_single", {}) or {}
    lines = [
        board.get("headline_zh") or "今日组合结论：先看单关，再看是否有合格 2串1。",
        board.get("user_verdict_zh") or gate.get("reason_zh") or "组合需要通过可信度、赔率覆盖、相关性和命中率纪律。",
        "优先单关：" + (best_single.get("match") or best_single.get("legs") or best_single.get("message_zh") or "暂无"),
        "每日 2串1候选：" + (daily2.get("legs") or best2.get("legs") or best2.get("message_zh") or best2.get("reject_reason") or "暂无"),
        "每日 3串1候选：" + (daily3.get("legs") or daily3.get("message_zh") or daily3.get("reject_reason") or "暂无"),
        "学习反馈：" + "；".join((packet.get("learning_history_summary") or {}).get("lessons", [])[:2]),
        "临场复核：" + ((packet.get("closing_line_review") or {}).get("downgrade_zh") or "临近开赛前复核赔率是否反向漂移。"),
        "AI 研究建议：不要只看高组合赔率，要先看盈亏线、校准概率、安全边际、缺失情报和被拒原因。",
    ]
    return "\n".join(line for line in lines if line.strip())


def _display_cards(packet: dict, ai_result: dict) -> list[dict]:
    board = packet.get("user_combo_board", {}) or {}
    gate = packet.get("combo_gate", {}) or {}
    history = packet.get("learning_history_summary", {}) or {}
    return [
        {
            "label": "组合结论",
            "value": board.get("headline_zh", "待评估"),
            "help": board.get("user_verdict_zh", gate.get("reason_zh", "先看单关，再判断组合。")),
        },
        {
            "label": "AI 状态",
            "value": ai_result.get("provider", "local"),
            "help": ai_result.get("status", "not_requested"),
        },
        {
            "label": "学习样本",
            "value": history.get("settled_count", 0),
            "help": f"Brier {history.get('brier_score', 'N/A')} / Log Loss {history.get('log_loss', 'N/A')}",
        },
        {
            "label": "下一步",
            "value": board.get("primary_action_zh", "查看观察信号"),
            "help": "auto 模式会自动调用 DeepSeek Pro；失败时回退本地摘要。",
        },
    ]


def _structured_notes(packet: dict, ai_result: dict, local_summary: str) -> dict:
    text = str(ai_result.get("text") or local_summary or "")
    best_single = packet.get("best_single") or {}
    daily2 = packet.get("daily_2x1_candidate") or packet.get("best_2x1") or {}
    daily3 = packet.get("daily_3x1_candidate") or packet.get("best_3x1") or {}
    rejected = packet.get("nearest_rejected_combos") or []
    board = packet.get("user_combo_board") or {}
    gate = packet.get("combo_gate") or {}
    missing = packet.get("missing_signals") or []
    return {
        "version": "structured_ai_research_notes_v0",
        "source": ai_result.get("provider", "local"),
        "status": ai_result.get("status", "unknown"),
        "single_notes": [
            {
                "target": best_single.get("match") or best_single.get("legs") or "Top 单关",
                "note_zh": _note_from_text(text, ["优先单关", "最强观察", "Top 单关"], _single_note(best_single, missing)),
                "usage_zh": "先看赔率是否覆盖校准概率，再等临场赔率、伤停和首发复核。",
            }
        ],
        "combo_notes": [
            {
                "target": daily2.get("legs") or "Top 2串1",
                "note_zh": _note_from_text(text, ["每日 2串1候选", "2串1", "组合纪律"], _combo_note(daily2, gate)),
                "usage_zh": "组合必须每一腿都过纪律；可信度不足时只做被拒复盘，不升级为强观察。",
            },
            {
                "target": daily3.get("legs") or "Top 3串1",
                "note_zh": _note_from_text(text, ["每日 3串1候选", "3串1"], _combo_note(daily3, gate, combo_type="3串1")),
                "usage_zh": "3串1 是最高波动纸面候选，默认更严格。",
            },
        ],
        "total_goals_notes": [
            {
                "target": "总进球",
                "note_zh": _note_from_text(text, ["总进球", "进球节奏", "节奏"], "总进球只用于判断比赛节奏；若官方赔率缺失，只看模型倾向，不计算 EV。"),
                "usage_zh": "更适合做节奏参考，不适合替代胜平负纪律。",
            }
        ],
        "score_notes": [
            {
                "target": "比分",
                "note_zh": _note_from_text(text, ["比分", "比分倾向"], "比分矩阵波动较高，只作倾向参考，不能当作强观察。"),
                "usage_zh": "用于理解 Poisson/xG + Dixon-Coles 的比分分布。",
            }
        ],
        "rejected_combo_notes": [
            {
                "target": row.get("legs") or row.get("match") or f"被拒组合 {index + 1}",
                "note_zh": row.get("reject_reason") or row.get("discipline_summary_zh") or "未通过可信度、相关性、赔率覆盖或风险纪律。",
                "usage_zh": "赛后学习时要记录这些被拒组合是否真的命中，用于判断规则是否过严。",
            }
            for index, row in enumerate(rejected[:5])
        ],
        "match_notes": _match_notes(packet, text, missing),
        "daily_summary_zh": board.get("headline_zh") or gate.get("reason_zh") or _note_from_text(text, ["核心结论", "今日结论"], "先看单关，不强行组合。"),
        "missing_review_zh": _missing_note(missing),
    }


def _merge_ds_structured_notes(base: dict, text: object, packet: dict) -> dict:
    ds_payloads = _extract_structured_notes_json_list(text)
    if not ds_payloads:
        base["structured_source"] = "local_fallback"
        base["ds_structured_status"] = "not_found"
        base["quality_audit"] = _structured_quality_audit(base, packet)
        return base
    merged = dict(base)
    for ds_notes in ds_payloads:
        for key in (
            "daily_summary_zh",
            "missing_review_zh",
            "single_notes",
            "combo_notes",
            "total_goals_notes",
            "score_notes",
            "rejected_combo_notes",
            "match_notes",
        ):
            value = ds_notes.get(key)
            if _valid_structured_value(value):
                merged[key] = _sanitize_structured_value(value)
    merged["structured_source"] = "deepseek_structured"
    merged["ds_structured_status"] = "loaded"
    merged["quality_audit"] = _structured_quality_audit(merged, packet)
    return merged


def _structured_quality_audit(notes: dict, packet: dict) -> dict:
    required = ["single_notes", "combo_notes", "total_goals_notes", "score_notes", "match_notes"]
    coverage = {key: bool(notes.get(key)) for key in required}
    covered = sum(1 for value in coverage.values() if value)
    top_card_coverage = _top_card_coverage(notes, packet)
    source = notes.get("structured_source", "local_fallback")
    score = int(round((covered / len(required)) * 70))
    if source == "deepseek_structured":
        score += 20
    if notes.get("rejected_combo_notes"):
        score += 10
    if top_card_coverage["expected_count"]:
        missing_ratio = 1.0 - (top_card_coverage["matched_count"] / top_card_coverage["expected_count"])
        score -= int(round(missing_ratio * 20))
    score = max(0, min(100, score))
    return {
        "score": score,
        "grade": _quality_grade(score),
        "structured_source": source,
        "coverage": coverage,
        "top_card_coverage": top_card_coverage,
        "covered_count": covered,
        "required_count": len(required),
        "message_zh": _quality_message(score, source, coverage, top_card_coverage),
        "fallback_used": source != "deepseek_structured",
    }


def _top_card_coverage(notes: dict, packet: dict) -> dict:
    expected = _expected_top_targets(packet)
    note_keys = {_note_key(row.get("target")) for row in notes.get("match_notes", []) if isinstance(row, dict)}
    matched = []
    missing = []
    for target in expected:
        key = _note_key(target)
        if key and any(key in note_key or note_key in key for note_key in note_keys):
            matched.append(target)
        else:
            missing.append(target)
    return {
        "expected_count": len(expected),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "matched_targets": matched[:8],
        "missing_targets": missing[:8],
        "message_zh": (
            "AI 逐场笔记已覆盖全部 Top 卡片。"
            if expected and not missing
            else "部分 Top 卡片没有匹配到逐场 AI 笔记，页面会使用分类提示或本地解释兜底。"
            if expected
            else "当前没有可审计的 Top 卡片目标。"
        ),
    }


def _expected_top_targets(packet: dict) -> list[str]:
    items = [
        packet.get("best_single") or {},
        packet.get("daily_2x1_candidate") or packet.get("best_2x1") or {},
        packet.get("daily_3x1_candidate") or packet.get("best_3x1") or {},
        packet.get("best_risk_adjusted_combo") or {},
    ]
    items.extend((packet.get("nearest_rejected_combos") or [])[:3])
    targets: list[str] = []
    for item in items:
        target = item.get("match") or item.get("legs") or item.get("label_zh")
        if target and target not in targets:
            targets.append(str(target))
    return targets


def _quality_grade(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def _quality_message(score: int, source: str, coverage: dict, top_card_coverage: dict | None = None) -> str:
    missing = [key for key, ok in coverage.items() if not ok]
    if source != "deepseek_structured":
        return "DS 未返回可解析结构化研究块，本次使用本地结构化兜底；Top 卡片仍可显示解释，但 AI 覆盖质量较低。"
    if missing:
        return "DS 已返回结构化研究块，但仍缺少：" + "、".join(missing) + "；缺失部分使用本地兜底。"
    if top_card_coverage and top_card_coverage.get("missing_count"):
        return "DS 结构化研究可用，但部分 Top 卡片缺少逐场笔记；缺口会用分类提示或本地解释兜底。"
    if score >= 85:
        return "DS 结构化研究覆盖完整，已用于首页 Top 卡片提示。"
    return "DS 结构化研究可用，但仍建议赛后对照学习。"


def _extract_structured_notes_json(text: object) -> dict:
    payloads = _extract_structured_notes_json_list(text)
    return payloads[-1] if payloads else {}


def _extract_structured_notes_json_list(text: object) -> list[dict]:
    raw = str(text or "")
    marker = "STRUCTURED_NOTES_JSON:"
    if marker not in raw:
        return []
    decoder = json.JSONDecoder()
    payloads: list[dict] = []
    for after in raw.split(marker)[1:]:
        after = after.strip()
        start = after.find("{")
        if start < 0:
            continue
        candidate = after[start:]
        try:
            payload, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _valid_structured_value(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return False


def _sanitize_structured_value(value: object) -> object:
    if isinstance(value, str):
        return value.strip()[:600]
    if isinstance(value, list):
        return [_sanitize_note_row(row) for row in value[:8] if isinstance(row, dict)]
    return value


def _sanitize_note_row(row: dict) -> dict:
    allowed = {"target", "note_zh", "usage_zh", "type", "role_zh", "risk_level", "key", "missing_review_zh"}
    clean = {}
    for key, value in row.items():
        if key in allowed and value is not None:
            clean[key] = str(value).strip()[:500]
    if clean.get("target") and not clean.get("key"):
        clean["key"] = _note_key(clean.get("target"))
    return clean


def _note_from_text(text: str, patterns: list[str], fallback: str) -> str:
    lines = [line.replace("*", "").replace("#", "").replace("`", "").replace(">", "").strip() for line in str(text or "").splitlines()]
    lines = [line for line in lines if line]
    for pattern in patterns:
        for line in lines:
            if pattern in line:
                return line[:180]
    return fallback


def _single_note(item: dict, missing: list) -> str:
    target = item.get("match") or item.get("legs") or "Top 单关"
    risk = item.get("risk_level") or item.get("risk") or "待评估"
    if _is_longshot(item):
        return f"{target} 属于高赔率冷门观察，风险为 {risk}；可单独跟踪，不适合作为组合核心。"
    if missing:
        return f"{target} 可先观察，但仍要复核缺失情报和临场赔率。"
    return f"{target} 先看赔率覆盖、校准概率和临场复核，不直接升级为组合核心。"


def _combo_note(item: dict, gate: dict, combo_type: str = "2串1") -> str:
    if item.get("status") == "通过门控":
        return f"{combo_type} 已进入纸面观察，但仍要逐腿复核赔率、伤停、首发和天气。"
    reason = item.get("reject_reason") or item.get("message_zh") or gate.get("reason_zh")
    return reason or f"{combo_type} 当前未通过可信度、相关性、赔率覆盖或风险纪律，不强行组合。"


def _missing_note(missing: list) -> str:
    if not missing:
        return "当前没有新增缺失情报记录，但赛日前仍要复核首发、伤停、天气和赔率漂移。"
    cleaned = [str(item) for item in missing if item][:6]
    return "赛日前重点复核：" + "、".join(cleaned)


def _is_longshot(item: dict) -> bool:
    for key in ("odds", "official_odds", "combo_odds"):
        try:
            if float(item.get(key) or 0) >= 6:
                return True
        except (TypeError, ValueError):
            continue
    return str(item.get("risk_level") or "").lower() == "very_high"


def _match_notes(packet: dict, text: str, missing: list) -> list[dict]:
    notes: list[dict] = []
    sources = [
        ("single", packet.get("best_single") or {}),
        ("combo_2x1", packet.get("daily_2x1_candidate") or packet.get("best_2x1") or {}),
        ("combo_3x1", packet.get("daily_3x1_candidate") or packet.get("best_3x1") or {}),
        ("risk_adjusted_combo", packet.get("best_risk_adjusted_combo") or {}),
    ]
    for note_type, item in sources:
        if item:
            notes.append(_match_note_from_item(note_type, item, text, missing))
    for index, item in enumerate((packet.get("nearest_rejected_combos") or [])[:5]):
        notes.append(_match_note_from_item("rejected_combo", item, text, missing, index=index))
    unique: dict[str, dict] = {}
    for note in notes:
        key = note.get("key") or note.get("target") or str(len(unique))
        unique[key] = note
    return list(unique.values())


def _match_note_from_item(note_type: str, item: dict, text: str, missing: list, index: int = 0) -> dict:
    target = item.get("match") or item.get("legs") or item.get("label_zh") or f"观察项 {index + 1}"
    key = _note_key(target)
    risk = item.get("risk_level") or item.get("risk") or "待评估"
    reason = item.get("reject_reason") or item.get("discipline_summary_zh") or item.get("decision_reason_zh") or item.get("message_zh")
    if note_type == "single":
        note = _note_from_text(text, [target, "优先单关", "最强观察"], _single_note(item, missing))
        role = "单关观察"
    elif note_type.startswith("combo") or note_type == "risk_adjusted_combo":
        note = _note_from_text(text, [target, "组合纪律", "2串1", "3串1"], reason or _combo_note(item, {}, combo_type="组合"))
        role = "组合观察"
    else:
        note = reason or "该组合未通过纪律，适合进入赛后被拒复盘。"
        role = "被拒组合"
    return {
        "key": key,
        "target": target,
        "type": note_type,
        "role_zh": role,
        "risk_level": risk,
        "note_zh": note,
        "usage_zh": _usage_for_note_type(note_type),
        "missing_review_zh": _missing_note(missing),
    }


def _usage_for_note_type(note_type: str) -> str:
    if note_type == "single":
        return "单关先看赔率覆盖和临场复核，不自动升级为组合核心。"
    if note_type == "rejected_combo":
        return "被拒组合用于赛后复盘规则是否过严，不代表当前应强行放开。"
    return "组合需要逐腿通过纪律、相关性、可信度和情报复核。"


def _note_key(text: object) -> str:
    raw = str(text or "").strip().lower()
    compact = "".join(ch for ch in raw if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")
    return compact[:80] or "note"


def _token_budget(packet: dict, llm_status: dict) -> dict:
    raw = json.dumps(packet, ensure_ascii=False, sort_keys=True, default=str)
    estimated_input_tokens = max(1, int(len(raw) / 3.2))
    max_output_tokens = int(llm_status.get("max_output_tokens") or 800)
    max_input_tokens = int(llm_status.get("max_input_tokens") or 6000)
    clipped = estimated_input_tokens > max_input_tokens
    cache_key = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return {
        "estimated_input_tokens": estimated_input_tokens,
        "max_output_tokens": max_output_tokens,
        "estimated_max_total_tokens": min(estimated_input_tokens, max_input_tokens) + max_output_tokens,
        "max_input_tokens": max_input_tokens,
        "input_would_be_clipped": clipped,
        "research_cache_key": cache_key,
        "cost_control_zh": "本地先生成研究包；auto 模式会自动调用 DeepSeek Pro 做解释层分析。相同 cache key 可用于复盘同一次研究口径。",
    }

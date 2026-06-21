from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.api.routes import dispatch_route
from src.qa.checks import QaCheckResult, results_to_dicts, summarize_checks

FORBIDDEN_BUTTON_TEXT = [
    "下注",
    "投注",
    "购买",
    "下单",
    "支付",
    "代购",
    "跟单",
    "自动投注",
    "追号",
    "倍投",
    "回血",
    "必中",
    "稳赢",
    "稳赚",
    "杀庄",
    "保本",
]


def run_strict_trader_audit(project_root: str = ".") -> dict[str, Any]:
    root = Path(project_root)
    html_path = root / "src/dashboard/static/index.html"
    js_path = root / "src/dashboard/static/app.js"
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    js = js_path.read_text(encoding="utf-8") if js_path.exists() else ""
    combined = html + "\n" + js

    checks: list[QaCheckResult] = []
    endpoint_payloads = {}
    endpoint_specs = {
        "next_available": ("/api/view/next-available", {"provider": "auto", "bankroll": "10000", "risk_profile": "aggressive"}),
        "matches": ("/api/view/matches", {"provider": "auto", "date": "2026-06-10"}),
        "intelligence": ("/api/view/intelligence", {"provider": "auto", "date": "2026-06-10"}),
        "intelligence_external": ("/api/view/intelligence", {"provider": "mock", "date": "2026-06-10", "external_signals": "data/fixtures/external_signals_mock_20260610.json"}),
        "optimizer_aggressive": ("/api/view/optimizer", {"provider": "auto", "date": "2026-06-10", "bankroll": "10000", "risk_profile": "aggressive"}),
        "score_goals": ("/api/view/score-goals", {"provider": "auto", "date": "2026-06-10"}),
        "llm_status": ("/api/llm/status", {}),
        "learning_history": ("/api/view/learning-history", {}),
        "user_workflow": ("/api/view/user-workflow", {"input": "data/fixtures/user_onboarding_sample.csv", "mapping": "data/fixtures/user_onboarding_mapping_example.json"}),
        "operation_simulate": ("/api/view/operation", {"historical_data": "data/fixtures/operation_walkforward_sample.csv", "initial_bankroll": "10000"}),
        "qa": ("/api/view/qa", {}),
    }
    for name, (path, query) in endpoint_specs.items():
        try:
            payload = dispatch_route(path, query)
            endpoint_payloads[name] = payload
            checks.append(QaCheckResult(f"audit.endpoint.{name}", bool(payload.get("ok")), message=f"{name} endpoint returns ok envelope"))
        except Exception as exc:  # noqa: BLE001 - audit must report cleanly
            endpoint_payloads[name] = {"ok": False, "error": str(exc).splitlines()[0][:180]}
            checks.append(QaCheckResult(f"audit.endpoint.{name}", False, message=f"{name} endpoint failed cleanly", details={"error": str(exc).splitlines()[0][:180]}))

    checks.extend(_static_checks(html, combined))
    acceptance_checks = _acceptance_checks(html, combined, endpoint_payloads)
    checks.extend(acceptance_checks)
    phase3_readiness = _phase3_readiness(html, combined, endpoint_payloads)
    source_flags = _source_flags(root)
    goal_readiness = _goal_readiness(html, combined, endpoint_payloads, acceptance_checks, source_flags)
    summary = summarize_checks(checks)
    findings = [
        {"name": c.name, "message": c.message, "details": c.details}
        for c in checks
        if not c.passed
    ]
    return {
        "audit_version": "phase2o_strict_trader_audit_v0",
        "overall_passed": summary["overall_passed"],
        "summary": summary,
        "checks": results_to_dicts(checks),
        "acceptance_summary": summarize_checks(acceptance_checks),
        "acceptance_criteria": results_to_dicts(acceptance_checks),
        "phase3_summary": _phase3_summary(phase3_readiness),
        "phase3_readiness": phase3_readiness,
        "goal_summary": _goal_summary(goal_readiness),
        "goal_readiness": goal_readiness,
        "endpoint_summary": _endpoint_summary(endpoint_payloads),
        "findings": findings,
        "fix_suggestions": _fix_suggestions(findings),
        "disclaimer": "严厉交易者审计只检查观察信号、纸面模拟和风险诊断，不构成投注建议。",
    }


def _static_checks(html: str, combined: str) -> list[QaCheckResult]:
    checks = [
        QaCheckResult("audit.home.today_observation", "今日观察" in html, message="首页包含今日观察"),
        QaCheckResult("audit.home.top_singles", "Top 单关观察" in html, message="首页包含 Top 单关观察"),
        QaCheckResult("audit.home.top_parlay", "Top 2串1观察" in html, message="首页包含 Top 2串1观察"),
        QaCheckResult("audit.home.top_total_goals", "Top 总进球观察" in html, message="首页包含 Top 总进球观察"),
        QaCheckResult("audit.home.top_scores", "Top 比分观察" in html, message="首页包含 Top 比分观察"),
        QaCheckResult("audit.home.advanced_closed", "<details id=\"advancedSettings\"" in html and "<details id=\"advancedSettings\" open" not in html, message="高级设置默认关闭"),
        QaCheckResult("audit.home.no_visible_operation_panel", "操作面板" not in html and "sidebar" not in html, message="首页没有默认技术操作面板"),
        QaCheckResult("audit.home.no_api_base_label", "API Base" not in html, message="首页不显示 API Base 文案"),
        QaCheckResult(
            "audit.ai.auto_research_default",
            "auto：自动跑 DS Pro" in html and 'return mode === "auto" ? "auto" : mode' in combined,
            message="AI 研究模式默认 auto，前端保留 auto 交给后端解析，而不是硬编码为 DeepSeek。",
        ),
    ]
    for label in FORBIDDEN_BUTTON_TEXT:
        checks.append(
            QaCheckResult(
                f"audit.button.{label}",
                f">{label}<" not in combined and f">{label} " not in combined,
                message=f"没有 {label} 正向按钮",
            )
        )
    return checks


def _acceptance_checks(html: str, combined: str, payloads: dict[str, dict]) -> list[QaCheckResult]:
    next_available = _payload_data(payloads, "next_available")
    optimizer = _payload_data(payloads, "optimizer_aggressive")
    score_goals = _payload_data(payloads, "score_goals")
    operation = _payload_data(payloads, "operation_simulate")
    llm_status = _payload_data(payloads, "llm_status")
    learning_history = _payload_data(payloads, "learning_history")
    ai_research = optimizer.get("ai_combo_research") if isinstance(optimizer.get("ai_combo_research"), dict) else {}
    gate = optimizer.get("credibility_gate") if isinstance(optimizer.get("credibility_gate"), dict) else {}
    best_parlay = optimizer.get("best_parlay_summary") if isinstance(optimizer.get("best_parlay_summary"), dict) else {}

    matches_count = _safe_int(next_available.get("matches_count"))
    provider_used = str(next_available.get("provider_used") or "")
    data_source_status = next_available.get("data_source_status")
    observation_rows = _collect_observation_rows(next_available) or _collect_observation_rows(optimizer)
    rejected_combo_rows = _collect_rejected_combo_rows(optimizer)
    profit_notes = operation.get("profit_explanation") or []
    disclaimers_blob = _stringify([next_available, optimizer, score_goals, operation])
    best_risk_adjusted = best_parlay.get("best_risk_adjusted_combo") if isinstance(best_parlay.get("best_risk_adjusted_combo"), dict) else {}
    best_parlay_final_status = (
        ((best_risk_adjusted.get("best_parlay_quality") or {}).get("final_status"))
        or best_risk_adjusted.get("status")
        or best_parlay.get("status")
        or ""
    )

    no_forbidden_buttons = all(
        f">{label}<" not in combined and f">{label} " not in combined
        for label in FORBIDDEN_BUTTON_TEXT
    )
    score_rows = (score_goals.get("score_table") or []) + (score_goals.get("top_scores") or [])
    total_goal_rows = score_goals.get("total_goals_table") or []
    long_run_score = next_available.get("long_run_score") if isinstance(next_available.get("long_run_score"), dict) else {}
    score_roadmap = long_run_score.get("score_roadmap") if isinstance(long_run_score.get("score_roadmap"), list) else []

    return [
        QaCheckResult(
            "acceptance.01_today_observation_default",
            bool(next_available) and "今日观察" in html,
            message="App 默认进入今日观察，并能取得 next-available 预览。",
            details={"selected_date": next_available.get("selected_date"), "matches_count": matches_count},
        ),
        QaCheckResult(
            "acceptance.02_no_visible_technical_controls",
            "<details id=\"advancedSettings\"" in html and "<details id=\"advancedSettings\" open" not in html and "API Base" not in html and "操作面板" not in html,
            message="首页不默认展示 API Base、Provider、路径输入等技术操作面板。",
        ),
        QaCheckResult(
            "acceptance.03_top_observations_visible",
            all(text in html for text in ["Top 单关观察", "Top 2串1观察", "Top 总进球观察", "Top 比分观察"]) and matches_count is not None,
            message="首页展示可售比赛数与 Top 单关、2串1、总进球、比分观察入口。",
            details={"matches_count": matches_count},
        ),
        QaCheckResult(
            "acceptance.04_no_transaction_controls",
            no_forbidden_buttons,
            message="App 没有投注、支付、下单、代购等正向操作按钮。",
        ),
        QaCheckResult(
            "acceptance.05_sporttery_success_or_calm_fallback",
            (provider_used == "sporttery" and (matches_count or 0) > 0) or isinstance(data_source_status, dict),
            message="Sporttery 成功时展示真实比赛；不可用时保留平静的数据源状态说明。",
            details={"provider_used": provider_used, "matches_count": matches_count},
        ),
        QaCheckResult(
            "acceptance.06_datasource_status_no_crash",
            bool(payloads.get("next_available", {}).get("ok")) and isinstance(data_source_status, dict),
            message="数据源失败或回退时不崩溃，并返回 data_source_status。",
        ),
        QaCheckResult(
            "acceptance.07_observations_have_discipline_context",
            bool(observation_rows)
            and all(_has_any(row, ["selection_reason", "通过门控原因", "reason", "selected_reason"]) for row in observation_rows[:8])
            and all(label in combined for label in ["支持因素", "反对因素", "缺失情报"]),
            message="观察项包含并展示通过门控原因、反对因素和缺失情报等严厉交易者上下文。",
            details={"checked_rows": min(len(observation_rows), 8), "total_rows": len(observation_rows)},
        ),
        QaCheckResult(
            "acceptance.08_rejected_combos_have_reasons",
            bool(rejected_combo_rows)
            and all(_has_any(row, ["reject_reason", "rejected_reason", "拒绝原因", "reason"]) for row in rejected_combo_rows[:12])
            and "Top 2串1被拒原因" in html
            and "Top 3串1被拒原因" in html,
            message="被拒绝的 2串1/3串1 组合包含拒绝原因，并在今日观察首页展示。",
            details={"checked_rows": min(len(rejected_combo_rows), 12), "total_rows": len(rejected_combo_rows)},
        ),
        QaCheckResult(
            "acceptance.09_operation_profit_explained",
            bool(profit_notes),
            message="模拟走盘解释为什么赚/亏，并区分本金收益率与模拟投入 ROI。",
            details={"notes_count": len(profit_notes) if isinstance(profit_notes, list) else 1},
        ),
        QaCheckResult(
            "acceptance.10_model_outputs_are_not_guarantees",
            ("不代表未来表现" in disclaimers_blob or "不保证" in disclaimers_blob) and ("不构成" in disclaimers_blob or "纸面" in disclaimers_blob) and bool(score_rows) and bool(total_goal_rows),
            message="模型输出包含非保证声明，并展示比分 Top 与总进球概率。",
            details={"score_rows": len(score_rows), "total_goal_rows": len(total_goal_rows)},
        ),
        QaCheckResult(
            "acceptance.11_long_run_score_roadmap",
            bool(score_roadmap)
            and "下一步优先级" in combined
            and all(_safe_int(row.get("score")) is not None and _safe_int(row.get("score")) < 90 for row in score_roadmap)
            and all(bool(row.get("next")) for row in score_roadmap),
            message="Long-run score 输出可执行路线图，且不把满分项列为待办。",
            details={
                "roadmap_count": len(score_roadmap),
                "roadmap": [
                    {"label": row.get("label"), "score": row.get("score"), "next": row.get("next")}
                    for row in score_roadmap
                ],
            },
        ),
        QaCheckResult(
            "acceptance.12_ai_telemetry_unified",
            bool(ai_research)
            and all(key in ai_research for key in ["ds_status", "ds_attempted", "ds_completed", "ds_error_code", "fallback_reason", "token_in", "token_out", "token_total"])
            and all(key in llm_status for key in ["runtime_status", "runtime_status_zh", "ds_attempted", "ds_completed", "ds_error_code", "last_token_total", "status_detail_zh"]),
            message="AI 研究和 LLM 状态统一返回 DS telemetry、fallback 原因和 token 消耗。",
            details={
                "ai_ds_status": ai_research.get("ds_status"),
                "ai_fallback_reason": ai_research.get("fallback_reason"),
                "ai_token_total": ai_research.get("token_total"),
                "llm_runtime_status": llm_status.get("runtime_status"),
                "llm_status_detail": llm_status.get("status_detail_zh"),
            },
        ),
        QaCheckResult(
            "acceptance.13_learning_metrics_returned",
            isinstance(learning_history.get("daily_metrics"), list)
            and isinstance(learning_history.get("window_metrics"), list)
            and isinstance(next_available.get("daily_learning_metrics"), list)
            and isinstance(next_available.get("window_learning_metrics"), list)
            and bool(learning_history.get("latest_daily_summary_zh")),
            message="学习闭环返回今日和区间指标，首页视图也能透传这些指标。",
            details={
                "daily_metric_rows": len(learning_history.get("daily_metrics") or []),
                "window_metric_rows": len(learning_history.get("window_metrics") or []),
                "next_available_daily_rows": len(next_available.get("daily_learning_metrics") or []),
                "next_available_window_rows": len(next_available.get("window_learning_metrics") or []),
            },
        ),
        QaCheckResult(
            "acceptance.14_combo_gate_explicit",
            gate.get("combo_gate") in {"closed", "restricted", "open"}
            and bool(optimizer.get("no_combo_reason") or best_parlay.get("no_combo_reason"))
            and best_parlay_final_status in {"selected", "rejected", "no_combo", "daily_candidate"},
            message="串联纪律固定返回 combo_gate、no_combo_reason 和 best_parlay final_status。",
            details={
                "combo_gate": gate.get("combo_gate"),
                "no_combo_reason": optimizer.get("no_combo_reason") or best_parlay.get("no_combo_reason"),
                "best_parlay_final_status": best_parlay_final_status,
            },
        ),
        QaCheckResult(
            "acceptance.15_learning_digests_present",
            isinstance(learning_history.get("daily_digest"), dict)
            and bool((learning_history.get("daily_digest") or {}).get("summary_zh"))
            and bool((learning_history.get("daily_digest") or {}).get("next_step_zh"))
            and isinstance(learning_history.get("window_digests"), list)
            and isinstance(next_available.get("daily_learning_digest"), dict)
            and bool((next_available.get("daily_learning_digest") or {}).get("summary_zh"))
            and isinstance(next_available.get("window_learning_digests"), list),
            message="学习闭环除了原始指标，还会返回今日/区间复盘摘要和下一步动作。",
            details={
                "daily_digest_headline": (learning_history.get("daily_digest") or {}).get("headline_zh"),
                "window_digest_count": len(learning_history.get("window_digests") or []),
                "next_available_digest_headline": (next_available.get("daily_learning_digest") or {}).get("headline_zh"),
            },
        ),
        QaCheckResult(
            "acceptance.16_llm_guidance_present",
            all(key in llm_status for key in ["config_status_zh", "runtime_notice_zh", "next_step_zh"])
            and all(key in (next_available.get("ai_research_layer") or {}) for key in ["config_status_zh", "runtime_notice_zh", "next_step_zh"])
            and "配置：" in combined
            and "学习结论：" in combined,
            message="DS 状态会返回配置状态、本轮状态和下一步动作，首页也保留学习结论提示。",
            details={
                "config_status_zh": llm_status.get("config_status_zh"),
                "runtime_notice_zh": llm_status.get("runtime_notice_zh"),
                "next_step_zh": llm_status.get("next_step_zh"),
            },
        ),
        QaCheckResult(
            "acceptance.17_learning_reports_present",
            isinstance(learning_history.get("daily_report"), dict)
            and bool((learning_history.get("daily_report") or {}).get("headline_zh"))
            and bool((learning_history.get("daily_report") or {}).get("paragraphs_zh"))
            and isinstance(learning_history.get("window_reports"), list)
            and isinstance(next_available.get("daily_learning_report"), dict)
            and bool((next_available.get("daily_learning_report") or {}).get("headline_zh"))
            and isinstance(next_available.get("window_learning_reports"), list),
            message="学习闭环固定返回今日/区间复盘段落，前端可直接渲染日报而不必自己拼字段。",
            details={
                "daily_report_headline": (learning_history.get("daily_report") or {}).get("headline_zh"),
                "daily_report_paragraphs": len((learning_history.get("daily_report") or {}).get("paragraphs_zh") or []),
                "window_report_count": len(learning_history.get("window_reports") or []),
                "next_available_daily_report_headline": (next_available.get("daily_learning_report") or {}).get("headline_zh"),
            },
        ),
    ]


def _phase3_readiness(html: str, combined: str, payloads: dict[str, dict]) -> list[dict[str, Any]]:
    next_available = _payload_data(payloads, "next_available")
    matches = _payload_data(payloads, "matches")
    intelligence = _payload_data(payloads, "intelligence")
    intelligence_external = _payload_data(payloads, "intelligence_external")
    external_signal_status = intelligence_external.get("external_signals_status") if isinstance(intelligence_external.get("external_signals_status"), dict) else {}
    optimizer = _payload_data(payloads, "optimizer_aggressive")
    score_goals = _payload_data(payloads, "score_goals")
    user_workflow = _payload_data(payloads, "user_workflow")

    matches_count = _safe_int(next_available.get("matches_count"))
    data_source_status = next_available.get("data_source_status")
    source_health = next_available.get("source_health") if isinstance(next_available.get("source_health"), dict) else {}
    scan_window = source_health.get("scan_window") if isinstance(source_health.get("scan_window"), dict) else {}
    missing_signals = _collect_missing_signals(next_available, intelligence, optimizer, score_goals)
    signal_keys = _collect_signal_keys(next_available, intelligence)
    intelligence_gap_actions = intelligence.get("intelligence_gap_actions") or []
    connected_external_keys = _collect_connected_signal_keys(intelligence_external)
    rejected_combo_rows = _collect_rejected_combo_rows(optimizer)
    user_steps = user_workflow.get("steps") or []
    user_readiness = user_workflow.get("readiness_table") or []
    user_preflight = user_workflow.get("preflight_quality") if isinstance(user_workflow.get("preflight_quality"), dict) else {}
    user_preflight_checks = user_workflow.get("preflight_checks") or []
    user_cli_handoff = user_workflow.get("cli_handoff") if isinstance(user_workflow.get("cli_handoff"), dict) else {}
    user_replay_readiness = user_workflow.get("replay_readiness_summary") if isinstance(user_workflow.get("replay_readiness_summary"), dict) else {}
    user_has_backtest_context = bool(user_workflow.get("backtest_explanation") or user_workflow.get("workflow_summary"))
    score_integrity = score_goals.get("probability_integrity") or []

    return [
        _phase_item(
            "Phase 3-A",
            "首页极简化与今日观察",
            ready="今日观察" in html and "API Base" not in html and "<details id=\"advancedSettings\" open" not in html,
            evidence=[
                "首页包含今日观察",
                "高级设置 details 存在且默认关闭",
                "首页未出现 API Base 文案",
            ],
            gaps=[],
        ),
        _phase_item(
            "Phase 3-B",
            "Sporttery 自动拉取与数据源状态",
            ready=bool(payloads.get("next_available", {}).get("ok")) and matches_count is not None and isinstance(data_source_status, dict) and bool(source_health) and bool(scan_window.get("complete")),
            evidence=[
                f"selected_date={next_available.get('selected_date')}",
                f"matches_count={matches_count}",
                f"provider_used={next_available.get('provider_used')}",
                f"source_health={source_health.get('health')}",
                f"source_reliability={source_health.get('reliability_label_zh')}:{source_health.get('reliability_score')}",
                f"all_attempts_stable={source_health.get('all_attempts_stable')}",
                f"scan_window={scan_window.get('start_date')}..{scan_window.get('end_date')}",
                f"scan_complete={scan_window.get('complete')}",
                f"days_checked={scan_window.get('days_checked')}",
                f"scanned_dates={', '.join(source_health.get('scanned_dates') or [])}",
                f"successful_attempts={source_health.get('successful_attempts')}/{source_health.get('attempt_count')}",
                f"sporttery_attempts={source_health.get('sporttery_attempts')}",
                f"fallback_attempts={source_health.get('fallback_attempts')}",
                f"empty_attempts={source_health.get('empty_attempts')}",
                f"warning_attempts={source_health.get('warning_attempts')}",
                f"matches_table_rows={len(matches.get('matches_table') or [])}",
                "外部接口仍可能受网络、证书或接口变更影响；App 已显示可靠性评级和回退状态。",
            ],
            gaps=[],
        ),
        _phase_item(
            "Phase 3-C",
            "赛前情报融合接口与缺失情报展示",
            ready=bool(missing_signals) and _signals_mark_unknown(intelligence) and {"schedule", "travel"}.issubset(set(signal_keys)) and bool(connected_external_keys) and external_signal_status.get("source_type") == "user_json",
            evidence=[
                f"missing_signals={', '.join(missing_signals) if missing_signals else 'none'}",
                f"signal_status_keys={', '.join(signal_keys) if signal_keys else 'none'}",
                f"intelligence_gap_actions={len(intelligence_gap_actions)}",
                f"gap_action_status={_readiness_status_counts(intelligence_gap_actions)}",
                f"external_signal_connected={', '.join(connected_external_keys) if connected_external_keys else 'none'}",
                f"external_signal_source={external_signal_status.get('source_type')}",
                f"external_signal_load_status={external_signal_status.get('load_status')}",
                f"external_signal_invalid_items={external_signal_status.get('invalid_items')}",
                f"external_signal_coverage={external_signal_status.get('matched_count')}/{external_signal_status.get('matches_count')}",
                "新闻、伤停、首发、天气等未接入时显示 not_connected / unknown",
                "真实新闻、伤停、首发、天气源不默认联网抓取；当前只读取用户提供的本地结构化 JSON。",
            ],
            gaps=[],
        ),
        _phase_item(
            "Phase 3-D",
            "比分/总进球/让球概率矩阵",
            ready=bool(score_goals.get("score_table")) and bool(score_goals.get("total_goals_table")) and bool(score_goals.get("handicap_table")) and bool(score_integrity) and all(row.get("status") == "pass" for row in score_integrity if isinstance(row, dict)),
            evidence=[
                f"score_rows={len(score_goals.get('score_table') or [])}",
                f"total_goal_rows={len(score_goals.get('total_goals_table') or [])}",
                f"handicap_rows={len(score_goals.get('handicap_table') or [])}",
                f"integrity_rows={len(score_integrity)}",
                f"integrity_status={_readiness_status_counts(score_integrity)}",
            ],
            gaps=[],
        ),
        _phase_item(
            "Phase 3-E",
            "用户历史 CSV 回测与模型校准",
            ready=bool(user_steps) and bool(user_readiness) and bool(user_preflight_checks) and bool(user_cli_handoff.get("command")) and user_has_backtest_context,
            evidence=[
                f"user_workflow_steps={len(user_steps)}",
                f"user_readiness_items={len(user_readiness)}",
                f"user_readiness_status={_readiness_status_counts(user_readiness)}",
                f"preflight_checks={len(user_preflight_checks)}",
                f"rows_normalized={user_preflight.get('rows_normalized')}",
                f"had_odds_coverage={user_preflight.get('had_odds_coverage')}",
                f"replay_readiness={user_replay_readiness.get('label')}:{user_replay_readiness.get('score')}",
                f"calibration_status={user_replay_readiness.get('calibration_status')}",
                f"cli_handoff_mode={user_cli_handoff.get('mode')}",
                f"cli_handoff_outputs={len(user_cli_handoff.get('expected_outputs') or [])}",
                "用户 CSV 预检、字段修复、回测解释和校准说明已进入只读视图",
                "真实用户 CSV 的效果取决于数据质量；完整写文件 workflow 保持 CLI-only。",
            ],
            gaps=[],
        ),
        _phase_item(
            "Phase 3-F",
            "组合优化器展示被拒组合和原因",
            ready=bool(rejected_combo_rows) and all(_has_any(row, ["reject_reason", "rejected_reason", "拒绝原因", "reason"]) for row in rejected_combo_rows[:12]),
            evidence=[
                f"rejected_combo_rows={len(rejected_combo_rows)}",
                "2串1/3串1 候选排行榜包含被拒原因",
            ],
            gaps=[],
        ),
    ]


def _phase_item(phase: str, title: str, ready: bool, evidence: list[str], gaps: list[str]) -> dict[str, Any]:
    status = "ready" if ready and not gaps else "partial" if ready else "needs_work"
    return {
        "phase": phase,
        "title": title,
        "status": status,
        "ready": ready,
        "evidence": evidence,
        "remaining_gaps": gaps,
    }


def _phase3_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"ready": 0, "partial": 0, "needs_work": 0}
    for item in items:
        status = str(item.get("status") or "needs_work")
        counts[status] = counts.get(status, 0) + 1
    return {"total": len(items), **counts, "overall_ready": counts.get("needs_work", 0) == 0 and counts.get("partial", 0) == 0}


def _goal_readiness(
    html: str,
    combined: str,
    payloads: dict[str, dict],
    acceptance_checks: list[QaCheckResult],
    source_flags: dict[str, bool],
) -> list[dict[str, Any]]:
    next_available = _payload_data(payloads, "next_available")
    matches = _payload_data(payloads, "matches")
    intelligence = _payload_data(payloads, "intelligence")
    optimizer = _payload_data(payloads, "optimizer_aggressive")
    score_goals = _payload_data(payloads, "score_goals")
    user_workflow = _payload_data(payloads, "user_workflow")
    operation = _payload_data(payloads, "operation_simulate")

    source_health = next_available.get("source_health") if isinstance(next_available.get("source_health"), dict) else {}
    scan_window = source_health.get("scan_window") if isinstance(source_health.get("scan_window"), dict) else {}
    observation_rows = _collect_observation_rows(next_available) or _collect_observation_rows(optimizer)
    rejected_combo_rows = _collect_rejected_combo_rows(optimizer)
    missing_signals = _collect_missing_signals(next_available, intelligence, optimizer, score_goals)
    signal_keys = set(_collect_signal_keys(next_available, intelligence))
    score_integrity = score_goals.get("probability_integrity") or []
    operation_entry = next_available.get("operation_entry") if isinstance(next_available.get("operation_entry"), dict) else {}
    user_replay = user_workflow.get("replay_readiness_summary") if isinstance(user_workflow.get("replay_readiness_summary"), dict) else {}
    no_forbidden_buttons = all(f">{label}<" not in combined and f">{label} " not in combined for label in FORBIDDEN_BUTTON_TEXT)
    disclaimer_blob = _stringify([next_available, optimizer, score_goals, operation])

    items = [
        _goal_item(
            "产品原则",
            "首页不是操作面板，而是今日观察",
            "今日观察" in html and "操作面板" not in html and "sidebar" not in html,
            ["首页包含今日观察", "首页没有默认操作面板"],
        ),
        _goal_item(
            "产品原则",
            "打开 App 自动拉取 Sporttery 可售比赛",
            bool(payloads.get("next_available", {}).get("ok")) and bool(scan_window.get("complete")),
            [f"selected_date={next_available.get('selected_date')}", f"provider_used={next_available.get('provider_used')}", f"scan_complete={scan_window.get('complete')}"],
        ),
        _goal_item(
            "产品原则",
            "默认隐藏 API Base、provider、路径、风险参数",
            "<details id=\"advancedSettings\"" in html and "<details id=\"advancedSettings\" open" not in html and "API Base" not in html,
            ["高级设置 details 存在且默认关闭", "首页不显示 API Base 文案"],
        ),
        _goal_item(
            "产品原则",
            "默认 risk profile 使用 aggressive，且只用于纸面观察",
            optimizer.get("risk_profile") == "aggressive" and "纸面" in disclaimer_blob,
            [f"optimizer_risk_profile={optimizer.get('risk_profile')}", "输出包含纸面模拟/观察语义"],
        ),
        _goal_item(
            "产品原则",
            "所有高级参数放进折叠面板",
            "<details id=\"advancedSettings\"" in html and "<details id=\"advancedSettings\" open" not in html,
            ["高级设置默认关闭"],
        ),
        _goal_item(
            "产品原则",
            "功能围绕比赛、观察价值、原因、风险、拒绝原因和回测表现",
            bool(next_available.get("matches_count") is not None)
            and bool(observation_rows)
            and bool(rejected_combo_rows)
            and bool(operation_entry.get("metrics")),
            [
                f"matches_count={next_available.get('matches_count')}",
                f"observation_rows={len(observation_rows)}",
                f"rejected_combo_rows={len(rejected_combo_rows)}",
                f"operation_entry_metrics={len(operation_entry.get('metrics') or [])}",
            ],
        ),
        _goal_item(
            "产品原则",
            "不提供投注、下单、支付、代购或自动化购彩能力",
            no_forbidden_buttons and ("不提供" in combined or "不构成" in disclaimer_blob),
            ["无正向交易按钮", "页面/输出包含非交易声明"],
        ),
        _goal_item(
            "技术目标",
            "稳定 Sporttery 数据源并显示状态",
            bool(source_health.get("health")) and source_health.get("reliability_score") is not None,
            [f"source_health={source_health.get('health')}", f"source_reliability={source_health.get('reliability_label_zh')}:{source_health.get('reliability_score')}"],
        ),
        _goal_item(
            "技术目标",
            "自动扫描未来 1-3 天可售比赛",
            bool(scan_window.get("complete")) and int(scan_window.get("days_checked") or 0) >= 4,
            [f"scan_window={scan_window.get('start_date')}..{scan_window.get('end_date')}", f"days_checked={scan_window.get('days_checked')}"],
        ),
        _goal_item(
            "技术目标",
            "建立比分矩阵",
            bool(score_goals.get("score_table")) and bool(score_integrity),
            [f"score_rows={len(score_goals.get('score_table') or [])}", f"integrity_rows={len(score_integrity)}"],
        ),
        _goal_item(
            "技术目标",
            "用 Poisson / Dixon-Coles 推导比分、总进球、胜平负、让球胜平负",
            source_flags.get("poisson_score_matrix")
            and source_flags.get("dixon_coles")
            and bool(score_goals.get("total_goals_table"))
            and bool(score_goals.get("handicap_table")),
            [
                f"poisson_score_matrix={source_flags.get('poisson_score_matrix')}",
                f"dixon_coles={source_flags.get('dixon_coles')}",
                f"total_goal_rows={len(score_goals.get('total_goals_table') or [])}",
                f"handicap_rows={len(score_goals.get('handicap_table') or [])}",
            ],
        ),
        _goal_item(
            "技术目标",
            "用 Elo / 历史强度 / proxy xG 建立球队强弱",
            source_flags.get("elo_strength") and source_flags.get("proxy_xg"),
            [f"elo_strength={source_flags.get('elo_strength')}", f"proxy_xg={source_flags.get('proxy_xg')}"],
        ),
        _goal_item(
            "技术目标",
            "用赔率市场去水概率做强基准",
            source_flags.get("market_no_vig") and any(_has_any(row, ["market_prob"]) for row in observation_rows[:8]),
            [f"market_no_vig={source_flags.get('market_no_vig')}", f"observation_rows_with_market={len(observation_rows)}"],
        ),
        _goal_item(
            "技术目标",
            "建立情报融合层：伤停、首发、赛程、旅行、天气、新闻、战意",
            {"injuries", "lineup", "schedule", "travel", "weather", "news", "motivation"}.issubset(signal_keys),
            [f"signal_status_keys={', '.join(sorted(signal_keys))}"],
        ),
        _goal_item(
            "技术目标",
            "没有可靠情报时显示 unknown，不得编造",
            bool(missing_signals) and _signals_mark_unknown(intelligence),
            [f"missing_signals={', '.join(missing_signals)}", "unknown/not_connected 已进入 view"],
        ),
        _goal_item(
            "技术目标",
            "输出 confidence_score 和 missing_signals",
            bool(observation_rows)
            and all(_has_any(row, ["confidence_score"]) for row in observation_rows[:5])
            and all(_has_any(row, ["missing_signals"]) for row in observation_rows[:5]),
            [f"checked_observations={min(len(observation_rows), 5)}"],
        ),
        _goal_item(
            "技术目标",
            "组合优化显示通过门控原因和拒绝原因",
            bool(observation_rows)
            and bool(rejected_combo_rows)
            and all(_has_any(row, ["selection_reason", "reason"]) for row in observation_rows[:5])
            and all(_has_any(row, ["reject_reason", "reason"]) for row in rejected_combo_rows[:12]),
            [f"observation_rows={len(observation_rows)}", f"rejected_combo_rows={len(rejected_combo_rows)}"],
        ),
        _goal_item(
            "技术目标",
            "被拒组合进入赛后学习闭环",
            source_flags.get("rejected_combo_learning_snapshot") and source_flags.get("rejected_combo_learning_ui"),
            [
                f"snapshot_records_rejected_combo={source_flags.get('rejected_combo_learning_snapshot')}",
                f"ui_shows_rejected_combo_count={source_flags.get('rejected_combo_learning_ui')}",
            ],
        ),
        _goal_item(
            "技术目标",
            "模拟经营显示资金曲线、回撤、玩法贡献",
            bool(operation.get("equity_curve")) and bool(operation.get("combo_summary")) and bool(operation.get("profit_explanation")),
            [
                f"equity_rows={len(operation.get('equity_curve') or [])}",
                f"combo_rows={len(operation.get('combo_summary') or [])}",
                f"profit_notes={len(operation.get('profit_explanation') or [])}",
            ],
        ),
        _goal_item(
            "技术目标",
            "DeepSeek 只做解释层，不参与概率计算和组合选择",
            source_flags.get("deepseek_only_explain_layer") and not source_flags.get("deepseek_in_probability_stack"),
            [
                f"deepseek_only_explain_layer={source_flags.get('deepseek_only_explain_layer')}",
                f"deepseek_in_probability_stack={source_flags.get('deepseek_in_probability_stack')}",
            ],
        ),
        _goal_item(
            "技术目标",
            "auto AI 研究自动解析 DS Pro 或本地摘要",
            source_flags.get("ai_auto_backend_resolves_provider") and source_flags.get("ai_auto_frontend_passes_auto") and source_flags.get("ai_auto_execution_plan"),
            [
                f"backend_resolves_auto={source_flags.get('ai_auto_backend_resolves_provider')}",
                f"frontend_passes_auto={source_flags.get('ai_auto_frontend_passes_auto')}",
                f"auto_execution_plan={source_flags.get('ai_auto_execution_plan')}",
            ],
        ),
        _goal_item(
            "Phase 3-E",
            "真实用户历史 CSV 回测与模型校准具备可读准备度",
            user_replay.get("score") is not None and bool(user_replay.get("next_action_zh")),
            [f"replay_readiness={user_replay.get('label')}:{user_replay.get('score')}", f"calibration_status={user_replay.get('calibration_status')}"],
        ),
    ]
    for check in acceptance_checks:
        items.append(
            _goal_item(
                "验收标准",
                check.name,
                bool(check.passed),
                [check.message],
                details=check.details,
            )
        )
    return items


def _goal_item(
    category: str,
    requirement: str,
    achieved: bool,
    evidence: list[str],
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "category": category,
        "requirement": requirement,
        "status": "achieved" if achieved else "needs_work",
        "achieved": bool(achieved),
        "evidence": evidence,
        "details": details or {},
    }


def _goal_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    achieved = sum(1 for item in items if item.get("achieved"))
    total = len(items)
    return {
        "total": total,
        "achieved": achieved,
        "needs_work": total - achieved,
        "overall_ready": achieved == total,
    }


def _source_flags(root: Path) -> dict[str, bool]:
    def read(path: str) -> str:
        file_path = root / path
        return file_path.read_text(encoding="utf-8") if file_path.exists() else ""

    feature_context = read("src/intelligence/feature_context.py")
    fusion = read("src/intelligence/fusion.py")
    score_matrix = read("src/models/score_matrix.py")
    dixon_coles = read("src/models/dixon_coles.py")
    optimizer = read("src/optimizer/portfolio_optimizer.py")
    intelligence_stack = "\n".join(
        [
            feature_context,
            fusion,
            read("src/intelligence/news_signals.py"),
            read("src/intelligence/lineup_signals.py"),
            read("src/intelligence/weather_signals.py"),
            read("src/intelligence/schedule_signals.py"),
            read("src/intelligence/motivation_signals.py"),
        ]
    )
    probability_stack = "\n".join([feature_context, fusion, score_matrix, dixon_coles, optimizer])
    explain_stack = "\n".join([read("src/explain/deepseek_explainer.py"), read("src/explain/llm_explainer.py"), read("src/view_models/analysis_view.py")])
    ai_combo_research = read("src/explain/ai_combo_research.py")
    observation_snapshot = read("src/learning/observation_snapshot.py")
    dashboard_app = read("src/dashboard/static/app.js")
    return {
        "poisson_score_matrix": "poisson_pmf" in score_matrix and "build_score_matrix" in feature_context,
        "dixon_coles": "apply_dixon_coles_adjustment" in dixon_coles and "dixon_coles" in fusion,
        "elo_strength": "_elo_strength" in feature_context and "elo_strength" in fusion,
        "proxy_xg": "_xg_baseline" in feature_context and "poisson_xg" in fusion,
        "market_no_vig": "market_no_vig" in fusion and "no_vig_probs" in feature_context,
        "deepseek_only_explain_layer": "deepseek" in explain_stack.lower(),
        "deepseek_in_probability_stack": "deepseek" in probability_stack.lower(),
        "ai_auto_backend_resolves_provider": "_resolve_ai_provider" in ai_combo_research and "auto_ds_pro" in ai_combo_research,
        "ai_auto_execution_plan": "auto_execution_plan" in ai_combo_research and "读取 T+1 可售比赛" in ai_combo_research and "autoPlanSteps" in dashboard_app,
        "ai_auto_frontend_passes_auto": 'return mode === "auto" ? "auto" : mode' in dashboard_app,
        "intelligence_modules": all(token in intelligence_stack for token in ["news", "lineup", "weather", "schedule", "motivation"]),
        "rejected_combo_learning_snapshot": "rejected_combo_count" in observation_snapshot and "learning_track\": \"rejected_combo" in observation_snapshot,
        "rejected_combo_learning_ui": "被拒组合复盘" in dashboard_app and "rejected_combo_count" in dashboard_app,
    }


def _readiness_status_counts(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return ", ".join(f"{key}:{value}" for key, value in sorted(counts.items())) or "none"


def _endpoint_summary(payloads: dict[str, dict]) -> dict[str, Any]:
    next_available = payloads.get("next_available", {}).get("data", {})
    optimizer = payloads.get("optimizer_aggressive", {}).get("data", {})
    score_goals = payloads.get("score_goals", {}).get("data", {})
    return {
        "selected_date": next_available.get("selected_date"),
        "matches_count": next_available.get("matches_count"),
        "provider_used": next_available.get("provider_used"),
        "optimizer_risk_profile": optimizer.get("risk_profile"),
        "score_goals_rows": len(score_goals.get("total_goals_table", []) or []) + len(score_goals.get("score_table", []) or []),
    }


def _payload_data(payloads: dict[str, dict], name: str) -> dict[str, Any]:
    payload = payloads.get(name) or {}
    data = payload.get("data") if isinstance(payload, dict) else {}
    return data if isinstance(data, dict) else {}


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _stringify(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return str(value)


def _has_any(row: dict[str, Any], keys: list[str]) -> bool:
    return any(str(row.get(key) or "").strip() for key in keys)


def _collect_observation_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    direct_keys = [
        "top_single_observations",
        "top_singles",
        "top_2x1",
        "top_parlay_2x1",
        "top_total_goals",
        "top_scores",
    ]
    for key in direct_keys:
        rows.extend(_list_of_dicts(data.get(key)))

    top_observations = data.get("top_observations")
    if isinstance(top_observations, dict):
        for key in ["singles", "parlay_2x1", "parlay_3x1", "total_goals", "scores"]:
            rows.extend(_list_of_dicts(top_observations.get(key)))

    selected_portfolio = data.get("selected_portfolio")
    if isinstance(selected_portfolio, dict):
        for key in ["singles", "parlay_2x1", "parlay_3x1"]:
            rows.extend(_list_of_dicts(selected_portfolio.get(key)))

    return rows


def _collect_rejected_combo_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidate_rankings = data.get("candidate_rankings")
    if isinstance(candidate_rankings, dict):
        for key in ["parlay_2x1", "parlay_3x1"]:
            rows.extend(_list_of_dicts(candidate_rankings.get(key)))
    rows.extend(_list_of_dicts(data.get("rejected_candidates")))
    return [row for row in rows if not row.get("selected")]


def _collect_missing_signals(*items: dict[str, Any]) -> list[str]:
    collected: list[str] = []
    for item in items:
        values = item.get("missing_signals")
        if isinstance(values, list):
            collected.extend(str(value) for value in values if value)
        context_summary = item.get("context_summary")
        if isinstance(context_summary, dict):
            values = context_summary.get("missing_signals")
            if isinstance(values, list):
                collected.extend(str(value) for value in values if value)
    return list(dict.fromkeys(collected))


def _collect_signal_keys(*items: dict[str, Any]) -> list[str]:
    collected: list[str] = []
    for item in items:
        rows = item.get("signal_status")
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and row.get("key"):
                    collected.append(str(row["key"]))
    return list(dict.fromkeys(collected))


def _collect_connected_signal_keys(*items: dict[str, Any]) -> list[str]:
    collected: list[str] = []
    for item in items:
        status = item.get("external_signals_status")
        if isinstance(status, dict):
            fields = status.get("supplied_fields")
            if isinstance(fields, list):
                collected.extend(str(field) for field in fields if field)
        rows = item.get("signal_status")
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict) or not row.get("key"):
                    continue
                raw = str(row.get("status_raw") or row.get("status") or "")
                if raw in {"connected", "confirmed", "user_supplied"} or row.get("source_zh") == "用户 JSON":
                    collected.append(str(row["key"]))
    return list(dict.fromkeys(collected))


def _signals_mark_unknown(data: dict[str, Any]) -> bool:
    blob = _stringify(data)
    return "not_connected" in blob and "unknown" in blob


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _fix_suggestions(findings: list[dict]) -> list[str]:
    if not findings:
        return ["未发现阻断问题；继续保持只读、观察信号和风险诊断边界。"]
    suggestions = []
    for item in findings:
        name = item.get("name", "")
        if "operation_panel" in name or "api_base" in name:
            suggestions.append("把技术控件放入默认关闭的高级设置抽屉，不要放在首页第一屏。")
        elif "button" in name:
            suggestions.append("替换正向交易按钮文案，使用观察、模拟、风险解释等表述。")
        elif "endpoint" in name:
            suggestions.append("修复对应只读 API endpoint，并确保错误不暴露 traceback。")
        else:
            suggestions.append("补齐今日观察首页必要模块。")
    return list(dict.fromkeys(suggestions))


def main() -> None:
    parser = argparse.ArgumentParser(description="严厉交易者 App 审计：检查首页、只读 API、观察信号和禁用交易控件。")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    report = run_strict_trader_audit(".")
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Strict trader audit: {'passed' if report['overall_passed'] else 'failed'}")
        for finding in report.get("findings", []):
            print(f"- {finding.get('name')}: {finding.get('message')}")


if __name__ == "__main__":
    main()

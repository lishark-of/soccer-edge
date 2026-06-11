from __future__ import annotations

from src.explain.safety import DISCLAIMER_TEXT


def build_user_workflow_view(workflow_result: dict) -> dict:
    field_report = workflow_result.get("field_report", {}) or {}
    backtest = workflow_result.get("backtest", {}) or {}
    analysis = workflow_result.get("analysis", {}) or {}
    preflight_quality = workflow_result.get("preflight_quality", {}) or {}
    readiness_table = _readiness_table(workflow_result, field_report, backtest, preflight_quality)
    replay_readiness_summary = _replay_readiness_summary(readiness_table, preflight_quality, field_report)
    steps = [
        _step(1, "识别 CSV 字段", _status(not field_report.get("missing_required_fields"), bool(field_report.get("warnings"))), _field_summary(field_report)),
        _step(2, "生成标准化数据", _status(bool(workflow_result.get("normalized_output_path")), False), workflow_result.get("normalized_output_path") or "尚未生成标准化 CSV。"),
        _step(3, "运行概率回测", _status(backtest.get("matches_evaluated", 0) > 0, bool(backtest.get("warnings"))), f"有效评估 {backtest.get('matches_evaluated', 0)} 场，候选触发 {backtest.get('bets_total', 0)} 次。"),
        _step(4, "生成校准文件", _status(bool(workflow_result.get("calibration_artifact_path")), False), workflow_result.get("calibration_artifact_path") or "尚未生成 calibration artifact。"),
        _step(5, "运行明日分析", _status(bool(analysis), bool((analysis or {}).get("warnings"))), f"分析比赛数：{(analysis or {}).get('matches_analyzed', 0)}。"),
        _step(6, "查看候选信号与风险", _status(bool((analysis or {}).get("single_candidates") or (analysis or {}).get("parlay_2x1_candidates")), bool((analysis or {}).get("warnings"))), "进入 App 的候选信号和组合风险页查看解释。"),
    ]
    return {
        "title": "用户 CSV 入门流程",
        "steps": steps,
        "summary_cards": [
            {"label": "字段识别", "value": field_report.get("confidence", "unknown"), "help": "high 表示必需字段和赔率字段识别较完整。"},
            {"label": "字段可标准化", "value": "yes" if field_report.get("can_normalize") else "no", "help": "必需字段齐全后才可生成标准化 CSV。"},
            {"label": "可做 EV 回测", "value": "yes" if field_report.get("can_backtest_with_ev") else "no", "help": "赔率字段齐全后才能评估 EV 与候选触发。"},
            {"label": "标准化数据", "value": workflow_result.get("normalized_output_path") or "未生成", "help": "生成文件位于 ignored 目录，不应提交。"},
            {"label": "回测有效比赛", "value": backtest.get("matches_evaluated", 0), "help": "满足训练样本和赔率条件的比赛数量。"},
            {"label": "校准文件", "value": workflow_result.get("calibration_artifact_path") or "未生成", "help": "用于后续分析的诊断辅助。"},
        ],
        "readiness_cards": _readiness_cards(readiness_table),
        "readiness_table": readiness_table,
        "replay_readiness_summary": replay_readiness_summary,
        "preflight_quality": preflight_quality,
        "preflight_checks": preflight_quality.get("checks", []) or [],
        "cli_handoff": workflow_result.get("cli_handoff", {}) or {},
        "field_report": field_report,
        "repair_suggestions": workflow_result.get("repair_suggestions", []) or [],
        "workflow_summary": workflow_result.get("workflow_summary", {}) or {},
        "backtest_explanation": workflow_result.get("backtest_explanation", []) or [],
        "calibration_explanation": workflow_result.get("calibration_explanation", []) or [],
        "data_quality_notes": workflow_result.get("data_quality_notes", []) or [],
        "next_steps": workflow_result.get("next_steps", []) or [],
        "warnings": workflow_result.get("warnings", []) or [],
        "disclaimer": DISCLAIMER_TEXT,
    }


def _readiness_table(workflow_result: dict, field_report: dict, backtest: dict, preflight_quality: dict) -> list[dict]:
    status = workflow_result.get("overall_status", "preview")
    missing_required = field_report.get("missing_required_fields") or []
    missing_odds = field_report.get("missing_odds_fields") or []
    normalized_path = workflow_result.get("normalized_output_path")
    calibration_path = workflow_result.get("calibration_artifact_path")
    evaluated = int(backtest.get("matches_evaluated", 0) or 0)
    backtest_preflight_status = preflight_quality.get("backtest_preflight_status")
    calibration_preflight_status = preflight_quality.get("calibration_preflight_status")
    return [
        {
            "item": "字段预检",
            "status": "ready" if not missing_required else "blocked",
            "meaning_zh": "必需字段齐全。" if not missing_required else "缺少必需字段：" + "、".join(missing_required),
            "next_action_zh": "可以进入标准化。" if not missing_required else "按修复建议补齐 CSV 或 mapping。",
        },
        {
            "item": "赔率覆盖",
            "status": "ready" if field_report.get("can_backtest_with_ev") else "warning",
            "meaning_zh": "胜平负赔率可用于 EV 回测。" if field_report.get("can_backtest_with_ev") else "赔率字段不完整：" + ("、".join(missing_odds) if missing_odds else "未确认"),
            "next_action_zh": "可以评估候选触发与 EV。" if field_report.get("can_backtest_with_ev") else "补充胜赔、平赔、负赔后再看 EV。",
        },
        {
            "item": "标准化 CSV",
            "status": "ready" if normalized_path else "pending",
            "meaning_zh": f"已生成：{normalized_path}" if normalized_path else "App 预览不写文件，完整 workflow 由 CLI 生成。",
            "next_action_zh": "进入回测诊断。" if normalized_path else "字段 OK 后运行 CLI workflow 生成标准化 CSV。",
        },
        {
            "item": "概率回测",
            "status": "ready" if evaluated > 0 else backtest_preflight_status or "pending",
            "meaning_zh": f"已评估 {evaluated} 场。" if evaluated > 0 else "尚未完成回测；当前预检状态：" + str(backtest_preflight_status or "pending"),
            "next_action_zh": "查看 ROI、Brier Score、Log Loss 和最大回撤。" if evaluated > 0 else "生成标准化 CSV 后运行回测。",
        },
        {
            "item": "校准文件",
            "status": "ready" if calibration_path else calibration_preflight_status or "pending",
            "meaning_zh": f"已生成：{calibration_path}" if calibration_path else "尚未生成校准文件；当前预检状态：" + str(calibration_preflight_status or "pending"),
            "next_action_zh": "后续分析可读取校准诊断。" if calibration_path else "回测完成后再生成 calibration artifact。",
        },
        {
            "item": "App 使用状态",
            "status": "ready" if status == "success" else "preview",
            "meaning_zh": "完整流程完成。" if status == "success" else "当前是只读预览，不会写 normalized/calibration 文件。",
            "next_action_zh": "查看候选信号与风险解释。" if status == "success" else "确认字段后，用 CLI 执行完整 workflow。",
        },
    ]


def _readiness_cards(readiness_table: list[dict]) -> list[dict]:
    counts = {"ready": 0, "warning": 0, "pending": 0, "blocked": 0, "preview": 0}
    for row in readiness_table:
        status = str(row.get("status") or "pending")
        counts[status] = counts.get(status, 0) + 1
    return [
        {"label": "ready", "value": counts.get("ready", 0), "help": "已经具备的流程环节。"},
        {"label": "pending", "value": counts.get("pending", 0) + counts.get("preview", 0), "help": "预览或等待完整 CLI workflow 的环节。"},
        {"label": "warning", "value": counts.get("warning", 0), "help": "不阻断但会影响 EV/回测质量。"},
        {"label": "blocked", "value": counts.get("blocked", 0), "help": "需要先修复字段或 mapping。"},
    ]


def _replay_readiness_summary(readiness_table: list[dict], preflight_quality: dict, field_report: dict) -> dict:
    statuses = {row.get("item"): row.get("status") for row in readiness_table}
    blocked = [row for row in readiness_table if row.get("status") == "blocked"]
    warnings = [row for row in readiness_table if row.get("status") == "warning"]
    ready = [row for row in readiness_table if row.get("status") == "ready"]
    rows_read = int(preflight_quality.get("rows_read", 0) or 0)
    rows_normalized = int(preflight_quality.get("rows_normalized", 0) or 0)
    had_odds_coverage = float(preflight_quality.get("had_odds_coverage", 0) or 0)
    can_normalize = bool(field_report.get("can_normalize"))
    can_backtest = bool(field_report.get("can_backtest_with_ev")) and preflight_quality.get("backtest_preflight_status") == "ready"
    calibration_status = preflight_quality.get("calibration_preflight_status") or statuses.get("校准文件") or "pending"
    score = 0
    score += 30 if can_normalize else 0
    score += 25 if can_backtest else 0
    score += 20 if rows_normalized >= 30 else 10 if rows_normalized >= 10 else 0
    score += 15 if had_odds_coverage >= 0.95 else 8 if had_odds_coverage >= 0.7 else 0
    score += 10 if calibration_status in {"ready", "warning"} else 0
    if blocked:
        label = "需要先修字段"
        next_action = "先按修复建议补齐 CSV 或 mapping，再进入完整 workflow。"
    elif can_backtest:
        label = "可进入完整复盘"
        next_action = "可使用 CLI 完整执行标准化、回测、校准和明日分析；Dashboard/API 保持只读预览。"
    elif can_normalize:
        label = "可标准化，回测待补"
        next_action = "先生成标准化 CSV，再补齐赔率或样本后做 EV 回测。"
    else:
        label = "仅可预检"
        next_action = "先修复字段识别和必需列。"
    proof_points = [
        f"可标准化：{'yes' if can_normalize else 'no'}。",
        f"预计标准化行数：{rows_normalized}/{rows_read}。",
        f"胜平负赔率覆盖：{had_odds_coverage:.0%}。",
        f"回测准备度：{preflight_quality.get('backtest_preflight_status') or 'pending'}。",
        f"校准准备度：{calibration_status}。",
    ]
    return {
        "label": label,
        "score": min(score, 100),
        "summary_zh": f"CSV 复盘准备度为 {label}，评分 {min(score, 100)}/100。",
        "next_action_zh": next_action,
        "proof_points": proof_points,
        "blocked_items": [row.get("item") for row in blocked],
        "warning_items": [row.get("item") for row in warnings],
        "ready_items": [row.get("item") for row in ready],
        "calibration_status": calibration_status,
        "calibration_note_zh": "校准文件用于诊断概率偏差，不保证未来表现；样本不足时只给 warning，不应过度解读。",
    }


def _step(number: int, title: str, status: str, summary: str) -> dict:
    return {"step": number, "title": title, "status": status, "summary": summary}


def _status(success: bool, warning: bool) -> str:
    if success and warning:
        return "warning"
    if success:
        return "success"
    return "error"


def _field_summary(field_report: dict) -> str:
    missing = field_report.get("missing_required_fields") or []
    if missing:
        return "缺少必需字段：" + "、".join(missing)
    return f"已识别 {len(field_report.get('recognized_fields', []) or [])} 个字段。"

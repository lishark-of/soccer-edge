from __future__ import annotations

from src.explain.safety import DISCLAIMER_TEXT


def build_user_workflow_view(workflow_result: dict) -> dict:
    field_report = workflow_result.get("field_report", {}) or {}
    backtest = workflow_result.get("backtest", {}) or {}
    analysis = workflow_result.get("analysis", {}) or {}
    steps = [
        _step(1, "识别 CSV 字段", _status(not field_report.get("missing_required_fields"), bool(field_report.get("warnings"))), _field_summary(field_report)),
        _step(2, "生成标准化数据", _status(bool(workflow_result.get("normalized_output_path")), False), workflow_result.get("normalized_output_path") or "尚未生成标准化 CSV。"),
        _step(3, "运行概率回测", _status(backtest.get("matches_evaluated", 0) > 0, bool(backtest.get("warnings"))), f"有效评估 {backtest.get('matches_evaluated', 0)} 场，候选触发 {backtest.get('bets_total', 0)} 次。"),
        _step(4, "生成校准文件", _status(bool(workflow_result.get("calibration_artifact_path")), False), workflow_result.get("calibration_artifact_path") or "尚未生成 calibration artifact。"),
        _step(5, "运行明日分析", _status(bool(analysis), bool((analysis or {}).get("warnings"))), f"分析比赛数：{(analysis or {}).get('matches_analyzed', 0)}。"),
        _step(6, "查看候选信号与风险", _status(bool((analysis or {}).get("single_candidates") or (analysis or {}).get("parlay_2x1_candidates")), bool((analysis or {}).get("warnings"))), "进入 App 的候选买点和组合风险页查看解释。"),
    ]
    return {
        "title": "用户 CSV 入门流程",
        "steps": steps,
        "summary_cards": [
            {"label": "字段识别", "value": field_report.get("confidence", "unknown"), "help": "high 表示必需字段和赔率字段识别较完整。"},
            {"label": "标准化数据", "value": workflow_result.get("normalized_output_path") or "未生成", "help": "生成文件位于 ignored 目录，不应提交。"},
            {"label": "回测有效比赛", "value": backtest.get("matches_evaluated", 0), "help": "满足训练样本和赔率条件的比赛数量。"},
            {"label": "校准文件", "value": workflow_result.get("calibration_artifact_path") or "未生成", "help": "用于后续分析的诊断辅助。"},
        ],
        "field_report": field_report,
        "repair_suggestions": workflow_result.get("repair_suggestions", []) or [],
        "next_steps": workflow_result.get("next_steps", []) or [],
        "warnings": workflow_result.get("warnings", []) or [],
        "disclaimer": DISCLAIMER_TEXT,
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

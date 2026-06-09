from __future__ import annotations

from src.explain.safety import DISCLAIMER_TEXT


def build_qa_view(qa_result: dict) -> dict:
    summary = qa_result.get("summary", {}) or {}
    checks = list(qa_result.get("checks", []) or [])
    failed = [item for item in checks if not item.get("passed")]
    warning_checks = [item for item in checks if item.get("severity") == "warning"]
    return {
        "title": "QA 健康检查",
        "summary_cards": [
            {"label": "整体状态", "value": "通过" if qa_result.get("overall_passed") else "需检查", "help": "QA 是质量闸门，不代表预测准确。"},
            {"label": "检查总数", "value": summary.get("total", 0), "help": "已执行的 QA 检查数量。"},
            {"label": "失败", "value": summary.get("failed", 0), "help": "需要优先处理的错误检查。"},
            {"label": "警告", "value": summary.get("warnings", 0), "help": "不一定阻断，但建议关注。"},
        ],
        "failed_checks": failed[:30],
        "warning_checks": warning_checks[:30],
        "warnings": list(qa_result.get("warnings", []) or []),
        "disclaimer": DISCLAIMER_TEXT,
    }

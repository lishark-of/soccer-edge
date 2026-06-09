from __future__ import annotations

from src.explain.safety import DISCLAIMER_TEXT


def build_calibration_view(validation_result: dict) -> dict:
    valid = bool(validation_result.get("valid"))
    issues = list(validation_result.get("issues", []) or [])
    status = "可读取" if valid else "无效或缺失"
    return {
        "title": "校准 artifact 状态",
        "summary_cards": [
            {"label": "状态", "value": status, "help": "artifact 只能作为诊断辅助。"},
            {"label": "路径", "value": validation_result.get("path", ""), "help": "本地 calibration JSON 文件路径。"},
            {"label": "问题数量", "value": len(issues), "help": "校验发现的问题数量。"},
        ],
        "issues": issues,
        "explanations": [
            "校准 artifact 来自历史回测诊断，不能保证未来表现。",
            "无效或缺失时，分析会回退到未校准概率，不应导致应用崩溃。",
        ],
        "warnings": issues,
        "disclaimer": DISCLAIMER_TEXT,
    }

from __future__ import annotations


def diagnose_operation(report: dict) -> dict:
    issues: list[dict] = []
    strengths: list[dict] = []
    combo = report.get("combo_summary", {}) or {}
    if report.get("observation_count", 0) < 20:
        issues.append(_issue("warning", "样本量不足", "模拟观察项较少，统计波动会很大。", "导入更多真实历史 CSV 后再复盘。"))
    if float(report.get("max_drawdown") or 0.0) >= 0.12:
        issues.append(_issue("warning", "最大回撤偏大", "纸面本金曲线出现较明显回撤。", "降低每日模拟投入上限，或提高 EV / Edge 阈值后再观察。"))
    single = combo.get("single", {})
    parlay2 = combo.get("parlay_2x1", {})
    parlay3 = combo.get("parlay_3x1", {})
    if parlay2.get("settled", 0) and float(parlay2.get("profit", 0.0)) < 0:
        issues.append(_issue("warning", "2串1 组合回撤较大", "组合观察比单关更容易出现连续亏损。", "降低每日 2串1 数量，或提高 EV 阈值后再观察。"))
    if parlay3.get("settled", 0) and float(parlay3.get("profit", 0.0)) < 0:
        issues.append(_issue("warning", "3串1 表现不稳定", "3串1 需要更多条件同时发生，波动更大。", "默认保持关闭，除非样本量充足且风险可解释。"))
    if single.get("settled", 0) and float(single.get("hit_rate", 0.0)) >= 0.45:
        strengths.append({"title": "单关观察相对稳定", "detail": "单关命中率在当前 fixture 中相对可读，但仍不代表未来。"})
    if report.get("fixture_warning", True):
        issues.append(_issue("info", "fixture 不是生产数据", "示例数据只用于流程验证。", "用自己的历史 CSV 做更接近真实习惯的复盘。"))
    if not issues:
        strengths.append({"title": "未发现严重结构性问题", "detail": "当前阈值下没有触发明显风险告警，但仍需更多真实样本。"})
    return {
        "issues": issues,
        "strengths": strengths,
        "recommended_app_improvements": [
            "继续显示单关与组合观察的分开展示。",
            "真实 CSV 导入后优先查看最大回撤和 2串1 表现。",
        ],
    }


def _issue(severity: str, title: str, detail: str, suggestion: str) -> dict:
    return {"severity": severity, "title": title, "detail": detail, "suggestion": suggestion}

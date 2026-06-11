from __future__ import annotations

from pathlib import Path
from typing import Any

from src.audit.auto_fix_suggestions import build_auto_fix_suggestions
from src.audit.credibility import audit_credibility
from src.audit.issue_finder import find_static_app_issues


def run_user_acceptance_audit(project_root: str = ".") -> dict[str, Any]:
    root = Path(project_root)
    html = _read(root / "src/dashboard/static/index.html")
    js = _read(root / "src/dashboard/static/app.js")
    pages_checked = []
    issues = find_static_app_issues(html, js)
    payloads = {}
    endpoint_specs = {
        "今日观察": ("/api/view/next-available", {"provider": "auto", "bankroll": "10000", "risk_profile": "aggressive"}),
        "竞彩足球": ("/api/view/matches", {"provider": "auto", "date": "2026-06-10"}),
        "赛前优化": ("/api/view/optimizer", {"provider": "auto", "date": "2026-06-10", "bankroll": "10000", "risk_profile": "aggressive", "show_rejected": "1"}),
        "比分/进球数": ("/api/view/score-goals", {"provider": "auto", "date": "2026-06-10"}),
        "模拟走盘": ("/api/view/operation", {"historical_data": "data/fixtures/operation_walkforward_sample.csv", "initial_bankroll": "10000"}),
        "数据导入": ("/api/view/import/preview", {"input": "data/fixtures/user_onboarding_sample.csv", "adapter": "auto"}),
        "QA": ("/api/view/qa", {}),
    }
    for page, (path, query) in endpoint_specs.items():
        try:
            from src.api.routes import dispatch_route

            payload = dispatch_route(path, query)
            ok = bool(payload.get("ok"))
            data = payload.get("data") or {}
            payloads[page] = payload
            pages_checked.append({"page": page, "passed": ok, "endpoint": path})
            if not ok:
                issues.append(_issue("error", f"{page} 接口未通过", "页面无法正常展示。", "检查对应 API 输出。"))
            _page_specific_checks(page, data, issues)
        except Exception as exc:  # noqa: BLE001
            pages_checked.append({"page": page, "passed": False, "endpoint": path, "error_zh": str(exc).splitlines()[0][:160]})
            issues.append(_issue("error", f"{page} 请求失败", "用户会看到空页面或错误。", "修复接口并返回中文错误。"))
    next_data = (payloads.get("今日观察") or {}).get("data") or {}
    credibility = audit_credibility({**next_data, "optimizer": ((payloads.get("赛前优化") or {}).get("data") or {})})
    if "可信度" not in html:
        issues.append(_issue("warning", "首页未显式标注可信度", "用户不知道当前结果能信多少。", "在首页 summary card 显示可信度评分。"))
    return {
        "audit_version": "phase2p_user_acceptance_audit_v0",
        "overall_passed": not any(item.get("severity") == "error" for item in issues),
        "pages_checked": pages_checked,
        "issues": issues,
        "recommended_fixes": build_auto_fix_suggestions(issues),
        "credibility_score": credibility.get("credibility_score", 0),
        "credibility": credibility,
        "disclaimer": "使用者实操验收只检查观察信号、纸面模拟和风险诊断，不构成投注建议。",
    }


def _page_specific_checks(page: str, data: dict, issues: list[dict]) -> None:
    if page == "赛前优化":
        if not data.get("candidate_rankings"):
            issues.append(_issue("warning", "赛前优化缺少候选排行榜", "用户无法看到被拒组合。", "返回 candidate_rankings 和 rejected reasons。"))
        if not data.get("best_parlay_summary"):
            issues.append(_issue("warning", "缺少优秀串联摘要", "用户不知道 best 2串1 / best 3串1。", "补充 best_parlay_summary。"))
    if page == "模拟走盘":
        labels = " ".join(str(card.get("label")) for card in data.get("summary_cards", []) if isinstance(card, dict))
        if "本金收益率" not in labels and "ROI" not in labels:
            issues.append(_issue("warning", "模拟走盘收益口径不够清楚", "用户会误解为什么只赚一小部分。", "显示本金收益率和模拟投入 ROI。"))
    if page == "数据导入":
        if not data.get("field_report") and not data.get("repair_suggestions"):
            issues.append(_issue("warning", "数据导入缺少字段识别/修复建议", "用户不知道 CSV 怎么改。", "展示字段识别和中文修复建议。"))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _issue(severity: str, title: str, impact: str, suggestion: str) -> dict:
    return {"severity": severity, "title": title, "impact_zh": impact, "suggestion_zh": suggestion}

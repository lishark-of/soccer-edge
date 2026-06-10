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
        "optimizer_aggressive": ("/api/view/optimizer", {"provider": "auto", "date": "2026-06-10", "bankroll": "10000", "risk_profile": "aggressive"}),
        "score_goals": ("/api/view/score-goals", {"provider": "auto", "date": "2026-06-10"}),
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

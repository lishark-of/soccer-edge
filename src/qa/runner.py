from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.api.errors import ApiError, error_response
from src.api.routes import dispatch_route
from src.application import build_analysis_payload
from src.backtesting.backtest_engine import run_backtest
from src.backtesting.historical_loader import load_historical_matches
from src.backtesting.report import build_backtest_report
from src.exports.report_exporter import export_report_to_markdown
from src.qa.api_sanity import check_api_envelope, check_api_error_envelope
from src.qa.checks import QaCheckResult, results_to_dicts, summarize_checks
from src.qa.dashboard_sanity import check_dashboard_static_files
from src.qa.disclaimers import scan_project_disclaimers
from src.qa.git_hygiene import check_generated_paths_not_tracked, check_git_remote_absent, check_worktree_clean_or_expected
from src.qa.llm_sanity import check_deepseek_status_response, check_llm_disabled_by_default
from src.qa.model_sanity import check_analysis_output, check_backtest_output
from src.qa.network_safety import check_no_default_external_calls
from src.qa.rehearsal import run_end_to_end_rehearsal
from src.qa.report_sanity import check_report_structure


QA_VERSION = "phase2f_qa_harness_v0"
DISCLAIMER = "QA checks are diagnostics and do not guarantee prediction accuracy or future outcomes."


def run_qa(project_root: str, rehearsal: bool = False, strict: bool = False) -> dict:
    root = Path(project_root)
    checks: list[QaCheckResult] = []
    warnings: list[str] = []

    analysis = build_analysis_payload(target_date="2026-06-09", provider_name="mock")
    matches = load_historical_matches(str(root / "data/fixtures/historical_matches_backtest_sample.csv"))
    backtest = build_backtest_report(run_backtest(matches, min_train_matches=20))
    checks.extend(check_analysis_output(analysis))
    checks.extend(check_backtest_output(backtest))
    checks.extend(check_report_structure(analysis, "analysis"))
    checks.extend(check_report_structure(backtest, "backtest"))
    checks.extend(scan_project_disclaimers([str(root / "README.md"), str(root / "docs/qa_guide.md"), str(root / "docs/real_data_rehearsal_guide.md")]))
    checks.extend(check_api_envelope(dispatch_route("/api/health", {}), "health"))
    checks.extend(check_api_envelope(dispatch_route("/api/info", {}), "info"))
    llm_status = dispatch_route("/api/llm/status", {})
    checks.extend(check_api_envelope(llm_status, "llm_status"))
    checks.extend(check_deepseek_status_response(llm_status.get("data", {})))
    checks.extend(check_llm_disabled_by_default())
    checks.extend(check_no_default_external_calls())
    try:
        dispatch_route("/api/analyze", {"export": "xlsx"})
    except ApiError as exc:
        _, payload = error_response(exc)
        checks.extend(check_api_error_envelope(payload, "read_only_violation"))
    checks.extend(check_dashboard_static_files(str(root / "src/dashboard/static")))
    checks.extend(check_generated_paths_not_tracked(str(root)))
    checks.extend(check_git_remote_absent(str(root)))
    checks.extend(check_worktree_clean_or_expected(str(root)))

    rehearsal_payload = {}
    if rehearsal:
        rehearsal_payload = run_end_to_end_rehearsal(str(root))
        for item in rehearsal_payload.get("checks", []):
            checks.append(
                QaCheckResult(
                    name=f"rehearsal.{item['name']}",
                    passed=bool(item["passed"]),
                    severity=item.get("severity", "error"),
                    message=item.get("message", ""),
                    details=item.get("details", {}),
                )
            )
        warnings.extend(rehearsal_payload.get("warnings", []))

    summary = summarize_checks(checks)
    overall = summary["overall_passed"] and (not strict or summary["warnings"] == 0)
    return {
        "qa_version": QA_VERSION,
        "overall_passed": overall,
        "summary": {**summary, "overall_passed": overall},
        "checks": results_to_dicts(checks),
        "rehearsal": rehearsal_payload,
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }


def write_qa_markdown(report: dict, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    failed = [check for check in report.get("checks", []) if not check.get("passed")]
    warnings = [check for check in report.get("checks", []) if check.get("severity") == "warning"]
    lines = [
        "# football-jc-analysis QA Report",
        "",
        f"Generated: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
        f"Overall passed: {report.get('overall_passed')}",
        "",
        "## Summary",
        "",
    ]
    for key, value in report.get("summary", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Failed Checks", ""])
    for check in failed or [{"name": "none", "message": "none"}]:
        lines.append(f"- {check.get('name')}: {check.get('message')}")
    lines.extend(["", "## Warning Checks", ""])
    for check in warnings or [{"name": "none", "message": "none"}]:
        lines.append(f"- {check.get('name')}: {check.get('message')}")
    rehearsal = report.get("rehearsal") or {}
    lines.extend(["", "## Rehearsal", ""])
    if rehearsal:
        lines.append(f"- overall_passed: {rehearsal.get('overall_passed')}")
        lines.append(f"- normalized_output: {rehearsal.get('import_output', {}).get('output_path')}")
        lines.append(f"- calibration_artifact: {rehearsal.get('calibration_artifact_path')}")
        lines.append(f"- markdown_report: {rehearsal.get('markdown_report_path')}")
    else:
        lines.append("- not run")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- 仅供数据研究与娱乐参考。",
            "- 不提供投注、下单、支付、代购或任何自动化购彩能力。",
            "- 概率模型不保证结果。",
            "- 回测结果不保证未来表现。",
            "- 串关会显著放大风险。",
            f"- {DISCLAIMER}",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)

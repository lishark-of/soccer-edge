from __future__ import annotations

from pathlib import Path

from src.qa.checks import QaCheckResult
from src.qa.disclaimers import _check_banned_terms


def check_report_structure(report: dict, report_type: str = "unknown") -> list[QaCheckResult]:
    results = [
        QaCheckResult(f"report.{report_type}.warnings", "warnings" in report, severity="warning", message="report includes warnings"),
        QaCheckResult(f"report.{report_type}.disclaimer", bool(report.get("disclaimer") or report.get("disclaimers")), message="report includes disclaimer"),
    ]
    if report_type == "backtest":
        results.append(QaCheckResult("report.backtest.metrics", isinstance(report.get("metrics"), dict), message="backtest report includes metrics"))
    if report_type == "analysis":
        results.append(QaCheckResult("report.analysis.provider", bool(report.get("provider") and report.get("provider_used")), message="analysis report includes provider metadata"))
    return results


def check_report_warnings(report: dict) -> list[QaCheckResult]:
    return [QaCheckResult("report.warnings.list", isinstance(report.get("warnings", []), list), message="warnings is a list")]


def check_markdown_report(path: str) -> list[QaCheckResult]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return [QaCheckResult(f"report.markdown.{path}", False, message=str(exc))]
    results = [
        QaCheckResult("report.markdown.disclaimer", "不提供投注、下单、支付、代购或任何自动化购彩能力" in text, message="markdown contains safety disclaimer"),
    ]
    results.extend(_check_banned_terms(text, path))
    return results

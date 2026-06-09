from __future__ import annotations

from pathlib import Path

from src.application import build_analysis_payload
from src.backtesting.backtest_engine import run_backtest
from src.backtesting.historical_loader import load_historical_matches_with_warnings
from src.backtesting.report import build_backtest_report
from src.backtesting.schema import validate_historical_dataset
from src.calibration.persistence import save_calibration_artifact
from src.calibration.store import build_calibration_artifact
from src.exports.report_exporter import export_report_to_markdown
from src.ingestion.importer import import_historical_file
from src.qa.checks import QaCheckResult, results_to_dicts, summarize_checks
from src.qa.model_sanity import check_analysis_output, check_backtest_output, check_calibration_artifact
from src.qa.report_sanity import check_markdown_report, check_report_structure


def run_sample_import_rehearsal(
    project_root: str,
    input_path: str,
    mapping_path: str | None = None,
    adapter: str = "auto",
) -> dict:
    root = Path(project_root)
    return import_historical_file(
        input_path=str(root / input_path),
        adapter_name=adapter,
        mapping_path=str(root / mapping_path) if mapping_path else None,
        dry_run=True,
    )


def run_end_to_end_rehearsal(project_root: str) -> dict:
    root = Path(project_root)
    warnings: list[str] = []
    checks: list[QaCheckResult] = []
    normalized_path = root / "data/normalized/qa_rehearsal_normalized.csv"
    calibration_path = root / "artifacts/calibration/qa_rehearsal_calibration.json"
    markdown_path = root / "reports/qa_rehearsal_backtest.md"
    input_path = root / "data/fixtures/rehearsal_real_like_generic.csv"

    try:
        dry_run = import_historical_file(str(input_path), adapter_name="auto", dry_run=True)
        output = import_historical_file(str(input_path), adapter_name="auto", output_path=str(normalized_path))
        checks.append(QaCheckResult("rehearsal.import.normalized", output["rows_normalized"] >= 20, message="rehearsal normalized at least 20 rows"))
    except Exception as exc:
        dry_run = {}
        output = {}
        warnings.append(f"rehearsal import failed: {str(exc)[:180]}")
        checks.append(QaCheckResult("rehearsal.import", False, message="rehearsal import failed"))

    try:
        matches, load_warnings = load_historical_matches_with_warnings(str(normalized_path))
        warnings.extend(load_warnings)
        data_summary = validate_historical_dataset(matches)
        result = run_backtest(matches, min_train_matches=8)
        result["data_summary"] = data_summary
        report = build_backtest_report(result)
        artifact = build_calibration_artifact(report, report.get("model_version", "unknown"))
        save_calibration_artifact(artifact, str(calibration_path))
        export_report_to_markdown(report, str(markdown_path))
        analysis = build_analysis_payload(target_date="2026-06-09", provider_name="mock", calibration_artifact_path=str(calibration_path))
        checks.extend(check_backtest_output(report))
        checks.extend(check_report_structure(report, "backtest"))
        checks.extend(check_calibration_artifact(artifact))
        checks.extend(check_analysis_output(analysis))
        checks.extend(check_markdown_report(str(markdown_path)))
    except Exception as exc:
        report = {}
        artifact = {}
        analysis = {}
        warnings.append(f"rehearsal backtest/report failed: {str(exc)[:180]}")
        checks.append(QaCheckResult("rehearsal.backtest", False, message="rehearsal backtest failed"))

    summary = summarize_checks(checks)
    return {
        "overall_passed": summary["overall_passed"],
        "summary": summary,
        "checks": results_to_dicts(checks),
        "import_dry_run": dry_run,
        "import_output": output,
        "backtest_report": report,
        "calibration_artifact_path": str(calibration_path),
        "analysis_calibration_status": analysis.get("calibration_status"),
        "markdown_report_path": str(markdown_path),
        "warnings": warnings,
    }

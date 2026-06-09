from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.backtesting.backtest_engine import run_backtest
from src.backtesting.historical_loader import load_historical_matches_with_warnings
from src.backtesting.report import build_backtest_report
from src.backtesting.schema import validate_historical_dataset
from src.calibration.persistence import save_calibration_artifact
from src.calibration.store import build_calibration_artifact
from src.exports.backtest_exporter import export_backtest_to_csv, export_backtest_to_xlsx
from src.exports.report_exporter import export_report_to_markdown


DEFAULT_BACKTEST_FIXTURE = Path("data/fixtures/historical_matches_backtest_sample.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="竞彩足球历史回测诊断工具")
    parser.add_argument("--historical-data", default=str(DEFAULT_BACKTEST_FIXTURE))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--min-train-matches", type=int, default=20)
    parser.add_argument("--min-ev", type=float, default=0.04)
    parser.add_argument("--min-edge", type=float, default=0.025)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--export", choices=["csv", "xlsx"], default=None)
    parser.add_argument("--save-calibration", default=None)
    parser.add_argument("--report-md", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        matches, warnings = load_historical_matches_with_warnings(args.historical_data)
        data_summary = validate_historical_dataset(matches)
        result = run_backtest(
            matches,
            start_date=args.start_date,
            end_date=args.end_date,
            min_train_matches=args.min_train_matches,
            strategy_config={"min_ev": args.min_ev, "min_edge": args.min_edge},
        )
        result["data_summary"] = data_summary
        result["warnings"] = list(dict.fromkeys(warnings + data_summary.get("warnings", []) + result.get("warnings", [])))
        report = build_backtest_report(result)
        if args.export:
            output_dir = Path("exports_output")
            output_dir.mkdir(exist_ok=True)
            stem = "backtest_report"
            if args.export == "csv":
                report["export_file"] = export_backtest_to_csv(report, str(output_dir / f"{stem}.csv"))
            else:
                report["export_file"] = export_backtest_to_xlsx(report, str(output_dir / f"{stem}.xlsx"))
        if args.save_calibration:
            try:
                artifact = build_calibration_artifact(report, report.get("model_version", "unknown"))
                report["calibration_artifact_path"] = save_calibration_artifact(artifact, args.save_calibration)
            except Exception as exc:
                report.setdefault("warnings", []).append(f"calibration artifact save failed: {str(exc)[:180]}")
        if args.report_md:
            try:
                report["report_markdown_path"] = export_report_to_markdown(report, args.report_md)
            except Exception as exc:
                report.setdefault("warnings", []).append(f"markdown report export failed: {str(exc)[:180]}")
    except Exception as exc:
        report = _error_report(exc)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report)
    return 0


def _error_report(exc: Exception) -> dict:
    return {
        "model_version": "phase2c_backtest_market_poisson_elo_v0",
        "data_summary": {},
        "matches_total": 0,
        "matches_evaluated": 0,
        "matches_skipped": 0,
        "bets_total": 0,
        "metrics": {},
        "calibration": {},
        "warnings": [f"backtest failed: {str(exc)[:180]}"],
        "disclaimer": "Backtest results are research diagnostics and do not guarantee future outcomes.",
    }


def _print_text(report: dict) -> None:
    print(f"模型版本: {report.get('model_version')}")
    print(f"评估场次: {report.get('matches_evaluated')} | 下注样本: {report.get('bets_total')}")
    metrics = report.get("metrics", {})
    print(f"ROI: {metrics.get('roi', 0)} | PnL: {metrics.get('pnl', 0)} | Hit: {metrics.get('hit_rate', 0)}")
    if report.get("export_file"):
        print(f"导出文件: {report['export_file']}")
    for warning in report.get("warnings", []):
        print(f"- {warning}")
    print(report.get("disclaimer", ""))


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.version import get_build_info

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixture-based local sample workflow")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--write-report", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_sample_workflow(args.write_report)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report)
    return 0 if report["overall_passed"] else 1


def run_sample_workflow(write_report: str | None = None) -> dict:
    steps = []
    normalized = "data/normalized/sample_workflow_normalized.csv"
    calibration = "artifacts/calibration/sample_workflow_calibration.json"
    steps.append(_command("import dry-run", [sys.executable, "-m", "src.cli.import_history", "--input", "data/fixtures/import_sample_generic.csv", "--dry-run", "--format", "json"]))
    steps.append(_command("normalized output", [sys.executable, "-m", "src.cli.import_history", "--input", "data/fixtures/import_sample_generic.csv", "--output", normalized, "--format", "json"]))
    steps.append(_command("backtest fixture", [sys.executable, "-m", "src.cli.backtest", "--historical-data", "data/fixtures/historical_matches_backtest_sample.csv", "--format", "json"]))
    steps.append(_command("save calibration", [sys.executable, "-m", "src.cli.backtest", "--historical-data", "data/fixtures/historical_matches_backtest_sample.csv", "--save-calibration", calibration, "--format", "json"]))
    steps.append(_command("analysis with calibration", [sys.executable, "-m", "src.cli.analyze_tomorrow", "--provider", "mock", "--date", "2026-06-09", "--calibration-artifact", calibration, "--format", "json"]))
    markdown_path = None
    if write_report:
        markdown_path = _write_markdown(write_report, steps, normalized, calibration)
    failed = [item for item in steps if not item["passed"]]
    return {
        "workflow_version": "phase2i_sample_workflow_v0",
        "build_info": get_build_info(),
        "overall_passed": not failed,
        "steps": steps,
        "generated_outputs": {
            "normalized_output": normalized,
            "calibration_artifact": calibration,
            "markdown_report": markdown_path,
        },
        "summary": "Fixture workflow completed for import, backtest, calibration, and analysis." if not failed else "Fixture workflow had failures.",
        "warnings": [],
        "disclaimer": "Sample workflow uses fixtures and does not guarantee prediction accuracy or future outcomes.",
    }


def _command(name: str, command: list[str]) -> dict:
    env = os.environ.copy()
    env.pop("FOOTBALL_JC_LLM_ENABLED", None)
    env.pop("DEEPSEEK_API_KEY", None)
    try:
        completed = subprocess.run(command, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, timeout=120)
        return {"name": name, "passed": completed.returncode == 0, "returncode": completed.returncode, "stderr_tail": completed.stderr[-500:]}
    except Exception as exc:
        return {"name": name, "passed": False, "returncode": None, "stderr_tail": str(exc)[:180]}


def _write_markdown(output_path: str, steps: list[dict], normalized: str, calibration: str) -> str:
    path = PROJECT_ROOT / output_path
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Sample Workflow Report",
        "",
        f"Generated: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
        "",
        "## Steps",
    ]
    for step in steps:
        lines.append(f"- {'PASS' if step['passed'] else 'FAIL'} {step['name']}")
    lines.extend(
        [
            "",
            "## Generated Outputs",
            f"- normalized output: {normalized}",
            f"- calibration artifact: {calibration}",
            "",
            "## Safety",
            "- 仅供数据研究与娱乐参考。",
            "- 不提供投注、下单、支付、代购或任何自动化购彩能力。",
            "- 概率模型不保证结果。",
            "- 回测结果不保证未来表现。",
            "- 串关会显著放大风险。",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _print_text(report: dict) -> None:
    print("football-jc-analysis sample workflow")
    print(f"Overall passed: {report['overall_passed']}")
    for step in report["steps"]:
        print(f"- {'PASS' if step['passed'] else 'FAIL'} {step['name']}")
    print(report["summary"])


if __name__ == "__main__":
    raise SystemExit(main())

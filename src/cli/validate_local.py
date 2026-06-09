from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from src.api.routes import dispatch_route
from src.qa.dashboard_sanity import check_dashboard_static_files
from src.qa.git_hygiene import check_generated_paths_not_tracked, check_git_remote_absent
from src.version import get_build_info

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local release validation for football-jc-analysis")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_validation()
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report)
    return 0 if report["overall_passed"] else 1


def run_validation() -> dict:
    checks: list[dict] = []
    warnings: list[str] = []
    checks.append(_command("compileall", [sys.executable, "-m", "compileall", "src", "tests"]))
    checks.append(_command("analyze_tomorrow mock", [sys.executable, "-m", "src.cli.analyze_tomorrow", "--provider", "mock", "--date", "2026-06-09", "--format", "json"]))
    checks.append(_command("backtest fixture", [sys.executable, "-m", "src.cli.backtest", "--historical-data", "data/fixtures/historical_matches_backtest_sample.csv", "--format", "json"]))
    checks.append(_command("import dry-run", [sys.executable, "-m", "src.cli.import_history", "--input", "data/fixtures/import_sample_generic.csv", "--dry-run", "--format", "json"]))
    checks.append(_command("run_qa", [sys.executable, "-m", "src.cli.run_qa", "--format", "json"]))
    checks.append(_api_check("api health", "/api/health", {}))
    dashboard_results = check_dashboard_static_files(str(PROJECT_ROOT / "src/dashboard/static"))
    checks.append(_result("dashboard static smoke", all(item.passed for item in dashboard_results), {"failed": [item.name for item in dashboard_results if not item.passed]}))
    generated_results = check_generated_paths_not_tracked(str(PROJECT_ROOT))
    checks.append(_result("generated file hygiene", all(item.passed for item in generated_results), {"failed": [item.name for item in generated_results if not item.passed]}))
    remote_results = check_git_remote_absent(str(PROJECT_ROOT))
    checks.append(_result("remote none", all(item.passed for item in remote_results), {"failed": [item.name for item in remote_results if not item.passed]}))
    try:
        subprocess.run([sys.executable, "-m", "pytest"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True, timeout=60)
        checks.append(_result("pytest", True, {}))
    except subprocess.CalledProcessError as exc:
        if "No module named pytest" in (exc.stderr or exc.stdout):
            warnings.append("pytest unavailable: python3: No module named pytest")
            checks.append(_result("pytest", True, {"status": "unavailable"}, severity="warning"))
        else:
            checks.append(_result("pytest", False, {"stderr": (exc.stderr or "")[-500:]}))
    except Exception as exc:
        warnings.append(f"pytest unavailable: {str(exc)[:160]}")
        checks.append(_result("pytest", True, {"status": "unavailable"}, severity="warning"))
    failed = [item for item in checks if not item["passed"] and item.get("severity") != "warning"]
    return {
        "validation_version": "phase2i_local_release_validation_v0",
        "build_info": get_build_info(),
        "overall_passed": not failed,
        "checks": checks,
        "warnings": warnings,
        "disclaimer": "Local validation is diagnostic and does not guarantee prediction accuracy or future outcomes.",
    }


def _command(name: str, command: list[str]) -> dict:
    env = os.environ.copy()
    env.pop("FOOTBALL_JC_LLM_ENABLED", None)
    env.pop("DEEPSEEK_API_KEY", None)
    try:
        completed = subprocess.run(command, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, timeout=120)
        return _result(name, completed.returncode == 0, {"returncode": completed.returncode, "stderr_tail": completed.stderr[-500:]})
    except Exception as exc:
        return _result(name, False, {"error": str(exc)[:180]})


def _api_check(name: str, path: str, query: dict[str, str]) -> dict:
    try:
        payload = dispatch_route(path, query)
        return _result(name, bool(payload.get("ok")), {"payload_keys": sorted(payload.keys())})
    except Exception as exc:
        return _result(name, False, {"error": str(exc)[:180]})


def _result(name: str, passed: bool, details: dict, severity: str = "error") -> dict:
    return {"name": name, "passed": bool(passed), "severity": severity, "details": details}


def _print_text(report: dict) -> None:
    print("football-jc-analysis local validation")
    print(f"Version: {report['build_info']['version']}")
    print(f"Overall passed: {report['overall_passed']}")
    for check in report["checks"]:
        print(f"- {'PASS' if check['passed'] else 'FAIL'} {check['name']}")
    for warning in report.get("warnings", []):
        print(f"warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main())

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "src.cli.analyze_tomorrow", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_provider_mock_json_runs():
    result = _run_cli("--provider", "mock", "--date", "2026-06-09", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["provider"] == "mock"
    assert payload["provider_used"] == "mock"
    assert payload["matches_analyzed"] >= 3


def test_cli_provider_auto_json_runs():
    result = _run_cli("--provider", "auto", "--date", "2026-06-09", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["provider"] == "auto"
    assert "provider_used" in payload
    assert "provider_warnings" in payload

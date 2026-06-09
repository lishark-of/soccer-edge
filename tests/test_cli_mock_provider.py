import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = "data/fixtures/historical_matches_sample.csv"


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
    assert payload["historical_data_status"] == "fixture"


def test_cli_provider_auto_json_runs():
    result = _run_cli("--provider", "auto", "--date", "2026-06-09", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["provider"] == "auto"
    assert "provider_used" in payload
    assert "provider_warnings" in payload
    assert payload["model_version"] == "phase2b_market_poisson_elo_v0"


def test_cli_fixture_historical_json_runs():
    result = _run_cli(
        "--provider", "mock",
        "--date", "2026-06-09",
        "--historical-data", FIXTURE_PATH,
        "--format", "json",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["historical_data_status"] == "loaded"
    assert "poisson" in payload["model_components_available"]


def test_cli_no_historical_fixture_json_runs():
    result = _run_cli(
        "--provider", "mock",
        "--date", "2026-06-09",
        "--no-historical-fixture",
        "--format", "json",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["historical_data_status"] == "disabled"
    assert payload["model_components_available"] == ["market"]

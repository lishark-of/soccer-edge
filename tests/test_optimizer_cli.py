import json
import subprocess
import sys


def test_optimize_today_cli_json_shape():
    result = subprocess.run([sys.executable, "-m", "src.cli.optimize_today", "--provider", "mock", "--date", "2026-06-09", "--bankroll", "10000", "--format", "json"], check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    assert payload["bankroll"] == 10000
    assert "recommended_observation_portfolio" in payload
    assert "daily_exposure_cap" in payload

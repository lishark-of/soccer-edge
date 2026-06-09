import json
import subprocess
import sys


def test_backtest_cli_fixture_json_runs():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli.backtest",
            "--historical-data",
            "data/fixtures/historical_matches_backtest_sample.csv",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["model_version"] == "phase2c_backtest_market_poisson_elo_v0"

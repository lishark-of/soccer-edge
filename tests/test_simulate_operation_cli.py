import json
import subprocess
import sys


def test_simulate_operation_cli_json_shape():
    result = subprocess.run([sys.executable, "-m", "src.cli.simulate_operation", "--historical-data", "data/fixtures/operation_walkforward_sample.csv", "--initial-bankroll", "10000", "--format", "json"], check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    assert payload["simulation_version"] == "phase2l_paper_operation_v0"
    assert "final_bankroll" in payload

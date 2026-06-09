import json
import subprocess
import sys


def test_import_cli_dry_run_json():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli.import_history",
            "--input",
            "data/fixtures/import_sample_generic.csv",
            "--dry-run",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["rows_normalized"] >= 10

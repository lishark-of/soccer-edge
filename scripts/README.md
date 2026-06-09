# Scripts

This release does not require shell scripts. Prefer Python module commands:

```bash
python3 -m src.cli.launch_app
python3 -m src.cli.validate_local --format text
python3 -m src.cli.sample_workflow --format json
```

Generated outputs belong under ignored directories such as `reports/`, `artifacts/`, and `data/normalized/`.

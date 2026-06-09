# Calibration Guide

Calibration artifacts store diagnostic reliability tables generated from a backtest. They are JSON files intended to help inspect probability behavior, not to guarantee future outcomes.

## Generate An Artifact

```bash
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --save-calibration artifacts/calibration/sample_calibration.json --format json
```

The artifact contains model version, source sample counts, calibration bins, selected metrics, and warnings.

## Load In Analysis

```bash
python3 -m src.cli.analyze_tomorrow --provider mock --date 2026-06-09 --calibration-artifact artifacts/calibration/sample_calibration.json --format json
```

The analysis output reports `calibration_status` as `loaded`, `invalid`, or `not_provided`.

## Current Behavior

Phase 2-D keeps calibration conservative. The artifact is validated and loaded as a diagnostic input, while probability adjustment remains lightweight and normalized.

## Safety

Calibration is diagnostic and does not guarantee future performance. It is not betting advice and does not provide投注、下单、支付、代购或任何自动化购彩能力。

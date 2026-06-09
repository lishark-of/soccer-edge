# Real Data Rehearsal Guide

Real-data rehearsal is a local dry-run style workflow for checking whether a user-provided CSV can pass import, normalization, backtest diagnostics, calibration artifact generation, and report QA.

## Prepare CSV

Use a local CSV with date, league, home team, away team, score, and optional 1X2 odds. Do not commit user-provided raw datasets.

## Dry Run Import

```bash
python3 -m src.cli.import_history --input data/fixtures/rehearsal_real_like_generic.csv --dry-run --format json
```

## Normalized Output

Generated normalized files should go under `data/normalized/`, which is ignored by Git.

## Rehearsal Runner

```bash
python3 -m src.cli.run_qa --rehearsal --format json
```

The runner generates ignored files under `data/normalized/`, `artifacts/`, and `reports/`.

## Safety

This project does not connect to lottery platforms and does not provide投注、下单、支付、代购或任何自动化购彩能力。概率模型不保证结果。回测结果不保证未来表现。串关会显著放大风险。

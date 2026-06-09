# football-jc-analysis 0.1.0-local Release Notes

`football-jc-analysis` is a local read-only football probability analysis and backtesting tool.

## What it can do

- Load mock and Sporttery-style provider data.
- Convert odds into market implied probability and no-vig probability.
- Build baseline market / Poisson / Elo probability estimates.
- Run single-match 1X2 backtest diagnostics.
- Import local historical CSV files through dry-run and normalized workflows.
- Save and validate calibration artifacts.
- Open a local dashboard for analysis, import preview, calibration, QA, and probability backtest views.
- Use local deterministic explanations by default.
- Optionally use DeepSeek for natural-language explanations when explicitly enabled with environment variables.

## What it cannot do

- It does not place orders.
- It does not process payments.
- It does not manage accounts.
- It does not proxy purchases.
- It does not automate lottery workflows.
- It does not guarantee outcomes.

## Quick start

```bash
python3 -m src.cli.launch_app
```

Open:

```text
http://127.0.0.1:8766
```

## Import data

Start with dry-run preview:

```bash
python3 -m src.cli.import_history --input data/fixtures/import_sample_generic.csv --dry-run --format json
```

User-provided real datasets should stay local and should not be committed to Git.

## Probability backtest

```bash
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --format json
```

Backtest results are diagnostics and do not guarantee future performance.

## DeepSeek optional explainer

DeepSeek is disabled by default. It only explains existing results and does not affect probability calculation, candidate selection, EV, or backtest metrics.

## Known limitations

- Baseline model only.
- Fixture data is not production data.
- Sporttery live API may fail depending on network/API availability.
- Local release only; no GitHub remote is attached.

## Safety

仅供数据研究与娱乐参考。  
不提供投注、下单、支付、代购或任何自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

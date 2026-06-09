# football-jc-analysis

`football-jc-analysis` is a research-oriented tool for China Sporttery football analysis. It turns match odds into implied probabilities, removes margin, applies a conservative placeholder model, detects positive EV directions, and builds single / `2串1` / `3串1` candidate combinations.

This project is not a betting platform. It does not place orders, handle payments, manage accounts, or claim guaranteed profit.

## Phase 2-D: Import Adapters + Calibration Persistence + Report Hardening

Status: implemented

新增：
- generic CSV import adapter
- sporttery-style export adapter
- football_data-style adapter
- field mapping JSON support
- import dry-run
- normalized historical CSV output
- import manifest with sha256
- data quality report
- calibration artifact save/load
- analyze_tomorrow calibration artifact loading
- Markdown report export

示例：

```bash
python3 -m src.cli.import_history --input data/fixtures/import_sample_generic.csv --dry-run --format json
python3 -m src.cli.import_history --input data/fixtures/import_sample_sporttery.csv --adapter sporttery_export --mapping data/fixtures/import_field_mapping_example.json --dry-run --format json
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --save-calibration artifacts/calibration/sample_calibration.json --format json
python3 -m src.cli.analyze_tomorrow --provider mock --date 2026-06-09 --calibration-artifact artifacts/calibration/sample_calibration.json --format json
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --report-md reports/backtest_sample.md --format json
```

限制：
- import fixtures 仅用于流程测试；
- calibration artifact 是诊断辅助，不保证未来表现；
- 不提供自动投注、支付、下单或代购能力。

## Phase 2-C: Backtesting + Calibration Diagnostics

Status: implemented

新增：
- flexible historical ingestion
- historical schema validation
- single-match 1X2 backtest engine
- value-bet baseline strategy
- flat stake ROI / PnL / hit rate metrics
- Brier score and log loss
- max drawdown
- calibration / reliability bins
- backtest CLI
- backtest CSV/XLSX export

示例：

```bash
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --format json
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --start-date 2026-05-15 --end-date 2026-06-09 --format json
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --export xlsx
```

限制：
- backtest fixture 仅用于流程测试；
- 回测结果不保证未来表现；
- calibration 只是诊断，不保证未来表现；
- 当前策略是 baseline；
- 不提供自动投注、支付、下单或代购能力。

## Phase 2-B: Historical + Poisson/Elo Baseline

Status: implemented

新增：
- historical CSV loader
- fixture historical dataset
- team strength baseline
- Poisson scoreline model
- simplified Elo model
- market / poisson / elo ensemble
- CLI model_components output
- no-future-leakage tests

运行示例：

```bash
python3 -m src.cli.analyze_tomorrow --provider mock --date 2026-06-09 --format json
python3 -m src.cli.analyze_tomorrow --provider mock --date 2026-06-09 --historical-data data/fixtures/historical_matches_sample.csv --format json
python3 -m src.cli.analyze_tomorrow --provider mock --date 2026-06-09 --no-historical-fixture --format json
```

限制：
- fixture 历史数据只用于开发与测试，不适合生产推断；
- 当前模型是 baseline，不构成投注建议；
- 概率不保证结果；
- 串关风险显著高于单关。

## Phase 2-A: Provider Layer

Status: implemented

新增：
- mock provider
- sporttery provider
- auto fallback provider
- CLI `--provider mock|sporttery|auto`
- `provider_used` / `provider_warnings` JSON output

## Development

安装测试依赖：

```bash
python3 -m pip install -r requirements-dev.txt
```

运行测试：

```bash
python3 -m pytest
```

## Repository status

当前项目建议作为独立 Git 仓库管理。

若要同步到 GitHub，请先创建远程仓库，然后手动添加 remote：

```bash
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Safety Notice

仅供数据研究与娱乐参考。
不提供投注、下单、支付、代购或任何自动化购彩能力。
概率模型不保证结果。
回测结果不保证未来表现。
串关会显著放大风险。

Every report must include:

- `仅供数据研究与娱乐参考`
- `概率模型不保证结果`
- `串关会显著放大风险`
- `请勿投入无法承受损失的资金`

The tool must never output:

- `必中`
- `稳赚`
- `保本`
- `回血`
- `杀庄`
- `自动投注`

## Known limitations

- baseline model only
- fixture historical data is not production data
- `sporttery` live API may fail depending on network/API availability
- no REST API yet
- project is local-only and not attached to Git/GitHub
- no GitHub remote attached

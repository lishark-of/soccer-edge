# football-jc-analysis

本地只读的竞彩足球概率分析与回测工具。

它可以：
- 查看 mock / sporttery provider 数据；
- 计算市场去水概率；
- 生成模型概率基线；
- 进行概率回测；
- 导入历史 CSV；
- 生成校准 artifact；
- 打开本地 Dashboard；
- 使用本地解释器解释候选信号和风险；
- 可选接入 DeepSeek 做自然语言解释，但默认关闭。

它不可以：
- 不投注；
- 不下单；
- 不支付；
- 不代购；
- 不自动化购彩；
- 不承诺命中；
- 不保证收益。

## Quick Start

启动本地 App：

```bash
python3 -m src.cli.launch_app
```

打开：

```text
http://127.0.0.1:8766
```

本地验证：

```bash
python3 -m src.cli.validate_local --format text
```

Sample workflow：

```bash
python3 -m src.cli.sample_workflow --format json
```

## Release

- version: `0.1.0-local`
- mode: local read-only
- remote: none
- tag: `v0.1.0-local`

This project is not a betting platform. It does not place orders, handle payments, manage accounts, or claim guaranteed profit.

## Phase 2-I: Release Packaging + Onboarding

Status: implemented

新增：
- project version metadata
- CHANGELOG
- RELEASE_NOTES
- onboarding guide
- local app quickstart
- release checklist
- sample workflow guide
- launch_app CLI
- validate_local CLI
- sample_workflow CLI
- local release tag support

示例：

```bash
python3 -m src.cli.launch_app
python3 -m src.cli.validate_local --format json
python3 -m src.cli.sample_workflow --write-report reports/sample_workflow.md --format json
```

限制：
- local release only；
- 不提供投注、下单、支付、代购或任何自动化购彩能力；
- DeepSeek optional and disabled by default；
- no GitHub remote attached；
- no push performed。

## Phase 2-H: Optional DeepSeek Explainer

Status: implemented

新增：
- DeepSeek config loader
- DeepSeek client with injectable transport
- prompt builder
- safety filter
- optional DeepSeek explainer
- fallback to local explainer
- `/api/llm/status` endpoint
- dashboard DeepSeek status panel
- LLM safety QA

默认行为：
- DeepSeek 默认关闭；
- 默认不发外部请求；
- 不需要 API Key 也能完整使用本地 App；
- DeepSeek 只用于自然语言解释；
- DeepSeek 不参与概率计算、候选筛选、EV、回测指标；
- DeepSeek 不保证结果。

启用方式：

```bash
export FOOTBALL_JC_LLM_ENABLED=true
export FOOTBALL_JC_LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=<your-api-key>
export DEEPSEEK_MODEL=deepseek-v4-flash
```

然后启动本地 API / Dashboard。

安全说明：
- 不要把 API Key 写入 Git；
- 不要把 API Key 写入报告；
- 不要在浏览器中输入 API Key；
- 任何 LLM 输出都会经过安全过滤；
- 不安全输出会 fallback 到本地解释。

## Phase 2-G: User-Facing App + Probability Backtest UX

Status: implemented

新增：
- user-facing local dashboard app
- Chinese explanation-first UI
- analysis summary cards
- candidate signal tables
- parlay risk explanation
- probability backtest page
- metric explanations
- calibration status page
- import preview page
- QA status page
- dashboard-friendly API view endpoints
- local deterministic explainer
- optional LLM/DeepSeek explainer stub, disabled by default

启动 API：

```bash
python3 -m src.cli.serve_api --host 127.0.0.1 --port 8765
```

启动 App：

```bash
python3 -m src.cli.serve_dashboard --host 127.0.0.1 --port 8766 --api-base http://127.0.0.1:8765
```

打开：

```text
http://127.0.0.1:8766
```

DeepSeek 说明：
- 当前阶段不默认接入 DeepSeek；
- 当前解释层使用本地 deterministic explainer；
- DeepSeek 仅作为后续可选解释增强；
- 如需接入，需要用户明确提供 API Key 和授权；
- 任何 LLM 输出都必须经过安全过滤，不得生成投注承诺。

限制：
- App 是本地只读；
- 不提供投注、下单、支付、代购或自动化购彩能力；
- 概率模型不保证结果；
- 回测结果不保证未来表现；
- 串关风险显著放大。

## Phase 2-F: QA Harness + Real-Data Rehearsal

Status: implemented

新增：
- QA harness
- model probability sanity checks
- report/disclaimer QA
- API envelope QA
- dashboard static safety QA
- generated-file / git hygiene QA
- sample real-data import rehearsal
- end-to-end rehearsal runner
- QA CLI
- QA Markdown report

示例：

```bash
python3 -m src.cli.run_qa --format json
python3 -m src.cli.run_qa --rehearsal --format json
python3 -m src.cli.run_qa --rehearsal --write-report reports/qa_report.md --format json
```

限制：
- QA rehearsal 使用 fixture，不代表真实生产数据；
- QA 通过不代表预测准确；
- 回测结果不保证未来表现；
- 不提供投注、下单、支付、代购或自动化购彩能力。

## Phase 2-E: Local Read-Only API + Dashboard

Status: implemented

新增：
- local read-only REST API
- local static dashboard
- health/info endpoints
- analyze endpoint
- backtest endpoint
- import preview endpoint
- calibration artifact validation endpoint
- standardized JSON response envelope
- read-only guard
- API and dashboard docs

示例：

```bash
python3 -m src.cli.serve_api --host 127.0.0.1 --port 8765
python3 -m src.cli.serve_dashboard --host 127.0.0.1 --port 8766 --api-base http://127.0.0.1:8765
```

API 示例：

```text
http://127.0.0.1:8765/api/health
http://127.0.0.1:8765/api/analyze?provider=mock&date=2026-06-09
http://127.0.0.1:8765/api/backtest?historical_data=data/fixtures/historical_matches_backtest_sample.csv
```

限制：
- API 默认只监听 127.0.0.1；
- API 和 dashboard 默认只读；
- 不提供投注、下单、支付、代购或自动化购彩能力；
- 不做公网部署；
- 不保证预测结果；
- 回测结果不保证未来表现。

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
- local read-only REST API exists, but no public deployment is provided
- project is local-only and not attached to Git/GitHub
- no GitHub remote attached

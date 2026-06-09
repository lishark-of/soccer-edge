# football-jc-analysis

`football-jc-analysis` is a research-oriented tool for China Sporttery football analysis. It turns match odds into implied probabilities, removes margin, applies a conservative placeholder model, detects positive EV directions, and builds single / `2串1` / `3串1` candidate combinations.

This project is not a betting platform. It does not place orders, handle payments, manage accounts, or claim guaranteed profit.

## Phase 2-A: Provider Layer

Status: implemented

新增：
- mock provider
- sporttery provider
- auto fallback provider
- CLI `--provider mock|sporttery|auto`
- `provider_used` / `provider_warnings` JSON output

运行示例：

```bash
python3 -m src.cli.analyze_tomorrow --provider auto --date 2026-06-09 --format json
python3 -m src.cli.analyze_tomorrow --provider mock --date 2026-06-09 --format json
python3 -m src.cli.analyze_tomorrow --provider sporttery --date 2026-06-09 --format json
```

## Phase 1 MVP

Phase 1 includes:

- provider abstraction with a built-in mock provider
- implied probability and no-vig probability
- placeholder ensemble probability model
- EV and edge calculation
- single / `2串1` / `3串1` candidate generation
- CLI output
- CSV/XLSX export
- tests

## Structure

```text
football-jc-analysis/
  README.md
  AGENTS.md
  pyproject.toml
  .env.example
  docs/
  src/
  tests/
```

## Run

From `/Users/shark-li/Documents/足球⚽️/football-jc-analysis`:

```bash
python3 -m src.cli.analyze_tomorrow
python3 -m src.cli.analyze_tomorrow --date 2026-06-09
python3 -m src.cli.analyze_tomorrow --format json
python3 -m src.cli.analyze_tomorrow --export xlsx
python3 -m src.cli.analyze_tomorrow --provider auto
python3 -m src.cli.analyze_tomorrow --provider mock
python3 -m src.cli.analyze_tomorrow --provider sporttery
```

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

- project is local-only and not attached to Git/GitHub
- `sporttery` live API may fail depending on network/API availability
- model remains a conservative placeholder
- Poisson / Elo are not implemented in this phase
- REST API is not implemented in this phase

## Optional local preview

A local preview server already exists, but it is not the focus of Phase 2-A:

```bash
python3 -m src.api.app
```

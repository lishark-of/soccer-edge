# Onboarding Guide

## 项目用途

`football-jc-analysis` 是本地只读的竞彩足球概率分析与回测工具。它帮助你用 mock 或本地历史数据体验赔率概率、模型基线、回测诊断、导入预检和本地 Dashboard。

## 本地只读安全边界

- 不提供投注、下单、支付、代购或任何自动化购彩能力。
- 不承诺命中。
- 不保证收益。
- 不默认调用 DeepSeek 或任何外部 LLM。
- 不连接 GitHub remote。

## 安装前检查

建议使用 Python 3.11+。如需运行 pytest，请安装开发依赖：

```bash
python3 -m pip install -r requirements-dev.txt
```

## 快速启动

```bash
python3 -m src.cli.launch_app
```

打开：

```text
http://127.0.0.1:8766
```

## 使用 mock 数据体验

在 Dashboard 里点击“先看 mock 分析”，或运行：

```bash
python3 -m src.cli.analyze_tomorrow --provider mock --date 2026-06-09 --format json
```

## 导入自己的历史 CSV

先 dry-run：

```bash
python3 -m src.cli.import_history --input your_local_history.csv --dry-run --format json
```

不要提交真实数据。建议放在 `data/raw/` 或 `data/imports/`，这些目录已被忽略。

## 运行回测

```bash
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --format json
```

## 生成 calibration artifact

```bash
python3 -m src.cli.backtest --historical-data data/fixtures/historical_matches_backtest_sample.csv --save-calibration artifacts/calibration/sample_calibration.json --format json
```

`artifacts/` 已被忽略，不应提交。

## 加载 calibration artifact

```bash
python3 -m src.cli.analyze_tomorrow --provider mock --date 2026-06-09 --calibration-artifact artifacts/calibration/sample_calibration.json --format json
```

## 查看 QA

```bash
python3 -m src.cli.run_qa --format json
python3 -m src.cli.validate_local --format text
```

## DeepSeek 可选解释层

DeepSeek 默认关闭。若未来启用，只用于自然语言解释，不参与概率计算、候选筛选、EV 或回测指标。不要把 API Key 写进 Git、报告或浏览器输入框。

## 常见问题

- API 未启动：先运行 `python3 -m src.cli.launch_app`。
- Sporttery live API 失败：可用 `--provider mock` 或 `--provider auto` fallback。
- pytest unavailable：安装 `requirements-dev.txt`。
- 看不到校准状态：先生成 calibration artifact。

## Safety

仅供数据研究与娱乐参考。  
不提供投注、下单、支付、代购或任何自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

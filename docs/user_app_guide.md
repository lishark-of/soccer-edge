# User App Guide

Phase 2-G adds a local, read-only dashboard for `football-jc-analysis`.

## Start the local API

```bash
python3 -m src.cli.serve_api --host 127.0.0.1 --port 8765
```

The API is local-only by default and should not be exposed publicly.

## Start the App

```bash
python3 -m src.cli.serve_dashboard --host 127.0.0.1 --port 8766 --api-base http://127.0.0.1:8765
```

Open:

```text
http://127.0.0.1:8766
```

## Pages

- 总览: service status, read-only mode, analysis/backtest/import/calibration/QA availability.
- 指定日期分析: summary cards and model component explanations.
- 候选买点: model signal table with odds, market probability, model probability, Edge, EV, risk level, and local explanation.
- 组合风险: `2串1` / `3串1` diagnostic combinations and risk notes.
- 概率回测: hit rate, ROI, PnL, Brier Score, Log Loss, max drawdown, calibration bins, and simulated historical rows.
- 数据导入预检: dry-run import preview, quality report, and manifest summary.
- 校准状态: local calibration artifact validation.
- QA 健康检查: QA summary, warnings, and failed checks.
- 原始 JSON: latest API response for debugging.

## How to read candidate signals

A candidate signal means the model and market disagree under the current baseline assumptions. It is not a deterministic instruction and does not guarantee any result.

## How to read risk level

Risk level summarizes model uncertainty, odds range, confidence, and combination effects. Parlay-style combinations multiply uncertainty and can amplify volatility.

## Warnings

Warnings should be read before interpreting any card or table. Fixture datasets are development samples and are not production historical data.

## Safety

仅供数据研究与娱乐参考。  
不提供投注、下单、支付、代购或任何自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

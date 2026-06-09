# LLM Safety Guide

Phase 2-H keeps LLM output behind safety gates.

## Prompt rules

The system prompt requires the explainer to:

- explain only probability, risk, and backtest diagnostics;
- avoid betting instructions;
- avoid guaranteed-outcome language;
- explain that probability models do not guarantee results;
- explain that backtests do not guarantee future performance;
- explain that parlays amplify risk.

## Banned output terms

The safety filter rejects or falls back when output contains terms such as:

- 必中
- 稳赢
- 稳赚
- 杀庄
- 保本
- 回血
- 倍投
- 追号
- 自动投注
- 代下单
- 支付购彩

## Output filtering

LLM output must pass `validate_explanation_safety`. Unsafe output is not shown; the app uses local deterministic explanation instead.

## Fallback local

Fallback is required for:

- disabled LLM mode;
- missing API key;
- client errors;
- invalid JSON or HTTP errors;
- unsafe output.

## Tests and validation

Tests must use fake transport. Validation must not make real DeepSeek calls unless a future user explicitly authorizes it.

## Safety

不允许投注指令。  
不允许保证收益。  
不允许支付、下单或代购能力。  
仅供数据研究与娱乐参考。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

# DeepSeek Integration Guide

Phase 2-H adds DeepSeek as an optional natural-language explainer only.

## Purpose

DeepSeek can explain existing probability, risk, and backtest diagnostics in plain Chinese. It does not calculate probabilities, select candidates, compute EV, or change backtest metrics.

## Default behavior

DeepSeek is disabled by default. The app works fully with the local deterministic explainer.

## Environment variables

```bash
export FOOTBALL_JC_LLM_ENABLED=true
export FOOTBALL_JC_LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=<your-api-key>
export DEEPSEEK_BASE_URL=https://api.deepseek.com
export DEEPSEEK_MODEL=deepseek-v4-flash
export DEEPSEEK_TIMEOUT_SECONDS=20
export DEEPSEEK_MAX_TOKENS=600
```

Do not commit API keys or env files.

## Check status

```text
http://127.0.0.1:8765/api/llm/status
```

The response only exposes `api_key_present` as a boolean. It never returns the key.

## Dashboard mode

The dashboard has an explanation mode selector:

- 本地解释（默认）
- DeepSeek 增强解释（可选）
- 自动回退

Do not enter API keys in the browser. Configure keys only through local environment variables.

## Common statuses

- `disabled`: local explanation is used.
- `missing_api_key`: DeepSeek was requested but no key is present; local explanation is used.
- `fallback_local`: DeepSeek output failed or was unsafe; local explanation is used.
- `loaded`: DeepSeek explanation was used.

## Safety

DeepSeek explanations do not guarantee outcomes and do not constitute betting advice.

仅供数据研究与娱乐参考。  
不提供投注、下单、支付、代购或任何自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

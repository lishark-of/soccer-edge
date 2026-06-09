# AGENTS.md

## Project intent

This project is a football lottery data analysis and probability research tool.
It must not implement wagering, payment, order placement, account management, or gambling automation.

## Safety rules

- Do not add payment features.
- Do not add auto-betting features.
- Do not claim guaranteed profit.
- Do not use phrases such as sure win, guaranteed, must hit, bankroll recovery, or beat the bookmaker.
- Every user-facing report must include probability and risk disclaimers.
- Do not implement wagering, payment, order placement, account management, or gambling automation.

## Coding rules

- Prefer Python 3.11+.
- Use type hints.
- Keep provider logic separate from probability/modeling logic.
- Keep probability/modeling logic separate from presentation.
- Historical features must use only data strictly before target match date.
- Backtests must use chronological evaluation only.
- Backtest results must be framed as diagnostics, not guarantees.
- User-provided raw datasets must not be committed.
- Generated artifacts, reports, normalized outputs, and calibration files must not be committed unless they are explicit fixtures.
- Local API and dashboard must default to read-only mode.
- Local API must bind to 127.0.0.1 by default.
- QA checks must not claim prediction accuracy or guaranteed outcomes.
- QA rehearsal fixtures are not production data.
- Do not add betting, payment, order placement, or proxy purchase UI controls.
- Dashboard must not include betting, payment, order placement, proxy purchase, martingale, or chase controls.
- LLM/DeepSeek integration must be disabled by default and must not make external calls without explicit user authorization.
- LLM/DeepSeek integration must be disabled by default.
- No external LLM calls may occur during tests or validation unless explicitly authorized.
- API keys must never be committed, logged, displayed, or written to reports/artifacts.
- LLM outputs must pass safety filtering and fallback to local explanations on violation.
- Add tests for every probability and ticket-counting function.
- Add tests for provider fallback and odds normalization.
- Add tests for no-future-leakage guards.
- Add tests for import adapters, calibration persistence, and report export.
- Add tests for API health, read-only guard, and dashboard static disclaimers.
- Add tests for QA harness, disclaimer scanning, model sanity, and generated-file hygiene.
- Add tests for user-facing dashboard, local explainer, view models, and probability backtest UX.
- Run tests before final response.

## Testing

Run:

`pytest`

If pytest is not available, document the reason and run the closest available validation.

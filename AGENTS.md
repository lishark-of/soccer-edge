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
- Add tests for every probability and ticket-counting function.
- Add tests for provider fallback and odds normalization.
- Add tests for no-future-leakage guards.
- Add tests for import adapters, calibration persistence, and report export.
- Run tests before final response.

## Testing

Run:

`pytest`

If pytest is not available, document the reason and run the closest available validation.

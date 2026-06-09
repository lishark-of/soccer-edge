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
- Release packaging must remain local-only and must not add a remote or push tags.
- Onboarding docs must keep read-only and no-wagering safety boundaries visible.
- Generated release rehearsal outputs under reports, artifacts, and data/normalized must not be committed.
- User-facing workflows must provide Chinese, actionable errors instead of raw Python tracebacks.
- Dashboard onboarding must guide users through mock analysis, CSV import, field report, backtest, calibration, and analysis.
- API/dashboard remain read-only by default.
- Full user data workflow that writes normalized/calibration/report files must be CLI-only unless explicitly authorized.
- Add tests for every probability and ticket-counting function.
- Add tests for provider fallback and odds normalization.
- Add tests for no-future-leakage guards.
- Add tests for import adapters, calibration persistence, and report export.
- Add tests for API health, read-only guard, and dashboard static disclaimers.
- Add tests for QA harness, disclaimer scanning, model sanity, and generated-file hygiene.
- Add tests for user-facing dashboard, local explainer, view models, and probability backtest UX.
- App UI must use JC Edge as the concise local dashboard name.
- Sporttery views must describe provider fallback clearly and must not imply official partnership.
- User-facing buttons must use observation, signal, probability, risk, preview, or analysis language rather than purchase or order language.
- Observation lists are temporary research aids and must not become wagering slips or persisted purchase plans.
- Run tests before final response.

## Testing

Run:

`pytest`

If pytest is not available, document the reason and run the closest available validation.

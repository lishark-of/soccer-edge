# Changelog

## 0.1.0-local

### Added
- Phase 1 MVP.
- Phase 2-A provider fallback.
- Phase 2-B probability baseline.
- Phase 2-C backtesting diagnostics.
- Phase 2-D import/calibration/reporting.
- Phase 2-E local API/dashboard.
- Phase 2-F QA harness/rehearsal.
- Phase 2-G user-facing dashboard/probability backtest UX.
- Phase 2-H optional DeepSeek explainer, disabled by default.
- Phase 2-I local release packaging and onboarding.

### Safety
- Read-only local mode.
- No betting/payment/order placement/proxy purchase.
- No guaranteed outcomes.
- DeepSeek optional explainer is disabled by default and does not affect probabilities.

### Limitations
- Baseline model only.
- Fixture data is for workflow testing, not production inference.
- Sporttery live API may fail depending on network/API availability.
- Local release only; no GitHub remote and no push performed.

# Local API Guide

The Phase 2-E API is a local read-only interface for `football-jc-analysis`. It is intended for research diagnostics and local inspection only.

## Start

```bash
python3 -m src.cli.serve_api --host 127.0.0.1 --port 8765
```

The default host is `127.0.0.1`. The server refuses non-local hosts in this phase.

## Response Envelope

Success:

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "disclaimer": "For research and entertainment reference only. No outcome is guaranteed."
}
```

Error:

```json
{
  "ok": false,
  "error": {
    "code": "bad_request",
    "message": "..."
  },
  "warnings": [],
  "disclaimer": "For research and entertainment reference only. No outcome is guaranteed."
}
```

## Endpoints

- `GET /api/health`
- `GET /api/info`
- `GET /api/matches?date=YYYY-MM-DD&provider=mock`
- `GET /api/analyze?date=YYYY-MM-DD&provider=mock`
- `GET /api/backtest?historical_data=data/fixtures/historical_matches_backtest_sample.csv`
- `GET /api/import/preview?input=data/fixtures/import_sample_generic.csv&adapter=auto`
- `GET /api/calibration/validate?path=artifacts/calibration/sample_calibration.json`
- `GET /api/report/summary?type=analysis&provider=mock`

## Read-Only Mode

The API does not write files, create reports, create calibration artifacts, place orders, handle payments, or connect to lottery accounts. Write-oriented query parameters return `read_only_violation`.

## Safety

Do not expose this local API publicly. It is not a betting platform and does not provide投注、下单、支付、代购或任何自动化购彩能力。

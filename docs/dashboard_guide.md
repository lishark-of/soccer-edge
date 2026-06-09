# Local Dashboard Guide

The dashboard is a static local page for viewing API output. It uses no external CDN, no npm, no remote fonts, and no external network calls other than the configured local API base.

## Start

```bash
python3 -m src.cli.serve_dashboard --host 127.0.0.1 --port 8766 --api-base http://127.0.0.1:8765
```

Open `http://127.0.0.1:8766` after the API server is running.

## Features

- health check
- match analysis
- backtest diagnostics
- import preview
- calibration artifact validation
- warnings panel
- JSON viewer

## Read-Only Mode

The dashboard displays: `Read-only local analysis mode`. It does not include betting, payment, order placement, proxy purchase, or automation controls.

## Common Errors

- API not started: the dashboard shows a connection error.
- Calibration artifact missing: validation returns `valid=false`.
- Sporttery live API failure: use `provider=mock` or `provider=auto` fallback.

## Safety

仅供数据研究与娱乐参考。概率模型不保证结果。回测结果不保证未来表现。

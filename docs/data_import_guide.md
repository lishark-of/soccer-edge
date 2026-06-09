# Data Import Guide

`football-jc-analysis` imports local historical files for research workflows only. It does not crawl betting sites, connect to lottery accounts, place orders, or provide purchase automation.

## Supported Formats

- CSV via `generic_csv`
- Chinese Sporttery-style CSV exports via `sporttery_export`
- Older football-data-style CSV exports via `football_data`

## Field Mapping

The importer can infer common English and Chinese aliases. You can also provide a JSON mapping:

```json
{
  "date": "比赛日期",
  "league": "赛事",
  "home_team": "主队",
  "away_team": "客队",
  "score": "比分",
  "odds_home": "胜赔",
  "odds_draw": "平赔",
  "odds_away": "负赔"
}
```

## Dry Run

```bash
python3 -m src.cli.import_history --input data/fixtures/import_sample_generic.csv --dry-run --format json
```

Dry-run returns preview, inferred mapping, quality report, and manifest metadata without writing normalized output.

## Normalized Output

```bash
python3 -m src.cli.import_history --input data/fixtures/import_sample_generic.csv --output data/normalized/import_sample_normalized.csv --format json
```

`data/normalized/` is ignored by Git. Do not commit user-provided raw datasets or generated normalized data.

## Quality Report

The report includes sample size, date range, leagues, teams, odds coverage, result distribution, skipped rows, and warnings.

## Safety

仅供数据研究与娱乐参考。概率模型不保证结果。回测结果不保证未来表现。不提供投注平台对接、投注、下单、支付、代购或任何自动化购彩能力。

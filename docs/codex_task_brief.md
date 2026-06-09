# Codex Task Brief

## Goal

Build a research tool for China Sporttery football analysis that:

- fetches match and odds data
- converts odds into implied and no-vig probabilities
- generates conservative model probabilities
- compares model probabilities with market probabilities
- detects positive EV directions
- builds single / `2串1` / `3串1` candidate combinations
- exports research reports

## Reference repositories

- `excalibur-sa/football-lottery`
- `guxima/JINGCAI-lottery-rules-and-calculate`
- `steven0610/football_data`
- `kkpop/FLAnalyzer`
- `G0mmer/football-prediction-2025`
- `vickyfriss/football-league-predictions`
- `czl0325/football_frontend` as limited negative reference

## Phase 1 scope

- mock provider only
- probability calculation
- rules for single / `2串1` / `3串1`
- EV and risk analysis
- CLI
- CSV/XLSX export
- tests

## Hard boundaries

- no payment
- no order placement
- no auto-betting
- no guaranteed-return language
- no regulatory evasion

## Default date

- local timezone `UTC+8`
- default target date is tomorrow
- manual override allowed, for example `2026-06-09`

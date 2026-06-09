from src.backtesting.historical_loader import HistoricalMatch
from src.backtesting.schema import validate_historical_dataset, validate_historical_match


def test_validate_historical_match_detects_bad_scores():
    match = HistoricalMatch("2026-06-01", "League", "A", "B", -1, 0, "H")
    assert "home_goals must be a non-negative integer" in validate_historical_match(match)


def test_validate_historical_dataset_summary():
    matches = [
        HistoricalMatch("2026-06-01", "League", "A", "B", 1, 0, "H", odds_had={"win": 1.8, "draw": 3.2, "lose": 4.0}),
        HistoricalMatch("2026-06-02", "League", "C", "A", 0, 0, "D"),
    ]
    summary = validate_historical_dataset(matches)
    assert summary["matches"] == 2
    assert summary["teams"] == 3

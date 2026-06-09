from src.backtesting.backtest_engine import (
    chronological_split,
    features_use_only_past_matches,
    rolling_feature_shift,
)
from src.backtesting.historical_loader import HistoricalMatch
from src.probability.elo_model import build_elo_ratings


def test_features_use_only_past_matches():
    rows = [
        {"date": "2026-06-01", "value": 1},
        {"date": "2026-06-02", "value": 2},
        {"date": "2026-06-03", "value": 3},
    ]

    assert features_use_only_past_matches(rows) is True


def test_rolling_features_shifted_by_one():
    shifted = rolling_feature_shift([1.0, 2.0, 3.0])

    assert shifted == [None, 1.0, 2.0]


def test_train_test_split_chronological():
    rows = [
        {"date": "2026-06-03", "value": 3},
        {"date": "2026-06-01", "value": 1},
        {"date": "2026-06-02", "value": 2},
        {"date": "2026-06-04", "value": 4},
    ]
    split = chronological_split(rows, train_ratio=0.5)

    assert [item["date"] for item in split.train] == ["2026-06-01", "2026-06-02"]
    assert [item["date"] for item in split.test] == ["2026-06-03", "2026-06-04"]


def test_no_future_leakage_in_elo_build():
    matches = [
        HistoricalMatch("2026-06-01", "Mock", "Alpha", "Beta", 1, 0, "H"),
        HistoricalMatch("2026-06-12", "Mock", "Alpha", "Beta", 9, 0, "H"),
    ]

    ratings = build_elo_ratings(matches, before_date="2026-06-09")

    assert ratings["Alpha"] > 1500.0
    assert ratings["Alpha"] < 1520.0

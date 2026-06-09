from src.backtesting.historical_loader import HistoricalMatch
from src.probability.elo_model import build_elo_ratings, elo_to_1x2_probs, expected_score, update_elo


def test_elo_expected_score_bounds():
    value = expected_score(1500, 1500)

    assert 0.0 < value < 1.0


def test_elo_update_home_win_increases_home_rating():
    home, away = update_elo(1500.0, 1500.0, "H")

    assert home > 1500.0
    assert away < 1500.0


def test_elo_to_1x2_probs_sums_to_one():
    probs = elo_to_1x2_probs(1560.0, 1490.0)

    assert abs(sum(probs.values()) - 1.0) < 1e-6


def test_no_future_leakage_in_elo_build():
    matches = [
        HistoricalMatch("2026-06-01", "Mock", "A", "B", 2, 1, "H"),
        HistoricalMatch("2026-06-10", "Mock", "A", "B", 9, 0, "H"),
    ]

    ratings = build_elo_ratings(matches, before_date="2026-06-09")
    baseline_home, baseline_away = update_elo(1500.0, 1500.0, "H")

    assert round(ratings["A"], 6) == round(baseline_home, 6)
    assert round(ratings["B"], 6) == round(baseline_away, 6)

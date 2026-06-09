from src.backtesting.backtest_engine import run_backtest
from src.backtesting.historical_loader import HistoricalMatch


def test_backtest_engine_uses_only_prior_matches():
    matches = []
    for day in range(1, 24):
        matches.append(HistoricalMatch(f"2026-05-{day:02d}", "L", "A", "B", 1, 0, "H", odds_had={"win": 1.8, "draw": 3.2, "lose": 4.5}))
    future = HistoricalMatch("2026-06-20", "L", "B", "A", 9, 0, "H", odds_had={"win": 1.8, "draw": 3.2, "lose": 4.5})
    report_without_future = run_backtest(matches, min_train_matches=20)
    report_with_future = run_backtest(matches + [future], end_date="2026-05-23", min_train_matches=20)
    assert report_without_future["predictions"] == report_with_future["predictions"]

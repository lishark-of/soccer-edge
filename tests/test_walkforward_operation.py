from src.backtesting.historical_loader import load_historical_matches
from src.paper_trading.walkforward import run_paper_operation_walkforward


def test_walkforward_uses_only_prior_matches():
    matches = load_historical_matches("data/fixtures/operation_walkforward_sample.csv")
    report = run_paper_operation_walkforward(matches, initial_bankroll=10000)
    evaluated_dates = [day["date"] for day in report["daily_ledger"]]
    assert evaluated_dates == sorted(evaluated_dates)
    assert report["skipped_days"] > 0


def test_walkforward_report_has_final_profit():
    matches = load_historical_matches("data/fixtures/operation_walkforward_sample.csv")
    report = run_paper_operation_walkforward(matches, initial_bankroll=10000)
    assert "final_bankroll" in report
    assert "total_profit" in report
    assert "walk_log" in report

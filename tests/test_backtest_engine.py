from src.backtesting.backtest_engine import run_backtest
from src.backtesting.backtest_strategy import select_value_bet
from src.backtesting.historical_loader import HistoricalMatch


def _matches(count=25):
    teams = ["A", "B", "C", "D"]
    rows = []
    for index in range(count):
        home = teams[index % 4]
        away = teams[(index + 1) % 4]
        rows.append(
            HistoricalMatch(
                date=f"2026-05-{index + 1:02d}",
                league="L",
                home_team=home,
                away_team=away,
                home_goals=2 if index % 3 == 0 else 1,
                away_goals=0 if index % 3 == 0 else 1,
                result_1x2="H" if index % 3 == 0 else "D",
                odds_had={"win": 1.9, "draw": 3.2, "lose": 4.2},
            )
        )
    return rows


def test_backtest_engine_skips_until_min_train_matches():
    report = run_backtest(_matches(25), min_train_matches=20)
    assert report["matches_evaluated"] == 5
    assert report["matches_skipped"] == 20


def test_select_value_bet_respects_thresholds():
    match = _matches(1)[0]
    bet = select_value_bet(match, {"win": 0.7, "draw": 0.2, "lose": 0.1}, {"win": 0.5, "draw": 0.3, "lose": 0.2}, {"win": 1.9, "draw": 3.2, "lose": 4.2})
    assert bet and bet["selection"] == "win"

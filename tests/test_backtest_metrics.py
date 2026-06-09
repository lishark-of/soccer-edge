from src.backtesting.metrics import brier_score, calculate_max_drawdown, calculate_pnl, calculate_roi, log_loss


def test_metrics_roi_and_pnl():
    bets = [{"stake": 1, "profit": 0.8}, {"stake": 1, "profit": -1}]
    assert calculate_pnl(bets) == -0.2
    assert calculate_roi(bets) == -0.1


def test_metrics_max_drawdown():
    assert calculate_max_drawdown([1, 3, 2, 4, 1]) == 3


def test_brier_score_bounds():
    value = brier_score([{"actual": "win", "probabilities": {"win": 0.6, "draw": 0.2, "lose": 0.2}}])
    assert 0 <= value <= 2


def test_log_loss_finite():
    value = log_loss([{"actual": "draw", "probabilities": {"win": 0.1, "draw": 0.8, "lose": 0.1}}])
    assert value > 0

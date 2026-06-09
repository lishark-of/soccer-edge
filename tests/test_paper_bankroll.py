from src.paper_trading.bankroll import apply_settlement, create_bankroll


def test_create_bankroll_starts_with_10000():
    bankroll = create_bankroll()
    assert bankroll.initial_bankroll == 10000.0
    assert bankroll.current_bankroll == 10000.0


def test_apply_settlement_updates_profit_and_drawdown():
    bankroll = create_bankroll(10000)
    bankroll = apply_settlement(bankroll, 100, -100)
    assert bankroll.current_bankroll == 9900
    assert bankroll.total_profit == -100
    assert bankroll.max_drawdown > 0

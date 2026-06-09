from src.paper_trading.settlement import settle_parlay_observation, settle_single_observation


def test_settle_single_win_profit():
    result = settle_single_observation({"paper_stake": 100, "odds": 2.5, "outcome_key": "win"}, "win")
    assert result["profit"] == 150
    assert result["hit"] is True


def test_settle_single_loss_profit():
    result = settle_single_observation({"paper_stake": 100, "odds": 2.5, "outcome_key": "win"}, "lose")
    assert result["profit"] == -100
    assert result["hit"] is False


def test_settle_parlay_requires_all_legs():
    observation = {"paper_stake": 50, "combined_odds": 4.0, "legs": [{"match_id": "m1", "outcome_key": "win"}, {"match_id": "m2", "outcome_key": "draw"}]}
    result = settle_parlay_observation(observation, {"m1": "win", "m2": "draw"})
    assert result["profit"] == 150
    assert result["hit"] is True

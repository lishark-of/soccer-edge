from src.optimizer.portfolio_optimizer import optimize_portfolio


def _candidate(i, ev=0.08, edge=0.04, odds=2.1):
    return {"candidate_type": "single", "match_id": f"m{i}", "league": f"L{i}", "home_team": f"H{i}", "away_team": f"A{i}", "outcome_label": "主胜", "odds": odds, "market_prob": 0.45, "model_prob": 0.53, "edge": edge, "ev": ev, "risk_level": "low", "risk_label": "低"}


def test_exposure_cap_and_fractional_kelly_cap():
    result = optimize_portfolio([_candidate(i) for i in range(8)], bankroll=10000)
    assert result["recommended_paper_exposure"] <= 300
    assert all(item["suggested_paper_stake"] <= 100 for item in result["recommended_observation_portfolio"]["singles"])


def test_3x1_disabled_by_default():
    result = optimize_portfolio([_candidate(i) for i in range(5)], bankroll=10000)
    assert result["recommended_observation_portfolio"]["parlay_3x1"] == []

from src.optimizer.portfolio_optimizer import optimize_portfolio


def test_rejected_candidates_include_reason():
    candidates = [
        {"candidate_type": "single", "match_id": "a", "league": "L", "home_team": "A", "away_team": "B", "outcome_label": "主胜", "odds": 1.8, "market_prob": 0.55, "model_prob": 0.56, "edge": 0.01, "ev": 0.008, "risk_level": "low"},
        {"candidate_type": "single", "match_id": "b", "league": "L", "home_team": "C", "away_team": "D", "outcome_label": "主胜", "odds": 2.1, "market_prob": 0.45, "model_prob": 0.53, "edge": 0.08, "ev": 0.113, "risk_level": "low"},
    ]
    result = optimize_portfolio(candidates, bankroll=10000, config={"risk_profile": "conservative"})
    assert result["rejected_candidates"]
    assert all(row.get("reason") for row in result["rejected_candidates"])

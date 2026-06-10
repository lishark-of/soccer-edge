from src.optimizer.portfolio_optimizer import optimize_portfolio


def _candidate(i):
    return {"candidate_type": "single", "match_id": f"m{i}", "league": f"L{i}", "home_team": f"H{i}", "away_team": f"A{i}", "outcome_label": "主胜", "odds": 2.1, "market_prob": 0.45, "model_prob": 0.53, "edge": 0.04, "ev": 0.113, "risk_level": "low"}


def test_profile_comparison_returns_three_profiles():
    result = optimize_portfolio([_candidate(i) for i in range(5)], bankroll=10000, config={"compare_profiles": True})
    assert set(result["profile_comparison"].keys()) == {"conservative", "balanced", "aggressive"}
    assert result["profile_comparison"]["balanced"]["daily_exposure_cap"] == 500

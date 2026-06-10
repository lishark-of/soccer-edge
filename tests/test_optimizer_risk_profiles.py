from src.optimizer.portfolio_optimizer import optimize_portfolio


def _candidate(i, ev=0.08, edge=0.04, odds=2.1):
    return {
        "candidate_type": "single",
        "match_id": f"m{i}",
        "league": f"L{i % 3}",
        "home_team": f"H{i}",
        "away_team": f"A{i}",
        "outcome_label": "主胜",
        "odds": odds,
        "market_prob": 0.45,
        "model_prob": 0.53,
        "edge": edge,
        "ev": ev,
        "risk_level": "low",
        "risk_label": "低",
    }


def test_conservative_profile_limits_exposure():
    result = optimize_portfolio([_candidate(i) for i in range(8)], bankroll=10000, config={"risk_profile": "conservative"})
    assert result["risk_profile"] == "conservative"
    assert result["daily_exposure_cap"] == 300
    assert result["recommended_paper_exposure"] <= 300


def test_balanced_profile_allows_more_2x1_than_conservative():
    candidates = [_candidate(i) for i in range(6)]
    conservative = optimize_portfolio(candidates, bankroll=10000, config={"risk_profile": "conservative"})
    balanced = optimize_portfolio(candidates, bankroll=10000, config={"risk_profile": "balanced"})
    assert len(conservative["selected_portfolio"]["parlay_2x1"]) == 0
    assert len(balanced["selected_portfolio"]["parlay_2x1"]) >= len(conservative["selected_portfolio"]["parlay_2x1"])
    assert balanced["risk_summary"]["profile_limits"]["max_parlay_2x1"] == 2


def test_aggressive_profile_can_include_3x1_when_enabled():
    result = optimize_portfolio([_candidate(i) for i in range(6)], bankroll=10000, config={"risk_profile": "aggressive"})
    assert result["risk_profile"] == "aggressive"
    assert result["risk_summary"]["enable_3x1"] is True
    assert len(result["candidate_rankings"]["parlay_3x1"]) > 0

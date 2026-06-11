from src.optimizer.portfolio_optimizer import optimize_portfolio


def test_rejected_parlay_rankings_include_leg_reasons_when_only_one_single_passes():
    candidates = [
        {
            "candidate_type": "single",
            "match_id": "m1",
            "home_team": "A",
            "away_team": "B",
            "play_type": "had",
            "outcome_label": "主胜",
            "odds": 3.25,
            "market_prob": 0.27,
            "model_prob": 0.416,
            "edge": 0.146,
            "ev": 0.352,
            "risk_level": "medium",
        },
        {
            "candidate_type": "single",
            "match_id": "m2",
            "home_team": "C",
            "away_team": "D",
            "play_type": "hhad",
            "outcome_label": "平",
            "odds": 3.6,
            "market_prob": 0.246,
            "model_prob": 0.259,
            "edge": 0.013,
            "ev": -0.066,
            "risk_level": "high",
        },
    ]
    result = optimize_portfolio(candidates, bankroll=10000, config={"risk_profile": "aggressive"})
    parlay_rows = result["candidate_rankings"]["parlay_2x1"]
    assert parlay_rows
    assert parlay_rows[0]["status"] == "未入选"
    assert "组合腿未全部通过单关纪律" in parlay_rows[0]["reject_reason"]
    assert "胜平负·主胜" in parlay_rows[0]["legs"]
    assert "让球胜平负·平" in parlay_rows[0]["legs"]

from src.optimizer.scoring import score_candidate


def test_longshot_not_parlay_eligible_by_default():
    item = score_candidate({"candidate_type": "single", "odds": 8.0, "model_prob": 0.15, "market_prob": 0.10, "ev": 0.2, "edge": 0.05, "risk_level": "medium"}, 10000, {"single_stake_cap_pct": 0.01, "parlay_2x1_cap_pct": 0.005, "parlay_3x1_cap_pct": 0.0, "kelly_multiplier": 0.25})
    assert item["risk_level"] == "very_high"
    assert item["parlay_eligible"] is False
    assert item["longshot_warning"]

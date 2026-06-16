from src.optimizer.portfolio_optimizer import optimize_portfolio


def _candidate(match_id, home, away, outcome, odds, model_prob, market_prob, ev, edge, confidence=0.62):
    return {
        "candidate_type": "single",
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "play_type": "had",
        "outcome_key": outcome,
        "outcome_label": outcome,
        "odds": odds,
        "model_prob": model_prob,
        "market_prob": market_prob,
        "ev": ev,
        "edge": edge,
        "risk_level": "medium",
        "observation_confidence": confidence,
    }


def test_aggressive_profile_exposes_hit_rate_discipline_limits():
    result = optimize_portfolio(
        [
            _candidate("m1", "A", "B", "主胜", 2.2, 0.58, 0.48, 0.27, 0.10),
            _candidate("m2", "C", "D", "客胜", 2.1, 0.55, 0.47, 0.15, 0.08),
        ],
        bankroll=10000,
        config={"risk_profile": "aggressive"},
    )
    limits = result["risk_summary"]["profile_limits"]
    assert limits["min_parlay_2x1_prob"] == 0.20
    assert limits["min_parlay_3x1_prob"] == 0.12
    assert limits["min_leg_confidence"] == 0.50
    assert "串联命中率纪律" in " ".join(result["explanations"])


def test_low_combo_probability_is_rejected_with_reason():
    result = optimize_portfolio(
        [
            _candidate("m1", "A", "B", "主胜", 3.2, 0.32, 0.25, 0.05, 0.07),
            _candidate("m2", "C", "D", "客胜", 2.9, 0.36, 0.29, 0.04, 0.07),
        ],
        bankroll=10000,
        config={"risk_profile": "aggressive"},
    )
    reasons = " ".join(row.get("reject_reason", "") for row in result["candidate_rankings"]["parlay_2x1"])
    assert "组合命中概率低于纪律门槛" in reasons


def test_longshot_single_is_not_parlay_core():
    result = optimize_portfolio(
        [
            _candidate("m1", "A", "B", "客胜", 8.0, 0.18, 0.10, 0.44, 0.08),
            _candidate("m2", "C", "D", "主胜", 2.0, 0.58, 0.50, 0.16, 0.08),
        ],
        bankroll=10000,
        config={"risk_profile": "aggressive"},
    )
    top_single = result["candidate_rankings"]["singles"][0]
    assert top_single["longshot_warning"]
    assert top_single["parlay_eligible"] is False
    reasons = " ".join(row.get("reject_reason", "") for row in result["candidate_rankings"]["parlay_2x1"])
    assert "高赔率冷门腿不适合作为串联核心" in reasons


from src.optimizer.scoring import score_candidate


def test_longshot_not_parlay_eligible_by_default():
    item = score_candidate({"candidate_type": "single", "odds": 8.0, "model_prob": 0.15, "market_prob": 0.10, "ev": 0.2, "edge": 0.05, "risk_level": "medium"}, 10000, {"single_stake_cap_pct": 0.01, "parlay_2x1_cap_pct": 0.005, "parlay_3x1_cap_pct": 0.0, "kelly_multiplier": 0.25})
    assert item["risk_level"] == "very_high"
    assert item["parlay_eligible"] is False
    assert item["longshot_warning"]


def test_market_calibrated_probability_shrinks_overconfident_model():
    item = score_candidate(
        {
            "candidate_type": "single",
            "odds": 2.4,
            "model_prob": 0.70,
            "market_prob": 0.42,
            "ev": 0.68,
            "edge": 0.28,
            "risk_level": "medium",
            "observation_confidence": 0.46,
        },
        10000,
        {
            "single_stake_cap_pct": 0.01,
            "parlay_2x1_cap_pct": 0.005,
            "parlay_3x1_cap_pct": 0.0,
            "kelly_multiplier": 0.25,
            "learning_settled_count": 8,
            "learning_probability_quality": {"sample_count": 8},
            "learning_clv_summary": {"settled_count": 0},
        },
    )

    assert item["raw_model_prob"] == 0.70
    assert item["model_prob"] < item["raw_model_prob"]
    assert item["model_prob"] > 0.42
    assert item["probability_shrinkage_weight"] > 0
    assert "向市场概率收缩" in item["probability_shrinkage_reason_zh"]


def test_market_benchmark_skill_controls_probability_shrinkage():
    base_candidate = {
        "candidate_type": "single",
        "odds": 2.4,
        "model_prob": 0.70,
        "market_prob": 0.42,
        "ev": 0.68,
        "edge": 0.28,
        "risk_level": "medium",
        "observation_confidence": 0.62,
    }
    base_cfg = {
        "single_stake_cap_pct": 0.01,
        "parlay_2x1_cap_pct": 0.005,
        "parlay_3x1_cap_pct": 0.0,
        "kelly_multiplier": 0.25,
        "learning_settled_count": 60,
        "learning_probability_quality": {"sample_count": 60, "brier_score": 0.23, "log_loss": 0.68},
        "learning_clv_summary": {"settled_count": 0},
    }

    weak = score_candidate(
        base_candidate,
        10000,
        {**base_cfg, "learning_market_benchmark": {"sample_count": 60, "brier_skill_score": -0.04}},
    )
    strong = score_candidate(
        base_candidate,
        10000,
        {**base_cfg, "learning_market_benchmark": {"sample_count": 60, "brier_skill_score": 0.05}},
    )

    assert weak["probability_shrinkage_weight"] > strong["probability_shrinkage_weight"]
    assert "暂未优于市场概率" in weak["probability_shrinkage_reason_zh"]
    assert "正 Brier Skill" in strong["probability_shrinkage_reason_zh"]
    assert weak["probability_shrinkage"]["market_benchmark_discipline"]["status"] == "behind_market"
    assert strong["probability_shrinkage"]["market_benchmark_discipline"]["status"] == "beating_market"


def test_probability_uncertainty_flags_fragile_value():
    item = score_candidate(
        {
            "candidate_type": "single",
            "odds": 2.05,
            "model_prob": 0.56,
            "market_prob": 0.49,
            "ev": 0.148,
            "edge": 0.07,
            "risk_level": "medium",
            "observation_confidence": 0.40,
        },
        10000,
        {
            "single_stake_cap_pct": 0.01,
            "parlay_2x1_cap_pct": 0.005,
            "parlay_3x1_cap_pct": 0.0,
            "kelly_multiplier": 0.25,
            "learning_settled_count": 4,
            "learning_probability_quality": {"sample_count": 4},
            "learning_clv_summary": {"settled_count": 0},
        },
    )

    assert item["probability_lower"] < item["model_prob"]
    assert item["robust_value_status"] in {"fragile", "thin"}
    assert item["robustness_penalty"] > 0
    assert "概率区间" in item["robust_value_reason_zh"]

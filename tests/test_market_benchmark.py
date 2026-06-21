from src.learning.market_benchmark import build_market_benchmark_from_learning


def test_market_benchmark_reports_model_skill_against_market_probability():
    result = build_market_benchmark_from_learning(
        {
            "rows": [
                {"model_prob": 0.70, "market_prob": 0.55, "hit": True},
                {"model_prob": 0.65, "market_prob": 0.52, "hit": True},
                {"model_prob": 0.28, "market_prob": 0.44, "hit": False},
                {"model_prob": 0.35, "market_prob": 0.48, "hit": False},
            ]
        }
    )

    assert result["sample_count"] == 4
    assert result["status"] == "beating_market"
    assert result["brier_skill_score"] > 0
    assert "模型相对市场" in result["summary_zh"]

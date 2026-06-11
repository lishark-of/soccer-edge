from src.optimizer.best_parlay import build_best_parlay_summary


def test_best_parlay_quality_final_status_exists():
    result = build_best_parlay_summary({"candidate_rankings": {"parlay_2x1": [{"type": "parlay_2x1", "legs": "A;B", "odds": 4.0, "model_prob": 0.35, "market_prob": 0.22, "ev": 0.3, "edge": 0.13, "confidence_score": 0.7, "risk_level": "low", "selected": True}]}})
    assert result["best_2x1"]["best_parlay_quality"]["final_status"] in {"selected", "rejected"}

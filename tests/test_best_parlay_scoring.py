from src.optimizer.best_parlay import build_best_parlay_summary


def test_best_2x1_has_reason():
    optimizer = {"candidate_rankings": {"parlay_2x1": [{"type": "parlay_2x1", "legs": "A;B", "odds": 4.0, "model_prob": 0.28, "market_prob": 0.22, "ev": 0.12, "edge": 0.06, "selected": True, "risk_level": "medium"}]}}
    result = build_best_parlay_summary(optimizer)
    assert result["best_2x1"]["selected_reason_zh"]


def test_best_3x1_rejected_has_reason():
    optimizer = {"candidate_rankings": {"parlay_3x1": [{"type": "parlay_3x1", "legs": "A;B;C", "odds": 12.0, "model_prob": 0.08, "market_prob": 0.06, "ev": 0.01, "edge": 0.01, "selected": False, "risk_level": "high", "reject_reason": "EV 不足"}]}}
    result = build_best_parlay_summary(optimizer)
    assert result["best_3x1_if_allowed"]["reject_reason"] == "EV 不足"


def test_combo_score_sorting_stable():
    optimizer = {"candidate_rankings": {"parlay_2x1": [
        {"type": "parlay_2x1", "legs": "low", "odds": 3.0, "model_prob": 0.2, "market_prob": 0.2, "ev": 0.01, "edge": 0.01, "selected": False},
        {"type": "parlay_2x1", "legs": "high", "odds": 4.0, "model_prob": 0.3, "market_prob": 0.22, "ev": 0.12, "edge": 0.08, "selected": True},
    ]}}
    result = build_best_parlay_summary(optimizer)
    assert "high" in result["best_2x1"]["legs"]

from src.optimizer.best_parlay import build_best_parlay_summary


def test_gate_closed_returns_no_combo_state():
    result = build_best_parlay_summary({"credibility_gate": {"combo_gate": "closed", "reason_zh": "可信度不足"}, "candidate_rankings": {"parlay_2x1": [{"type": "parlay_2x1", "legs": "A;B", "odds": 4.0, "model_prob": 0.3, "market_prob": 0.2, "ev": 0.2, "edge": 0.1}]}})
    assert result["status"] == "no_combo"
    assert result["best_2x1"]["status"] == "no_combo"

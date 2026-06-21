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


def test_best_parlay_outputs_daily_candidate_lanes():
    optimizer = {
        "credibility_gate": {"combo_gate": "closed", "label_zh": "不建议串联", "reason_zh": "可信度不足"},
        "candidate_rankings": {
            "singles": [
                {"type": "single", "match": "A vs B 主胜", "odds": 2.1, "model_prob": 0.58, "market_prob": 0.48, "ev": 0.20, "edge": 0.10, "risk_level": "medium"}
            ],
            "parlay_2x1": [
                {"type": "parlay_2x1", "legs": "A+B", "odds": 4.0, "model_prob": 0.24, "market_prob": 0.20, "ev": 0.08, "edge": 0.04, "risk_level": "medium", "reject_reason": "可信度不足"}
            ],
            "parlay_3x1": [
                {"type": "parlay_3x1", "legs": "A+B+C", "odds": 9.5, "model_prob": 0.10, "market_prob": 0.08, "ev": -0.05, "edge": 0.02, "risk_level": "high", "reject_reason": "3串1风险过高"}
            ],
        },
    }
    result = build_best_parlay_summary(optimizer)
    lanes = result["daily_output_lanes"]
    assert [row["key"] for row in lanes] == ["daily_single_candidate", "daily_2x1_candidate", "daily_3x1_candidate"]
    assert lanes[0]["status"] in {"selected", "paper_candidate"}
    assert lanes[1]["status"] == "paper_candidate"
    assert lanes[2]["status"] == "paper_candidate"
    assert "纸面" in lanes[1]["action_zh"]
    assert result["status"] == "paper_candidates"

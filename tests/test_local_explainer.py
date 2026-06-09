from src.explain.local_explainer import explain_backtest_metrics, explain_candidate
from src.explain.safety import BANNED_EXPLANATION_TERMS


def test_local_explainer_candidate_avoids_banned_terms():
    text = explain_candidate({"model_prob": 0.56, "fair_prob": 0.49, "edge": 0.07, "ev": 0.04, "risk_level": "medium"})
    for term in BANNED_EXPLANATION_TERMS:
        assert term not in text


def test_local_explainer_backtest_mentions_no_future_guarantee():
    notes = explain_backtest_metrics({"roi": 0.02, "hit_rate": 0.5})
    assert any("不代表未来表现" in item or "不能保证未来" in item for item in notes)

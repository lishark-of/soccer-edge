from src.audit.trader_review import build_trader_review


def test_trader_review_has_final_call():
    preview = {"provider_used": "sporttery", "intelligence_completeness": {"score": 60}, "optimizer": {"selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []}, "candidate_rankings": {}}}
    result = build_trader_review(preview)
    assert result["final_call_zh"]
    assert result["conclusions_zh"]

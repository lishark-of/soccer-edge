from src.audit.credibility import audit_credibility


def test_credibility_score_exists():
    result = audit_credibility({"provider_used": "sporttery", "intelligence_completeness": {"score": 70, "main_gaps_zh": [], "partial_gaps_zh": []}, "optimizer": {"selected_portfolio": {"singles": []}}})
    assert 0 <= result["credibility_score"] <= 100
    assert result["grade"] in {"A", "B", "C", "D"}


def test_mock_fixture_not_high_credibility():
    result = audit_credibility({"provider_used": "mock", "intelligence_completeness": {"score": 95}, "optimizer": {"selected_portfolio": {"singles": []}}})
    assert result["confidence_level"] != "high"


def test_missing_intelligence_deducts_score():
    strong = audit_credibility({"provider_used": "sporttery", "intelligence_completeness": {"score": 80, "main_gaps_zh": [], "partial_gaps_zh": []}, "optimizer": {"selected_portfolio": {"singles": []}}})
    weak = audit_credibility({"provider_used": "sporttery", "intelligence_completeness": {"score": 80, "main_gaps_zh": ["伤停", "首发", "天气"], "partial_gaps_zh": []}, "optimizer": {"selected_portfolio": {"singles": []}}})
    assert weak["credibility_score"] < strong["credibility_score"]


def test_high_ev_is_not_high_confidence_by_itself():
    payload = {"provider_used": "sporttery", "intelligence_completeness": {"score": 35, "main_gaps_zh": ["伤停", "首发", "天气", "新闻"], "partial_gaps_zh": []}}
    optimizer = {"selected_portfolio": {"singles": [{"ev": 0.2, "edge": 0.03, "risk_level": "high"}]}}
    result = audit_credibility(payload, optimizer)
    assert result["confidence_level"] in {"medium", "low"}

from src.audit.credibility import audit_credibility


def test_mock_fixture_credibility_not_above_c():
    result = audit_credibility({"provider_used": "mock", "source_coverage": {"match_coverage": []}}, {"selected_portfolio": {}})
    assert result["grade"] in {"C", "D"}
    assert result["credibility_score"] <= 64


def test_fallback_estimated_coverage_penalizes_score():
    preview = {
        "provider_used": "sporttery",
        "source_coverage": {
            "match_coverage": [
                {
                    "injuries": {"status": "not_connected"},
                    "lineup": {"status": "not_connected"},
                    "weather": {"status": "fallback_estimated"},
                    "news": {"status": "checked_empty"},
                }
            ]
        },
    }
    result = audit_credibility(preview, {"selected_portfolio": {}})
    assert result["credibility_score"] < 80
    assert any("兜底估算" in reason for reason in result["reasons"])

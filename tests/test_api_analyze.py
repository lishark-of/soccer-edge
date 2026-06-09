from src.api.routes import dispatch_route


def test_api_analyze_mock_json_shape():
    response = dispatch_route("/api/analyze", {"provider": "mock", "date": "2026-06-09"})
    assert response["ok"] is True
    assert response["data"]["provider_used"] == "mock"
    assert "single_candidates" in response["data"]

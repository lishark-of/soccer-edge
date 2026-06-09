from src.api.routes import dispatch_route


def test_api_health_response_shape():
    response = dispatch_route("/api/health", {})
    assert response["ok"] is True
    assert response["data"]["status"] == "ok"
    assert response["data"]["mode"] == "read_only"


def test_api_info_disables_betting_capabilities():
    response = dispatch_route("/api/info", {})
    disabled = response["data"]["disabled_capabilities"]
    assert "betting" in disabled
    assert "payment" in disabled
    assert "order_placement" in disabled

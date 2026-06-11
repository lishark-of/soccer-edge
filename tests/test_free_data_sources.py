from src.api.routes import dispatch_route
from src.providers.free_data_sources import build_free_data_source_status


def test_free_data_sources_default_to_safe_optional_status():
    payload = build_free_data_source_status()
    sources = {item["key"]: item for item in payload["sources"]}
    assert sources["sporttery"]["status"] == "enabled"
    assert sources["the_odds_api"]["status"] in {"configured", "not_configured"}
    assert sources["api_football"]["status"] in {"configured", "not_configured"}
    assert sources["the_odds_api"]["signup_url"].startswith("https://")
    assert sources["api_football"]["env_var"] == "JC_EDGE_API_FOOTBALL_KEY"
    assert "secret_config" in payload
    assert "账号" in payload["credential_policy_zh"]
    assert "The Odds API" in payload["next_registration_zh"]


def test_data_sources_api_view_shape():
    response = dispatch_route("/api/view/data-sources", {})
    assert response["ok"] is True
    data = response["data"]
    assert data["data_source_layer_version"] == "phase2p_free_source_status_v0"
    assert any(item["key"] == "open_meteo" for item in data["sources"])

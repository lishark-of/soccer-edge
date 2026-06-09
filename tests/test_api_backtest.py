from src.api.routes import dispatch_route


def test_api_backtest_fixture_json_shape():
    response = dispatch_route(
        "/api/backtest",
        {"historical_data": "data/fixtures/historical_matches_backtest_sample.csv"},
    )
    assert response["ok"] is True
    assert response["data"]["model_version"] == "phase2c_backtest_market_poisson_elo_v0"
    assert "metrics" in response["data"]

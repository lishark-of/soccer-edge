from src.api.routes import dispatch_route


def test_api_view_analyze_response_shape():
    payload = dispatch_route("/api/view/analyze", {"provider": "mock", "date": "2026-06-09"})
    assert payload["ok"] is True
    assert payload["data"]["summary_cards"]
    assert "candidate_tables" in payload["data"]


def test_api_view_backtest_response_shape():
    payload = dispatch_route("/api/view/backtest", {"historical_data": "data/fixtures/historical_matches_backtest_sample.csv"})
    assert payload["ok"] is True
    assert payload["data"]["summary_cards"]
    assert "metric_explanations" in payload["data"]

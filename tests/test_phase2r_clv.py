from src.market.clv import build_clv_tracking, calculate_clv, observation_key
from src.api.routes import dispatch_route


def test_calculate_clv_pending_without_closing_odds():
    result = calculate_clv(2.2, None)
    assert result["status"] == "pending_closing_odds"
    assert result["clv_pct"] is None
    assert "等待收盘赔率" in result["message_zh"]


def test_calculate_positive_clv():
    result = calculate_clv(2.2, 2.0)
    assert result["status"] == "positive_clv"
    assert result["clv_pct"] == 0.1


def test_build_clv_tracking_uses_stable_observation_key():
    observation = {"match_id": "m1", "play_type": "had", "outcome_key": "win", "odds": 2.2, "home_team": "A", "away_team": "B"}
    key = observation_key(observation)
    report = build_clv_tracking([observation], {key: 2.0})
    assert report["tracked_count"] == 1
    assert report["settled_count"] == 1
    assert report["positive_clv_count"] == 1


def test_clv_review_api_uses_local_fixture_files():
    payload = dispatch_route(
        "/api/view/clv-review",
        {
            "observations_json": "data/fixtures/clv_observations_example.json",
            "closing_odds": "data/fixtures/closing_odds_example.csv",
        },
    )
    assert payload["ok"] is True
    assert payload["data"]["settled_count"] == 2
    assert payload["data"]["positive_clv_count"] == 1

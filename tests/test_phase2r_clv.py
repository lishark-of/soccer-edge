from src.market.clv import build_clv_history, build_clv_tracking, calculate_clv, observation_key
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


def test_clv_history_groups_by_play_type_and_signal_bucket(tmp_path):
    payload = build_clv_tracking(
        [
            {"match_id": "m1", "play_type": "hhad", "outcome_key": "win", "odds": 2.2, "home_team": "A", "away_team": "B"},
            {"match_id": "m2", "play_type": "hhad", "outcome_key": "win", "odds": 2.4, "home_team": "C", "away_team": "D"},
        ],
        {
            "m1|hhad|win": 2.5,
            "m2|hhad|win": 2.6,
        },
    )
    path = tmp_path / "clv.json"
    path.write_text(__import__("json").dumps(payload, ensure_ascii=False), encoding="utf-8")

    history = build_clv_history(tmp_path)

    assert history["play_type_rows"][0]["play_type"] == "hhad"
    assert history["play_type_rows"][0]["average_clv_pct"] < 0
    assert history["bucket_rows"][0]["signal_bucket"] == "2.00-3.00"

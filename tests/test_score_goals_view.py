from src.view_models.score_goals_view import build_score_goals_view


def test_score_goals_view_renders_totals_and_scores():
    preview = {
        "date": "2026-06-10",
        "provider_used": "sporttery",
        "matches_count": 2,
        "top_single_observations": [{"match_no": "周三201", "home_team": "葡萄牙", "away_team": "尼日利亚", "play_type": "hhad", "direction": "主胜", "official_odds": 3.25, "market_prob": 0.27, "model_prob": 0.41, "edge": 0.14, "ev": 0.35}],
        "top_total_goals_observations": [{"match_no": "周三201", "home_team": "葡萄牙", "away_team": "尼日利亚", "play_type": "total_goals", "direction": "总进球 2", "model_prob": 0.26}],
        "top_score_observations": [{"match_no": "周三201", "home_team": "葡萄牙", "away_team": "尼日利亚", "play_type": "correct_score", "direction": "比分 2-0", "model_prob": 0.21}],
        "contexts": [
            {
                "match": {"match_no": "周三201", "home_team": "葡萄牙", "away_team": "尼日利亚"},
                "total_goals": {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.2, "4": 0.1, "5": 0.05, "6": 0.03, "7+": 0.02},
                "fused_probability": {"had": {"home": 0.5, "draw": 0.25, "away": 0.25}, "hhad": {"home": 0.3, "draw": 0.3, "away": 0.4}},
                "top_scores": [{"score": "2-0", "probability": 0.21}, {"score": "1-0", "probability": 0.15}],
            }
        ],
        "missing_signals": ["news"],
    }
    view = build_score_goals_view(preview)
    assert view["summary_cards"]
    assert view["total_goals_table"][0]["direction"] == "总进球 2"
    assert view["score_table"][0]["direction"] == "比分 2-0"
    assert view["handicap_table"][0]["play_type"] == "让球胜平负"
    assert view["handicap_table"][0]["direction"] == "主胜"
    assert view["probability_integrity"][0]["status"] == "pass"
    assert view["probability_integrity"][0]["total_goals_sum"] == "1.0000"

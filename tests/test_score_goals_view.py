from src.view_models.score_goals_view import build_score_goals_view


def test_score_goals_view_renders_totals_and_scores():
    preview = {
        "date": "2026-06-10",
        "provider_used": "sporttery",
        "matches_count": 2,
        "top_total_goals_observations": [{"match_no": "周三201", "home_team": "葡萄牙", "away_team": "尼日利亚", "play_type": "total_goals", "direction": "总进球 2", "model_prob": 0.26}],
        "top_score_observations": [{"match_no": "周三201", "home_team": "葡萄牙", "away_team": "尼日利亚", "play_type": "correct_score", "direction": "比分 2-0", "model_prob": 0.21}],
        "missing_signals": ["news"],
    }
    view = build_score_goals_view(preview)
    assert view["summary_cards"]
    assert view["total_goals_table"][0]["direction"] == "总进球 2"
    assert view["score_table"][0]["direction"] == "比分 2-0"

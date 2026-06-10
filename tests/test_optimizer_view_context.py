from src.view_models.optimizer_view import build_optimizer_view


def test_optimizer_view_exposes_data_source_context():
    view = build_optimizer_view(
        {
            "date": "2026-06-10",
            "provider_used": "sporttery",
            "matches_analyzed": 2,
            "candidate_pool_count": 9,
            "risk_profile": "aggressive",
            "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
        }
    )
    assert view["date"] == "2026-06-10"
    assert view["provider_used"] == "sporttery"
    assert view["matches_analyzed"] == 2
    labels = [card["label"] for card in view["summary_cards"]]
    assert "实际数据源" in labels
    assert "分析比赛数" in labels

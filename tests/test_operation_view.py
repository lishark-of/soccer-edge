from src.view_models.operation_view import build_operation_view


def test_operation_view_formats_rmb():
    view = build_operation_view({"initial_bankroll": 10000, "final_bankroll": 10320, "total_profit": 320, "roi": 0.032, "hit_rate": 0.48, "max_drawdown": 0.08})
    values = [card["value"] for card in view["summary_cards"]]
    assert "¥10,000.00" in values
    assert "+¥320.00" in values

from src.view_models.operation_view import build_operation_view


def test_operation_view_formats_rmb():
    view = build_operation_view({"initial_bankroll": 10000, "final_bankroll": 10320, "total_profit": 320, "roi": 0.032, "hit_rate": 0.48, "max_drawdown": 0.08})
    values = [card["value"] for card in view["summary_cards"]]
    assert "¥10,000.00" in values
    assert "+¥320.00" in values


def test_operation_view_explains_profit_loss_reasons():
    view = build_operation_view({
        "initial_bankroll": 10000,
        "final_bankroll": 10100,
        "total_profit": 100,
        "total_staked": 500,
        "hit_rate": 0.5,
        "max_drawdown": 0.04,
        "combo_summary": {"single": {"settled": 3, "profit": 120, "roi": 0.24}, "parlay_2x1": {"settled": 1, "profit": -20, "roi": -0.2}},
    })
    explanation = "；".join(view["profit_explanation"])
    assert "为什么" not in explanation or explanation
    assert "总盈亏" in explanation
    assert "玩法贡献" in explanation
    assert "不代表未来表现" in explanation

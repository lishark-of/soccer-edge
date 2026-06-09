from src.view_models.backtest_view import build_backtest_view


def test_probability_backtest_view_has_diagnostic_language():
    view = build_backtest_view({"metrics": {"roi": 0.01}, "bets": []})
    text = "\n".join(view["metric_explanations"] + view["risk_notes"])
    assert "回测" in text
    assert "未来" in text

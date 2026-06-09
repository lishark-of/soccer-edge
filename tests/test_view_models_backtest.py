from src.view_models.backtest_view import build_backtest_view


def test_backtest_view_has_metric_explanations():
    view = build_backtest_view(
        {
            "matches_total": 10,
            "matches_evaluated": 8,
            "bets_total": 2,
            "metrics": {"hit_rate": 0.5, "roi": 0.03, "max_drawdown": -0.1, "brier_score": 0.22, "log_loss": 1.01},
            "calibration": {"by_class": {"win": [{"bin_start": 0.4, "bin_end": 0.5, "count": 3, "avg_predicted_prob": 0.45, "observed_frequency": 0.33, "gap": -0.12}]}},
            "bets": [],
        }
    )
    assert view["summary_cards"]
    assert view["metric_explanations"]
    assert view["calibration_table"]


def test_probability_backtest_view_contains_required_cards():
    view = build_backtest_view({"metrics": {}, "bets": []})
    labels = {item["label"] for item in view["summary_cards"]}
    assert "Brier Score" in labels
    assert "Log Loss" in labels
    assert "最大回撤" in labels

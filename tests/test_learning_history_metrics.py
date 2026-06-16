from src.learning.history import build_learning_history


def test_learning_history_exposes_daily_and_window_metrics():
    payload = build_learning_history(include_fixtures=True)
    assert isinstance(payload.get("daily_metrics"), list)
    assert isinstance(payload.get("window_metrics"), list)
    assert "latest_daily_summary_zh" in payload
    assert isinstance(payload.get("window_summaries_zh"), list)
    assert isinstance(payload.get("daily_digest"), dict)
    assert isinstance(payload.get("window_digests"), list)
    assert isinstance(payload.get("daily_report"), dict)
    assert isinstance(payload.get("window_reports"), list)
    assert any(row.get("window") == "all_time" for row in payload["window_metrics"])
    if payload["daily_metrics"]:
        row = payload["daily_metrics"][0]
        assert "brier_score" in row
        assert "log_loss" in row
        assert "paper_roi" in row
        assert "average_clv_pct" in row
        assert payload["daily_digest"]["summary_zh"]
        assert payload["daily_digest"]["next_step_zh"]
        assert payload["daily_report"]["headline_zh"]
        assert payload["daily_report"]["paragraphs_zh"]
        assert payload["daily_report"]["metrics_line_zh"]
    if payload["window_digests"]:
        assert payload["window_digests"][0]["summary_zh"]
        assert payload["window_digests"][0]["next_step_zh"]
    if payload["window_reports"]:
        assert payload["window_reports"][0]["headline_zh"]
        assert payload["window_reports"][0]["paragraphs_zh"]

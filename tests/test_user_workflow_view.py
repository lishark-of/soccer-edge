from src.view_models.user_workflow_view import build_user_workflow_view


def test_user_workflow_view_has_six_steps():
    view = build_user_workflow_view({"field_report": {"recognized_fields": [], "missing_required_fields": []}, "backtest": {}, "analysis": {}})
    assert len(view["steps"]) == 6
    assert view["steps"][0]["title"] == "识别 CSV 字段"

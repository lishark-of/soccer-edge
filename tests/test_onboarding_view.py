from src.view_models.onboarding_view import build_onboarding_view


def test_onboarding_view_has_six_steps():
    view = build_onboarding_view()
    assert len(view["steps"]) == 6
    assert view["summary_cards"][0]["value"] == "JC Edge"
    assert any("竞彩足球" in step["title"] for step in view["steps"])

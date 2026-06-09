from src.application import build_matches_payload
from src.view_models.matches_view import build_matches_view


def test_matches_view_has_provider_warnings_as_data_source_notes():
    payload = build_matches_payload(target_date="2026-06-09", provider_name="mock")
    view = build_matches_view(payload)
    assert view["summary_cards"]
    assert "matches_table" in view
    assert "data_source_notes" in view
    assert any(card["label"] == "实际数据源" for card in view["summary_cards"])

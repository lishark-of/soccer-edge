from src.intelligence.missing_info import build_missing_info_from_preview


def test_missing_information_reports_unknown_fields():
    preview = {"contexts": [{"signals": {}}]}
    result = build_missing_info_from_preview(preview)
    assert "伤停" in result["missing_information"]
    assert "首发" in result["missing_information"]

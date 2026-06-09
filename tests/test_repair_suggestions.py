from src.ingestion.repair_suggestions import build_repair_suggestions


def test_repair_suggestions_include_mapping_example():
    suggestions = build_repair_suggestions({"missing_required_fields": ["home_team"], "missing_odds_fields": ["odds_home"]})
    assert suggestions[0]["message_zh"].startswith("未识别主队字段")
    assert suggestions[0]["mapping_example"] == {"home_team": "主队"}
    assert any(item["severity"] == "warning" for item in suggestions)

from src.intelligence.missing_info import build_missing_info_status


def test_missing_info_marks_user_can_supply():
    result = build_missing_info_status({"signals": {}})
    assert "伤停" in result["missing_information"]
    assert any(row["user_can_supply"] for row in result["fields"] if row["key"] == "injuries")


def test_missing_info_does_not_fabricate_connected():
    result = build_missing_info_status({"signals": {"weather": {"status": "not_connected"}}})
    weather = [row for row in result["fields"] if row["key"] == "weather"][0]
    assert weather["status"] == "not_connected"
    assert weather["impact"] == "unknown"

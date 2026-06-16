from src.intelligence.coverage_status import confidence_for_status, normalize_coverage_status, status_zh
from src.view_models.intelligence_view import build_intelligence_coverage_table


def test_checked_empty_is_not_confirmed():
    assert normalize_coverage_status("covered_empty") == "checked_empty"
    assert status_zh("checked_empty") == "已检查但未返回"
    assert normalize_coverage_status("checked_empty") != "confirmed"


def test_intelligence_coverage_table_uses_layered_status():
    preview = {
        "source_coverage": {
            "match_coverage": [
                {
                    "match": "周三201 葡萄牙 vs 尼日利亚",
                    "injuries": {"status": "checked_empty", "message_zh": "已检查，接口暂未返回伤停信息。"},
                    "lineup": {"status": "not_connected"},
                    "weather": {"status": "fallback_estimated", "city_source": "team_country_fallback"},
                    "news": {"status": "confirmed", "message_zh": "已检索到新闻。"},
                }
            ]
        }
    }
    table = build_intelligence_coverage_table(preview)
    rows = {(row["key"], row["status"]): row for row in table["rows"]}
    assert "已检查但未返回" in table["summary_zh"]
    assert "兜底估算" in table["summary_zh"]
    assert ("injuries", "checked_empty") in rows
    assert ("weather", "fallback_estimated") in rows
    assert rows[("weather", "fallback_estimated")]["confidence"] == "低"
    assert "不等于确认没有该信息" in rows[("injuries", "checked_empty")]["explanation_zh"]
    assert "兜底估算" in rows[("weather", "fallback_estimated")]["explanation_zh"]


def test_status_confidence_levels():
    assert confidence_for_status("confirmed") == "high"
    assert confidence_for_status("user_supplied") == "medium"
    assert confidence_for_status("fallback_estimated", fallback_source="team_country_fallback") == "low"

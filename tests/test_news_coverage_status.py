from src.intelligence.coverage_status import normalize_coverage_status
from src.providers.gdelt_news_provider import _query


def test_gdelt_alias_query_uses_english_team_names():
    query = _query("葡萄牙", "尼日利亚")
    assert "Portugal" in query
    assert "Nigeria" in query


def test_news_no_result_maps_to_checked_empty():
    assert normalize_coverage_status("not_found") == "checked_empty"

from src.ingestion.adapters.generic_csv_adapter import GenericCsvAdapter
from src.ingestion.adapters.sporttery_export_adapter import SportteryExportAdapter
from src.ingestion.field_mapping import infer_field_mapping


def test_generic_csv_adapter_preview():
    preview = GenericCsvAdapter().preview("data/fixtures/import_sample_generic.csv")
    assert preview["row_count"] >= 10
    assert "date" in preview["columns"]


def test_sporttery_export_adapter_handles_chinese_headers():
    adapter = SportteryExportAdapter()
    assert adapter.can_handle("data/fixtures/import_sample_sporttery.csv")
    preview = adapter.preview("data/fixtures/import_sample_sporttery.csv")
    assert "比赛日期" in preview["columns"]


def test_field_mapping_infers_common_aliases():
    mapping = infer_field_mapping(["比赛日期", "赛事", "主队", "客队", "比分", "胜赔", "平赔", "负赔"])
    assert mapping["date"] == "比赛日期"
    assert mapping["odds_home"] == "胜赔"

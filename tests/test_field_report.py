from src.ingestion.field_mapping import infer_field_mapping
from src.ingestion.field_report import build_field_recognition_report


def test_field_report_recognizes_chinese_headers():
    columns = ["比赛日期", "赛事", "主队", "客队", "比分", "胜赔", "平赔", "负赔"]
    mapping = infer_field_mapping(columns)
    report = build_field_recognition_report(columns, mapping)
    assert report["confidence"] == "high"
    assert not report["missing_required_fields"]
    assert report["can_backtest_with_ev"] is True


def test_field_report_reports_missing_required_fields():
    report = build_field_recognition_report(["比赛日期", "赛事", "比分"], {"date": "比赛日期", "league": "赛事", "score": "比分"})
    assert "home_team" in report["missing_required_fields"]
    assert report["confidence"] == "low"

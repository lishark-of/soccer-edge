from src.exports.report_exporter import export_report_to_markdown


def test_markdown_report_exporter_writes_file(tmp_path):
    path = tmp_path / "report.md"
    export_report_to_markdown({"model_version": "m", "warnings": []}, str(path))
    assert path.exists()
    assert "football-jc-analysis Report" in path.read_text(encoding="utf-8")

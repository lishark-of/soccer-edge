from pathlib import Path

from src.api.schemas import error_envelope, success_response
from src.qa.api_sanity import check_api_envelope, check_api_error_envelope
from src.qa.dashboard_sanity import check_dashboard_static_files
from src.qa.report_sanity import check_report_structure


def test_dashboard_sanity_rejects_external_cdn(tmp_path):
    (tmp_path / "index.html").write_text("Read-only local analysis mode https://cdn.example/x.js", encoding="utf-8")
    (tmp_path / "app.js").write_text("const api='http://127.0.0.1:8765';", encoding="utf-8")
    (tmp_path / "style.css").write_text("body{}", encoding="utf-8")
    results = check_dashboard_static_files(str(tmp_path))
    assert any(result.name == "dashboard.external_network" and not result.passed for result in results)


def test_report_sanity_requires_disclaimer():
    results = check_report_structure({"warnings": []}, "backtest")
    assert any(result.name == "report.backtest.disclaimer" and not result.passed for result in results)


def test_api_envelope_sanity():
    assert all(result.passed for result in check_api_envelope(success_response({"x": 1}), "test"))
    assert all(result.passed for result in check_api_error_envelope(error_envelope("bad_request", "bad"), "test"))

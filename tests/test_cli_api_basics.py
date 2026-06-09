from pathlib import Path

from src.api.app import phase_two_notice
from src.application import build_analysis_payload, build_matches_payload
from src.providers.factory import AutoFallbackProvider
from src.exports.xlsx_exporter import export_analysis_xlsx
from src.providers.mock_provider import MockProvider
from src.strategy.portfolio_builder import build_daily_analysis


def test_get_matches_mock_provider():
    provider = MockProvider()
    matches = provider.get_matches("2026-06-09")

    assert matches
    assert matches[0].date == "2026-06-09"


def test_analysis_returns_candidates_or_empty_list():
    provider = MockProvider()
    report = build_daily_analysis(provider, "2026-06-09")

    assert report.matches_analyzed > 0
    assert isinstance(report.single_candidates, list)
    assert isinstance(report.parlay_2x1_candidates, list)


def test_export_xlsx_created(tmp_path: Path):
    provider = MockProvider()
    report = build_daily_analysis(provider, "2026-06-09")
    path = export_analysis_xlsx(report, output_dir=str(tmp_path))

    assert path.exists()
    assert path.suffix == ".xlsx"


def test_analysis_payload_supports_provider_metadata():
    payload = build_analysis_payload(target_date="2026-06-09", provider_name="mock")

    assert payload["provider_requested"] == "mock"
    assert payload["provider_used"] == "mock"
    assert "disclaimers" in payload


def test_matches_payload_contains_match_rows():
    payload = build_matches_payload(target_date="2026-06-09", provider_name="mock")

    assert payload["matches"]
    assert payload["matches"][0]["date"] == "2026-06-09"


def test_phase_two_notice_points_to_preview_server():
    notice = phase_two_notice()

    assert notice["status"] == "preview_ready"
    assert "src.api.app" in notice["message"]


def test_auto_fallback_provider_can_wrap_mock_only():
    provider = AutoFallbackProvider(primary=MockProvider(), fallback=MockProvider())
    matches = provider.get_matches("2026-06-09")

    assert matches

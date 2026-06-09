from src.providers.mock_provider import MockProvider
from src.strategy.portfolio_builder import build_daily_analysis


def test_mock_provider_returns_matches():
    provider = MockProvider()
    matches = provider.get_matches("2026-06-09")

    assert len(matches) >= 3


def test_mock_provider_match_schema_has_required_fields():
    provider = MockProvider()
    match = provider.get_matches("2026-06-09")[0].to_dict()

    required = {
        "match_id",
        "match_num",
        "date",
        "kickoff_time",
        "league",
        "home_team",
        "away_team",
        "status",
        "had_odds",
        "hhad_odds",
        "is_single_allowed",
        "source",
        "raw",
    }
    assert required.issubset(set(match.keys()))


def test_mock_provider_contains_none_for_missing_odds():
    provider = MockProvider()
    matches = {match.match_no: match for match in provider.get_matches("2026-06-09")}

    assert matches["002"].had_odds["draw"] is None


def test_missing_odds_are_excluded_not_crash():
    provider = MockProvider()
    report = build_daily_analysis(provider, "2026-06-09")

    reasons = [item["reason"] for item in report.excluded_matches]
    assert any("赔率缺失或无效" in reason for reason in reasons)

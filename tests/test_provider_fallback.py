from src.domain.match import Match
from src.domain.odds import MatchOdds, OddsHistory
from src.providers.base import BaseProvider
from src.providers.factory import AutoFallbackProvider
from src.providers.mock_provider import MockProvider


class FailingProvider(BaseProvider):
    provider_name = "failing"

    def get_matches(self, date: str | None):
        raise RuntimeError("boom")

    def get_match_odds(self, match_id: str) -> MatchOdds:
        raise RuntimeError("boom")

    def get_odds_history(self, match_id: str) -> OddsHistory:
        raise RuntimeError("boom")


def test_auto_provider_falls_back_to_mock_when_primary_fails():
    provider = AutoFallbackProvider(primary=FailingProvider(), fallback=MockProvider())

    matches = provider.get_matches("2026-06-09")

    assert matches
    assert provider.fallback_used is True
    assert provider.resolved_provider_name == "mock"
    assert provider.messages

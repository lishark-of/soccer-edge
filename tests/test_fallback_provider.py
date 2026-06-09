from src.domain.odds import MatchOdds, OddsHistory
from src.providers.base import BaseProvider, ProviderError
from src.providers.fallback_provider import FallbackProvider
from src.providers.mock_provider import MockProvider


class PrimarySuccessProvider(MockProvider):
    name = "sporttery"
    provider_name = "sporttery"


class FailingProvider(BaseProvider):
    name = "sporttery"
    provider_name = "sporttery"

    def get_matches(self, date: str | None = None):
        raise ProviderError("boom")

    def get_match_odds(self, match_id: str) -> MatchOdds:
        raise ProviderError("boom")

    def get_odds_history(self, match_id: str) -> OddsHistory:
        raise ProviderError("boom")


def test_fallback_provider_uses_primary_when_successful():
    provider = FallbackProvider(primary=PrimarySuccessProvider(), fallback=MockProvider())

    matches = provider.get_matches("2026-06-09")

    assert matches
    assert provider.provider_used == "sporttery"
    assert provider.fallback_used is False
    assert provider.warnings == []


def test_fallback_provider_uses_mock_when_primary_raises():
    provider = FallbackProvider(primary=FailingProvider(), fallback=MockProvider())

    matches = provider.get_matches("2026-06-09")

    assert matches
    assert provider.provider_used == "mock"
    assert provider.fallback_used is True
    assert provider.warnings
    assert "fallback to mock" in provider.warnings[0]

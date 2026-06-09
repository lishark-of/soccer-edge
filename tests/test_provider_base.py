from src.providers.base import ProviderError
from src.providers.mock_provider import MockProvider


def test_provider_error_round_trips_message():
    error = ProviderError("boom")

    assert str(error) == "boom"


def test_mock_provider_exposes_provider_contract_name():
    provider = MockProvider()

    assert provider.name == "mock"
    assert provider.provider_name == "mock"

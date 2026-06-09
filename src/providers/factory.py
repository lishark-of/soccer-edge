from __future__ import annotations

from src.providers.base import BaseProvider
from src.providers.fallback_provider import FallbackProvider
from src.providers.mock_provider import MockProvider
from src.providers.sporttery_provider import SportteryProvider

AutoFallbackProvider = FallbackProvider


def create_provider(provider_name: str) -> BaseProvider:
    key = provider_name.strip().lower()
    if key == "mock":
        return MockProvider()
    if key == "sporttery":
        return SportteryProvider()
    if key == "auto":
        return FallbackProvider()
    raise ValueError(f"Unsupported provider: {provider_name}")

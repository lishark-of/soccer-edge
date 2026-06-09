from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from src.domain.match import Match
from src.domain.odds import MatchOdds, OddsHistory


class ProviderError(Exception):
    """Raised when a data provider cannot return usable match data."""


@runtime_checkable
class MatchProvider(Protocol):
    name: str
    provider_name: str

    def get_matches(self, date: str | None = None) -> list[Match]:
        ...

    def get_match_odds(self, match_id: str) -> MatchOdds:
        ...

    def get_odds_history(self, match_id: str) -> OddsHistory:
        ...


class BaseProvider(ABC):
    name = "base"
    provider_name = "base"

    @abstractmethod
    def get_matches(self, date: str | None) -> list[Match]:
        raise NotImplementedError

    @abstractmethod
    def get_match_odds(self, match_id: str) -> MatchOdds:
        raise NotImplementedError

    @abstractmethod
    def get_odds_history(self, match_id: str) -> OddsHistory:
        raise NotImplementedError

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class MarketOdds:
    play_type: str
    outcomes: dict[str, float | None]
    handicap: float | None = None
    source: str = "mock"
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MatchOdds:
    match_id: str
    markets: dict[str, MarketOdds] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        had = self.markets.get("had")
        hhad = self.markets.get("hhad")
        return {
            "match_id": self.match_id,
            "markets": {key: value.to_dict() for key, value in self.markets.items()},
            "had_odds": had.to_dict() if had else None,
            "hhad_odds": hhad.to_dict() if hhad else None,
        }


@dataclass(slots=True)
class OddsHistoryPoint:
    snapshot_at: str
    outcomes: dict[str, float | None]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OddsHistory:
    match_id: str
    history: dict[str, list[OddsHistoryPoint]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "history": {
                key: [point.to_dict() for point in points]
                for key, points in self.history.items()
            },
        }

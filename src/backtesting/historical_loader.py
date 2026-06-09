from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HistoricalMatch:
    date: str
    league: str
    home_team: str
    away_team: str
    result_1x2: str


def load_historical_matches(_: str) -> list[HistoricalMatch]:
    return []

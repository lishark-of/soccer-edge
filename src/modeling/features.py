from __future__ import annotations

from src.backtesting.historical_loader import HistoricalMatch


def historical_matches_before_date(historical_matches: list[HistoricalMatch], before_date: str) -> list[HistoricalMatch]:
    return sorted(
        [match for match in historical_matches if match.date < before_date],
        key=lambda match: (match.date, match.home_team, match.away_team),
    )

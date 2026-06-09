from __future__ import annotations

from src.ingestion.adapters.generic_csv_adapter import GenericCsvAdapter


FOOTBALL_DATA_HEADERS = {
    "match_time",
    "game",
    "home",
    "away",
    "score",
    "half_score",
    "league",
    "date",
}


class FootballDataAdapter(GenericCsvAdapter):
    name = "football_data"

    def can_handle(self, path: str) -> bool:
        if not super().can_handle(path):
            return False
        columns = set(self._columns(path))
        return len(columns.intersection(FOOTBALL_DATA_HEADERS)) >= 4

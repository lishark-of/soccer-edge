from __future__ import annotations

from csv import DictReader
from pathlib import Path
from typing import Any


class GenericCsvAdapter:
    name = "generic_csv"

    def can_handle(self, path: str) -> bool:
        return Path(path).suffix.lower() == ".csv"

    def preview(self, path: str, limit: int = 5) -> dict:
        rows = self.load_rows(path)
        columns = list(rows[0].keys()) if rows else self._columns(path)
        return {
            "columns": columns,
            "sample_rows": rows[:limit],
            "row_count": len(rows),
            "warnings": [] if rows else ["file has no data rows"],
        }

    def load_rows(self, path: str) -> list[dict[str, Any]]:
        if not self.can_handle(path):
            raise ValueError("generic_csv adapter only supports .csv files")
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in DictReader(handle)]

    def _columns(self, path: str) -> list[str]:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = DictReader(handle)
            return list(reader.fieldnames or [])

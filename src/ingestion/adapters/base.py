from __future__ import annotations

from typing import Any, Protocol


class HistoricalDataAdapter(Protocol):
    name: str

    def can_handle(self, path: str) -> bool:
        ...

    def preview(self, path: str, limit: int = 5) -> dict:
        ...

    def load_rows(self, path: str) -> list[dict[str, Any]]:
        ...

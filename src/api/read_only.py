from __future__ import annotations

from src.api.errors import ApiError


def ensure_read_only_operation(operation: str, write_requested: bool = False) -> None:
    if write_requested:
        raise ApiError(
            "read_only_violation",
            f"{operation} is read-only in the local API and cannot write files",
            status=403,
        )

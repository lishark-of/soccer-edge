from __future__ import annotations

from src.api.schemas import error_envelope


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def error_response(error: Exception) -> tuple[int, dict]:
    if isinstance(error, ApiError):
        return error.status, error_envelope(error.code, error.message)
    return 500, error_envelope("internal_error", str(error)[:180] or error.__class__.__name__)

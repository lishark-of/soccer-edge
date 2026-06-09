from __future__ import annotations


DISCLAIMER = "For research and entertainment reference only. No outcome is guaranteed."


def success_response(data: dict | list | None = None, warnings: list[str] | None = None) -> dict:
    return {
        "ok": True,
        "data": data if data is not None else {},
        "warnings": list(warnings or []),
        "disclaimer": DISCLAIMER,
    }


def error_envelope(code: str, message: str, warnings: list[str] | None = None) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
        "warnings": list(warnings or []),
        "disclaimer": DISCLAIMER,
    }

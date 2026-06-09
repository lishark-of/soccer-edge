from __future__ import annotations

from src.version import get_version


def build_release_checklist() -> dict:
    return {
        "version": get_version(),
        "items": [
            "Git remote is none",
            "stock-MING untouched",
            "compileall passed",
            "analyze/backtest/import/QA/API/dashboard smoke passed",
            "generated files ignored",
            "no API keys committed",
            "no .env committed",
            "no artifacts/reports committed",
            "no banned UI controls",
            "dashboard local-only",
            "DeepSeek disabled by default",
            "local tag created",
            "no push performed",
        ],
        "disclaimer": "Release checklist is local QA only and does not guarantee model accuracy.",
    }

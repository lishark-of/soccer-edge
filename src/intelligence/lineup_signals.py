from __future__ import annotations

from src.intelligence.news_signals import signal_or_unknown


def lineup_signal(external: dict | None) -> dict:
    return signal_or_unknown(external, "lineup")


def injury_signal(external: dict | None) -> dict:
    return signal_or_unknown(external, "injuries")

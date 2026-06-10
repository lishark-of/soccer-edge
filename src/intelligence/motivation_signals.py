from __future__ import annotations

from src.intelligence.news_signals import signal_or_unknown


def motivation_signal(external: dict | None) -> dict:
    """Return match motivation context without fabricating unavailable information."""
    return signal_or_unknown(external, "motivation")

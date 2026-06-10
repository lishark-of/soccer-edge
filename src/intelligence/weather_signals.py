from __future__ import annotations

from src.intelligence.news_signals import signal_or_unknown


def weather_signal(external: dict | None) -> dict:
    return signal_or_unknown(external, "weather")

from __future__ import annotations

from src.application import build_analysis_payload


def get_analysis_payload(date: str | None, provider_name: str) -> dict[str, object]:
    return build_analysis_payload(target_date=date, provider_name=provider_name)

from __future__ import annotations

from src.application import build_analysis_payload


def get_export_payload(date: str | None, provider_name: str, export_format: str) -> dict[str, object]:
    return build_analysis_payload(target_date=date, provider_name=provider_name, export_format=export_format)

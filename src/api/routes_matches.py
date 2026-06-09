from __future__ import annotations

from src.application import build_match_odds_payload, build_matches_payload, build_odds_history_payload


def get_matches_payload(date: str | None, provider_name: str) -> dict[str, object]:
    return build_matches_payload(target_date=date, provider_name=provider_name)


def get_match_odds_payload(match_id: str, date: str | None, provider_name: str) -> dict[str, object]:
    return build_match_odds_payload(match_id=match_id, target_date=date, provider_name=provider_name)


def get_odds_history_payload(match_id: str, date: str | None, provider_name: str) -> dict[str, object]:
    return build_odds_history_payload(match_id=match_id, target_date=date, provider_name=provider_name)

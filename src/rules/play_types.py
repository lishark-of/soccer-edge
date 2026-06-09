from __future__ import annotations

from enum import StrEnum


class PlayType(StrEnum):
    HAD = "had"
    HHAD = "hhad"
    SCORE = "score"
    TOTAL_GOALS = "total_goals"
    HALF_FULL = "half_full"
    MIXED = "mixed"


OUTCOME_LABELS = {
    PlayType.HAD: {"home": "胜", "draw": "平", "away": "负"},
    PlayType.HHAD: {"home": "让胜", "draw": "让平", "away": "让负"},
}


def outcome_label(play_type: str, outcome_key: str) -> str:
    labels = OUTCOME_LABELS.get(PlayType(play_type), {})
    return labels.get(outcome_key, outcome_key)

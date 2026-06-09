from __future__ import annotations

from itertools import combinations

from src.domain.selection import Selection
from src.rules.pass_types import normalize_pass_type, pass_leg_count


def calculate_ticket_count(selections: list[Selection], pass_type: str) -> int:
    normalized = normalize_pass_type(pass_type)
    leg_count = pass_leg_count(normalized)
    if leg_count == 1:
        return len(selections)
    if len(selections) < leg_count:
        return 0
    valid = 0
    for combo in combinations(selections, leg_count):
        match_ids = {selection.match_id for selection in combo}
        if len(match_ids) == leg_count:
            valid += 1
    return valid

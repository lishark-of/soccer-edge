from __future__ import annotations

from itertools import combinations

from src.domain.parlay import ParlayCandidate, ParlayLeg
from src.domain.selection import Selection
from src.rules.pass_types import normalize_pass_type, pass_leg_count


def build_parlay_combinations(selections: list[Selection], pass_type: str) -> list[list[ParlayLeg]]:
    normalized = normalize_pass_type(pass_type)
    leg_count = pass_leg_count(normalized)
    if leg_count == 1:
        return [[_to_leg(selection)] for selection in selections]

    parlays: list[list[ParlayLeg]] = []
    for combo in combinations(selections, leg_count):
        if len({selection.match_id for selection in combo}) != leg_count:
            continue
        parlays.append([_to_leg(selection) for selection in combo])
    return parlays


def _to_leg(selection: Selection) -> ParlayLeg:
    return ParlayLeg(
        match_id=selection.match_id,
        match_no=selection.match_no,
        home_team=selection.home_team,
        away_team=selection.away_team,
        play_type=selection.play_type,
        outcome_label=selection.outcome_label,
        odds=selection.odds,
        model_prob=selection.model_prob,
        fair_prob=selection.fair_prob,
        ev=selection.ev,
        risk_level=selection.risk_level,
    )

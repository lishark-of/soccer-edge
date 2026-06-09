from __future__ import annotations

from math import prod

from src.domain.parlay import ParlayCandidate, ParlayLeg, PayoutEstimate
from src.rules.ticket_count import calculate_ticket_count


def estimate_payout(parlay: list[ParlayLeg] | ParlayCandidate, stake_per_ticket: float = 2) -> PayoutEstimate:
    if isinstance(parlay, ParlayCandidate):
        pass_type = parlay.pass_type
        legs = parlay.legs
    else:
        leg_count = len(parlay)
        pass_type = "single" if leg_count == 1 else f"{leg_count}x1"
        legs = parlay
    combined_odds = round(prod(max(1.0, leg.odds) for leg in legs), 4)
    ticket_count = max(1, calculate_ticket_count([_to_selection_stub(leg) for leg in legs], pass_type))
    total_stake = round(ticket_count * stake_per_ticket, 2)
    theoretical_max_payout = round(total_stake * combined_odds, 2)
    breakeven_probability = round(1.0 / combined_odds, 6) if combined_odds > 0 else 0.0
    return PayoutEstimate(
        pass_type=pass_type,
        ticket_count=ticket_count,
        stake_per_ticket=stake_per_ticket,
        total_stake=total_stake,
        combined_odds=combined_odds,
        theoretical_max_payout=theoretical_max_payout,
        breakeven_probability=breakeven_probability,
    )


def _to_selection_stub(leg: ParlayLeg):
    from src.domain.selection import Selection

    return Selection(
        match_id=leg.match_id,
        match_no=leg.match_no,
        league="",
        home_team=leg.home_team,
        away_team=leg.away_team,
        play_type=leg.play_type,
        outcome_key=leg.outcome_label,
        outcome_label=leg.outcome_label,
        odds=leg.odds,
        fair_prob=leg.fair_prob,
        model_prob=leg.model_prob,
        edge=leg.model_prob - leg.fair_prob,
        ev=leg.ev,
        confidence=leg.model_prob,
        risk_level=leg.risk_level,
        risk_score=0.0,
    )

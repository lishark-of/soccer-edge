from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ParlayLeg:
    match_id: str
    match_no: str
    home_team: str
    away_team: str
    play_type: str
    outcome_label: str
    odds: float
    model_prob: float
    fair_prob: float
    ev: float
    risk_level: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PayoutEstimate:
    pass_type: str
    ticket_count: int
    stake_per_ticket: float
    total_stake: float
    combined_odds: float
    theoretical_max_payout: float
    breakeven_probability: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParlayCandidate:
    pass_type: str
    legs: list[ParlayLeg]
    combined_odds: float
    hit_probability: float
    market_probability: float
    ev: float
    risk_level: str
    risk_score: float
    payout: PayoutEstimate
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pass_type": self.pass_type,
            "legs": [leg.to_dict() for leg in self.legs],
            "combined_odds": self.combined_odds,
            "hit_probability": self.hit_probability,
            "market_probability": self.market_probability,
            "ev": self.ev,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "payout": self.payout.to_dict(),
            "warnings": list(self.warnings),
        }

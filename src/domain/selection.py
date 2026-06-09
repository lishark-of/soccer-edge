from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Selection:
    match_id: str
    match_no: str
    league: str
    home_team: str
    away_team: str
    play_type: str
    outcome_key: str
    outcome_label: str
    odds: float
    fair_prob: float
    model_prob: float
    edge: float
    ev: float
    confidence: float
    risk_level: str
    risk_score: float
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    supports_single: bool = True
    correlation_group: str = ""
    recommendation: str = ""
    model_components: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .parlay import ParlayCandidate
from .selection import Selection


@dataclass(slots=True)
class MatchAnalysis:
    selection: Selection
    recommended_use: str

    def to_dict(self) -> dict[str, Any]:
        payload = self.selection.to_dict()
        payload["recommended_use"] = self.recommended_use
        return payload


@dataclass(slots=True)
class DailyAnalysisReport:
    date: str
    matches_analyzed: int
    single_candidates: list[MatchAnalysis] = field(default_factory=list)
    parlay_2x1_candidates: list[ParlayCandidate] = field(default_factory=list)
    parlay_3x1_candidates: list[ParlayCandidate] = field(default_factory=list)
    excluded_matches: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)
    model_version: str = "phase2b_market_poisson_elo_v0"
    model_components_available: list[str] = field(default_factory=lambda: ["market"])
    historical_data_status: str = "unavailable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "matches_analyzed": self.matches_analyzed,
            "single_candidates": [item.to_dict() for item in self.single_candidates],
            "parlay_2x1_candidates": [item.to_dict() for item in self.parlay_2x1_candidates],
            "parlay_3x1_candidates": [item.to_dict() for item in self.parlay_3x1_candidates],
            "excluded_matches": list(self.excluded_matches),
            "warnings": list(self.warnings),
            "disclaimers": list(self.disclaimers),
            "model_version": self.model_version,
            "model_components_available": list(self.model_components_available),
            "historical_data_status": self.historical_data_status,
        }

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Match:
    match_id: str
    match_no: str
    date: str
    league: str
    kickoff_at: str
    home_team: str
    away_team: str
    supports_single: bool = True
    correlation_group: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "scheduled"
    source: str = "mock"
    raw: dict[str, Any] = field(default_factory=dict)
    had_odds: dict[str, float | None] | None = None
    hhad_odds: dict[str, float | None] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["match_num"] = self.match_no
        payload["kickoff_time"] = self.kickoff_at
        payload["is_single_allowed"] = self.supports_single
        return payload

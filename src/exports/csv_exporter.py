from __future__ import annotations

import csv
from pathlib import Path

from src.domain.analysis_result import DailyAnalysisReport


def export_analysis_csv(report: DailyAnalysisReport, output_dir: str = "exports_output") -> Path:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"analysis_{report.date}.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "match_no",
                "league",
                "home_team",
                "away_team",
                "play_type",
                "direction",
                "odds",
                "fair_prob",
                "model_prob",
                "edge",
                "ev",
                "risk_level",
                "recommended_use",
            ]
        )
        for item in report.single_candidates:
            selection = item.selection
            writer.writerow(
                [
                    selection.match_no,
                    selection.league,
                    selection.home_team,
                    selection.away_team,
                    selection.play_type,
                    selection.outcome_label,
                    selection.odds,
                    selection.fair_prob,
                    selection.model_prob,
                    selection.edge,
                    selection.ev,
                    selection.risk_level,
                    item.recommended_use,
                ]
            )
    return path

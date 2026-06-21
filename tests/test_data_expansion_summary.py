from __future__ import annotations

import json
from pathlib import Path

from src.learning.data_expansion import build_data_expansion_summary


def test_data_expansion_reads_cached_sources(tmp_path: Path):
    root = tmp_path / "cache"
    (root / "api_football").mkdir(parents=True)
    (root / "the_odds_api").mkdir(parents=True)
    (root / "weather").mkdir(parents=True)
    (root / "api_football_enrichment").mkdir(parents=True)
    (root / "api_football" / "fixtures_2026-06-22.json").write_text(json.dumps({"response": [{"fixture": {"id": 1}}]}), encoding="utf-8")
    (root / "the_odds_api" / "odds_soccer_fifa_world_cup_2026-06-22.json").write_text(json.dumps([{"id": "a"}, {"id": "b"}]), encoding="utf-8")
    (root / "weather" / "forecast_Lisbon_2026-06-22.json").write_text(json.dumps({"hourly": {}}), encoding="utf-8")
    (root / "api_football_enrichment" / "injuries_fixture_1.json").write_text(json.dumps({"response": []}), encoding="utf-8")

    summary = build_data_expansion_summary("2026-06-22", cache_root=root)

    assert summary["status"] == "available"
    assert summary["sources"]["api_football"]["fixture_count"] == 1
    assert summary["sources"]["the_odds_api"]["odds_event_count"] == 2
    assert summary["sources"]["weather"]["city_count"] == 1
    dumped = json.dumps(summary, ensure_ascii=False)
    assert "sk-" not in dumped
    assert "Bearer " not in dumped


def test_data_expansion_reports_gaps_when_missing(tmp_path: Path):
    summary = build_data_expansion_summary("2026-06-22", cache_root=tmp_path / "cache")
    assert summary["status"] == "missing"
    assert summary["gaps"]
    assert summary["coverage_grade"] == "D"

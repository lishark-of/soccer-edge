from src.intelligence import fusion


def test_next_available_returns_selected_date(monkeypatch):
    calls = []

    def fake_preview(provider_name="auto", target_date=None, external_signals_path=None, bankroll=10000.0, risk_profile="aggressive"):
        calls.append(target_date)
        count = 2 if target_date == "2026-06-12" else 0
        return {
            "date": target_date,
            "provider_used": "sporttery" if count else "mock",
            "matches_count": count,
            "optimizer": {"selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []}},
            "top_single_observations": [],
            "top_total_goals_observations": [],
            "top_score_observations": [],
            "missing_signals": [],
            "warnings": [],
            "data_source_status": {"status": "available" if count else "empty"},
        }

    monkeypatch.setattr(fusion, "build_intelligence_preview", fake_preview)
    result = fusion.build_next_available_preview(start_date="2026-06-10")
    assert result["selected_date"] == "2026-06-12"
    assert result["matches_count"] == 2
    assert calls == ["2026-06-10", "2026-06-11", "2026-06-12"]


def test_next_available_defaults_aggressive(monkeypatch):
    seen = {}

    def fake_preview(provider_name="auto", target_date=None, external_signals_path=None, bankroll=10000.0, risk_profile="aggressive"):
        seen["risk_profile"] = risk_profile
        return {"date": target_date, "matches_count": 1, "provider_used": "sporttery", "optimizer": {"selected_portfolio": {}}, "data_source_status": {}}

    monkeypatch.setattr(fusion, "build_intelligence_preview", fake_preview)
    fusion.build_next_available_preview(start_date="2026-06-10")
    assert seen["risk_profile"] == "aggressive"

from src.intelligence import fusion
from src.view_models.next_available_view import build_next_available_view


def test_next_available_returns_selected_date(monkeypatch):
    scan_calls = []
    full_calls = []

    def fake_scan(provider_name, target_date):
        scan_calls.append(target_date)
        count = 2 if target_date == "2026-06-12" else 0
        return {"date": target_date, "matches_count": count, "provider_used": "sporttery" if count else "sporttery", "status": "available" if count else "empty"}

    def fake_preview(provider_name="auto", target_date=None, external_signals_path=None, bankroll=10000.0, risk_profile="aggressive"):
        full_calls.append(target_date)
        return {
            "date": target_date,
            "provider_used": "sporttery",
            "matches_count": 2,
            "optimizer": {"selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []}},
            "top_single_observations": [],
            "top_total_goals_observations": [],
            "top_score_observations": [],
            "missing_signals": [],
            "warnings": [],
            "data_source_status": {"status": "available"},
        }

    monkeypatch.setattr(fusion, "_scan_next_available_attempt", fake_scan)
    monkeypatch.setattr(fusion, "build_intelligence_preview", fake_preview)
    result = fusion.build_next_available_preview(start_date="2026-06-10")
    assert result["selected_date"] == "2026-06-12"
    assert result["matches_count"] == 2
    assert scan_calls == ["2026-06-10", "2026-06-11", "2026-06-12", "2026-06-13"]
    assert full_calls == ["2026-06-12"]
    assert result["scan_window"]["complete"] is True
    assert result["scan_window"]["days_checked"] == 4


def test_next_available_defaults_aggressive(monkeypatch):
    seen = {}

    def fake_preview(provider_name="auto", target_date=None, external_signals_path=None, bankroll=10000.0, risk_profile="aggressive"):
        seen["risk_profile"] = risk_profile
        return {"date": target_date, "matches_count": 1, "provider_used": "sporttery", "optimizer": {"selected_portfolio": {}}, "data_source_status": {}}

    monkeypatch.setattr(fusion, "build_intelligence_preview", fake_preview)
    fusion.build_next_available_preview(start_date="2026-06-10")
    assert seen["risk_profile"] == "aggressive"


def test_next_available_passes_external_signals_path(monkeypatch):
    seen = []

    def fake_scan(provider_name, target_date):
        return {"date": target_date, "matches_count": 0, "provider_used": "sporttery", "status": "empty"}

    def fake_preview(provider_name="auto", target_date=None, external_signals_path=None, bankroll=10000.0, risk_profile="aggressive"):
        seen.append(external_signals_path)
        return {"date": target_date, "matches_count": 0, "provider_used": "mock", "optimizer": {"selected_portfolio": {}}, "data_source_status": {}}

    monkeypatch.setattr(fusion, "_scan_next_available_attempt", fake_scan)
    monkeypatch.setattr(fusion, "build_intelligence_preview", fake_preview)
    fusion.build_next_available_preview(start_date="2026-06-10", external_signals_path="data/fixtures/signals.json")
    assert seen == ["data/fixtures/signals.json"]


def test_next_available_view_includes_source_health():
    view = build_next_available_view(
        {
            "selected_date": "2026-06-10",
            "provider_used": "sporttery",
            "matches_count": 2,
            "optimizer": {
                "candidate_rankings": {
                    "parlay_2x1": [{"type": "parlay_2x1", "legs": "A+B", "odds": 4.0, "model_prob": 0.2, "market_prob": 0.18, "ev": -0.1, "edge": 0.01, "selected": False, "status": "未入选", "reject_reason": "组合风险过高"}],
                    "parlay_3x1": [{"type": "parlay_3x1", "legs": "A+B+C", "odds": 9.0, "model_prob": 0.08, "market_prob": 0.05, "ev": -0.2, "edge": 0.01, "selected": False, "status": "未入选", "reject_reason": "3串1 风险过高"}],
                },
                "selected_portfolio": {},
            },
            "attempts": [{"date": "2026-06-10", "matches_count": 2, "provider_used": "sporttery", "status": "available"}],
            "scan_window": {"start_date": "2026-06-10", "end_date": "2026-06-13", "days_checked": 4, "complete": True},
            "data_source_status": {"status": "available"},
            "contexts": [],
        }
    )
    assert view["source_health"]["health"] == "stable"
    assert view["source_health"]["scanned_dates"] == ["2026-06-10"]
    assert view["source_health"]["scan_window"]["complete"] is True
    assert view["source_health"]["successful_attempts"] == 1
    assert view["source_health"]["all_attempts_stable"] is True
    assert view["source_health"]["fallback_attempts"] == 0
    assert view["source_health"]["reliability_label_zh"] == "高"
    assert view["source_health"]["reliability_score"] >= 90
    assert view["top_2x1_display_mode"] == "nearest_rejected"
    assert view["top_2x1_display"][0]["reject_reason"] == "组合风险过高"
    assert "最接近的候选" in view["top_2x1_empty_explanation"]
    assert view["top_rejected_2x1"][0]["reject_reason"] == "组合风险过高"
    assert view["top_rejected_3x1"][0]["reject_reason"] == "3串1 风险过高"
    assert view["operation_entry"]["title"] == "回测表现怎么看"
    assert any("资金曲线" in item for item in view["operation_entry"]["metrics"])
    assert any("玩法贡献" in item for item in view["operation_entry"]["metrics"])


def test_next_available_view_marks_degraded_scan_window():
    view = build_next_available_view(
        {
            "selected_date": "2026-06-10",
            "provider_used": "sporttery",
            "matches_count": 2,
            "optimizer": {"candidate_rankings": {}, "selected_portfolio": {}},
            "attempts": [
                {"date": "2026-06-10", "matches_count": 2, "provider_used": "sporttery", "status": "available"},
                {"date": "2026-06-11", "matches_count": 0, "provider_used": "mock", "status": "fallback"},
            ],
            "scan_window": {"start_date": "2026-06-10", "end_date": "2026-06-13", "days_checked": 4, "complete": True},
            "data_source_status": {"status": "available"},
            "contexts": [],
        }
    )
    health = view["source_health"]
    assert health["health"] == "degraded"
    assert health["all_attempts_stable"] is False
    assert health["sporttery_attempts"] == 1
    assert health["fallback_attempts"] == 1
    assert health["partial_fallback_used"] is True
    assert health["reliability_label_zh"] in {"中", "低"}
    assert health["reliability_score"] < 90
    assert "Sporttery 成功" in health["source_action_items"][0]
    assert "mock/fallback" in health["degraded_reason_zh"]

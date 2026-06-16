from src.acceptance.phase2r import build_phase2r_acceptance_report
from src.api.routes import dispatch_route


def test_phase2r_acceptance_report_shape():
    report = build_phase2r_acceptance_report()
    assert report["acceptance_version"] == "phase2r_acceptance_v0"
    assert report["total_count"] == 5
    assert {check["id"] for check in report["checks"]} == {
        "R1_parlay_discipline",
        "R2_today_simplified",
        "R3_deepseek_optional_explainer",
        "R4_clv_tracking",
        "R5_backtest_credibility",
    }


def test_phase2r_acceptance_api_shape():
    payload = dispatch_route("/api/view/phase2r-acceptance", {})
    assert payload["ok"] is True
    assert payload["data"]["acceptance_version"] == "phase2r_acceptance_v0"
    assert payload["data"]["total_count"] == 5

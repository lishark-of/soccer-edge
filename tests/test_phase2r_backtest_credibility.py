from src.backtesting.credibility import build_backtest_credibility_from_rows, build_backtest_credibility_report
from src.api.routes import dispatch_route


def test_fixture_source_is_capped_at_c_grade_even_with_complete_fields():
    rows = [
        {
            "date": f"2026-01-{(idx % 28) + 1:02d}",
            "league": "L",
            "home_team": f"H{idx}",
            "away_team": f"A{idx}",
            "home_goals": "1",
            "away_goals": "0",
            "odds_home": "2.0",
            "odds_draw": "3.2",
            "odds_away": "3.5",
        }
        for idx in range(120)
    ]
    report = build_backtest_credibility_from_rows(rows, source_type="fixture")
    assert report["score"] <= 60
    assert report["grade"] == "C"


def test_user_csv_missing_odds_gets_next_step(tmp_path):
    path = tmp_path / "history.csv"
    path.write_text(
        "date,league,home_team,away_team,home_goals,away_goals\n"
        "2026-01-01,L,A,B,1,0\n"
        "2026-01-02,L,C,D,0,1\n",
        encoding="utf-8",
    )
    report = build_backtest_credibility_report(path, source_type="user_csv")
    assert report["odds_coverage"] == 0.0
    assert any("赔率" in step for step in report["next_steps"])


def test_backtest_view_includes_data_credibility():
    payload = dispatch_route(
        "/api/view/backtest",
        {"historical_data": "data/fixtures/historical_matches_backtest_sample.csv", "source_type": "fixture"},
    )
    assert payload["ok"] is True
    credibility = payload["data"]["backtest_credibility"]
    assert credibility["score"] <= 60
    assert credibility["grade"] in {"C", "D"}

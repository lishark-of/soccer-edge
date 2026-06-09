from src.paper_trading.selection_policy import allocate_paper_stakes, select_daily_observations


def _candidate(ev, edge, risk="low"):
    return {"home_team": "A", "away_team": "B", "ev": ev, "edge": edge, "risk_level": risk, "odds": 2.0}


def test_allocate_paper_stakes_respects_daily_cap():
    observations = {"singles": [_candidate(0.1, 0.05) for _ in range(10)], "parlay_2x1": [], "parlay_3x1": []}
    allocated = allocate_paper_stakes(observations, 10000)
    assert sum(item["paper_stake"] for item in allocated) <= 300


def test_select_daily_observations_prefers_singles():
    analysis = {"single_candidates": [_candidate(0.08, 0.04), _candidate(0.06, 0.03), _candidate(0.02, 0.01)]}
    selected = select_daily_observations(analysis)
    assert len(selected["singles"]) == 2
    assert selected["singles"][0]["ev"] >= selected["singles"][1]["ev"]

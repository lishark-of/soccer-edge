from src.optimizer.candidate_pool import build_candidate_pool, build_parlay_candidates


def test_ev_calculation_and_parlay_probability():
    analysis = {"date": "2026-06-09", "single_candidates": [
        {"match_id": "m1", "league": "A", "home_team": "H1", "away_team": "A1", "outcome_key": "win", "outcome_label": "主胜", "odds": 2.0, "fair_prob": 0.48, "model_prob": 0.55, "edge": 0.07, "ev": 0.1, "risk_level": "low"},
        {"match_id": "m2", "league": "B", "home_team": "H2", "away_team": "A2", "outcome_key": "lose", "outcome_label": "客胜", "odds": 2.5, "fair_prob": 0.36, "model_prob": 0.44, "edge": 0.08, "ev": 0.1, "risk_level": "low"},
    ]}
    pool = build_candidate_pool(analysis)
    assert round(pool[0]["ev"], 4) == 0.1
    parlays = [item for item in build_parlay_candidates(pool, max_legs=2) if not item.get("rejected")]
    assert parlays[0]["combo_prob"] == round(0.55 * 0.44, 6)

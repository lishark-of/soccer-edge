from src.intelligence.feature_context import build_match_context
from src.intelligence.fusion import build_observations_from_context, fused_probability
from src.domain.match import Match


def _match():
    return Match(match_id="m1", match_no="001", date="2026-06-10", league="测试", kickoff_at="2026-06-10T20:00:00+08:00", home_team="主队", away_team="客队", had_odds={"win": 2.0, "draw": 3.2, "lose": 3.6}, hhad_odds={"handicap": -1.0, "win": 4.0, "draw": 3.6, "lose": 1.8})


def test_fused_probability_normalized():
    context = build_match_context(_match())
    fused = fused_probability(context)
    assert abs(sum(fused["had"].values()) - 1.0) < 1e-6
    assert "top_scores" in fused


def test_observations_include_reasons():
    context = build_match_context(_match())
    observations, candidates = build_observations_from_context(context)
    assert observations
    assert candidates
    assert all("selection_reason" in row for row in observations)

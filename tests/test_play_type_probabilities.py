from src.intelligence.feature_context import build_match_context
from src.intelligence.fusion import fused_probability
from src.domain.match import Match


def test_hhad_total_goals_and_scores_output():
    match = Match(match_id="m1", match_no="001", date="2026-06-10", league="测试", kickoff_at="2026-06-10T20:00:00+08:00", home_team="主队", away_team="客队", had_odds={"win": 2.0, "draw": 3.2, "lose": 3.6}, hhad_odds={"handicap": -1.0, "win": 4.0, "draw": 3.6, "lose": 1.8})
    fused = fused_probability(build_match_context(match))
    assert abs(sum(fused["hhad"].values()) - 1.0) < 1e-6
    assert fused["total_goals"]
    assert len(fused["top_scores"]) == 5

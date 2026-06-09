from src.backtesting.historical_loader import HistoricalMatch
from src.domain.match import Match
from src.modeling.team_strength import build_team_strengths, estimate_xg_for_match


def test_team_strength_uses_only_matches_before_date():
    matches = [
        HistoricalMatch("2026-06-01", "Mock", "Alpha FC", "Beta United", 2, 1, "H"),
        HistoricalMatch("2026-06-10", "Mock", "Alpha FC", "Beta United", 8, 0, "H"),
    ]

    strengths = build_team_strengths(matches, before_date="2026-06-09")

    assert strengths["sample_size"] == 1
    assert strengths["teams"]["Alpha FC"]["goals_for"] == 2


def test_estimate_xg_for_match_returns_defaults_when_missing_history():
    match = Match(
        match_id="m1",
        match_no="001",
        date="2026-06-09",
        league="Mock",
        kickoff_at="2026-06-09T12:00:00+08:00",
        home_team="Unknown A",
        away_team="Unknown B",
    )

    home_xg, away_xg = estimate_xg_for_match(match, {"sample_size": 0, "teams": {}})

    assert home_xg == 1.35
    assert away_xg == 1.10

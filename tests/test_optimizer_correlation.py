from src.optimizer.correlation import correlation_discount, same_match_forbidden


def test_correlation_discount_defaults():
    a = {"match_id": "1", "league": "A", "home_team": "A1", "away_team": "A2"}
    b = {"match_id": "2", "league": "B", "home_team": "B1", "away_team": "B2"}
    assert correlation_discount([a, b]) == 1.0


def test_same_league_discount():
    a = {"match_id": "1", "league": "A", "home_team": "A1", "away_team": "A2"}
    b = {"match_id": "2", "league": "A", "home_team": "B1", "away_team": "B2"}
    assert correlation_discount([a, b]) == 0.95


def test_same_team_discount_and_same_match_forbidden():
    a = {"match_id": "1", "league": "A", "home_team": "A1", "away_team": "A2"}
    b = {"match_id": "2", "league": "B", "home_team": "A1", "away_team": "B2"}
    c = {"match_id": "1", "league": "C", "home_team": "C1", "away_team": "C2"}
    assert correlation_discount([a, b]) == 0.85
    assert same_match_forbidden([a, c]) is True
    assert correlation_discount([a, c]) == 0.0

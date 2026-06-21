from src.optimizer.correlation import correlation_quality


def _leg(match_id, home, away, league="A", play_type="had", outcome_key="home"):
    return {
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "league": league,
        "play_type": play_type,
        "outcome_key": outcome_key,
    }


def test_correlation_quality_blocks_same_match():
    quality = correlation_quality([
        _leg("m1", "A", "B", play_type="had"),
        _leg("m1", "A", "B", play_type="hhad"),
    ])
    assert quality["level"] == "blocked"
    assert quality["score"] == 0


def test_correlation_quality_penalizes_same_play_type():
    quality = correlation_quality([
        _leg("m1", "A", "B", league="L1", play_type="hhad", outcome_key="home"),
        _leg("m2", "C", "D", league="L2", play_type="hhad", outcome_key="home"),
    ])
    assert quality["score"] < 92
    assert "same_play_type" in quality["risk_flags"]


def test_correlation_quality_rewards_diverse_legs():
    quality = correlation_quality([
        _leg("m1", "A", "B", league="L1", play_type="had", outcome_key="home"),
        _leg("m2", "C", "D", league="L2", play_type="total_goals", outcome_key="over2"),
    ])
    assert quality["level"] == "strong"
    assert quality["score"] >= 80

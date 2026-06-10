from src.intelligence.feature_context import build_match_context
from src.domain.match import Match


def test_missing_news_lineup_weather_not_fabricated():
    match = Match(match_id="m1", match_no="001", date="2026-06-10", league="测试", kickoff_at="2026-06-10T20:00:00+08:00", home_team="主队", away_team="客队", had_odds={"win": 2.0, "draw": 3.2, "lose": 3.6})
    context = build_match_context(match)
    assert context["signals"]["news"]["status"] == "not_connected"
    assert context["signals"]["weather"]["impact"] == "unknown"
    assert "news" in context["missing_signals"]

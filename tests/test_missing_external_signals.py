from src.intelligence.feature_context import build_match_context
from src.domain.match import Match


def test_missing_news_lineup_weather_not_fabricated():
    match = Match(match_id="m1", match_no="001", date="2026-06-10", league="测试", kickoff_at="2026-06-10T20:00:00+08:00", home_team="主队", away_team="客队", had_odds={"win": 2.0, "draw": 3.2, "lose": 3.6})
    context = build_match_context(match)
    assert context["signals"]["news"]["status"] == "not_connected"
    assert context["signals"]["weather"]["impact"] == "unknown"
    assert context["signals"]["motivation"]["status"] == "not_connected"
    assert context["signals"]["motivation"]["impact"] == "unknown"
    assert context["signals"]["schedule"]["status"] == "basic_only"
    assert context["signals"]["schedule"]["impact"] == "unknown"
    assert context["signals"]["travel"]["status"] == "not_connected"
    assert context["signals"]["travel"]["impact"] == "unknown"
    assert "news" in context["missing_signals"]
    assert "motivation" in context["missing_signals"]
    assert "travel" in context["missing_signals"]


def test_external_motivation_signal_is_connected_without_fabrication():
    match = Match(match_id="m1", match_no="001", date="2026-06-10", league="测试", kickoff_at="2026-06-10T20:00:00+08:00", home_team="主队", away_team="客队", had_odds={"win": 2.0, "draw": 3.2, "lose": 3.6})
    context = build_match_context(match, external_signals={"motivation": "友谊赛轮换风险较高"})
    assert context["signals"]["motivation"]["status"] == "connected"
    assert context["signals"]["motivation"]["items"] == ["友谊赛轮换风险较高"]

from src.providers.api_football_enrichment import _injury_signal, _lineup_signal


def test_injury_empty_is_checked_empty_not_confirmed():
    signal = _injury_signal({"status": "ok", "response": []})
    assert signal["status"] == "checked_empty"
    assert "不等于确认无伤停" in signal["message_zh"]


def test_lineup_empty_is_checked_empty():
    signal = _lineup_signal({"status": "ok", "response": []})
    assert signal["status"] == "checked_empty"
    assert "临近开赛" in signal["message_zh"]

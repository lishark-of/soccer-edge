from src.providers.weather_provider import resolve_weather_city


def test_weather_venue_city_is_high_confidence_source():
    resolved = resolve_weather_city("Lisbon", "葡萄牙", "尼日利亚")
    assert resolved["city"] == "Lisbon"
    assert resolved["source"] == "venue_city"


def test_weather_country_fallback_is_marked_estimated():
    resolved = resolve_weather_city(None, "葡萄牙", "尼日利亚")
    assert resolved["city"] == "Lisbon"
    assert resolved["source"] == "team_country_fallback"
    assert "兜底" in resolved["message_zh"]

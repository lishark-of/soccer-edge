from src.intelligence.external_signals_loader import load_external_signals_with_status, preview_external_signals


def test_external_signals_example_loads_match_num():
    signals, status = load_external_signals_with_status("data/fixtures/external_signals_example.json")
    assert status["load_status"] == "loaded"
    assert "周三201" in signals


def test_external_signals_preview_shape():
    payload = preview_external_signals("data/fixtures/external_signals_example.json", "2026-06-10")
    assert payload["signals_count"] >= 1
    assert "injuries" in payload["supplied_fields"]

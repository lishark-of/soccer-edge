from src.intelligence.source_coverage import _warnings


def test_source_coverage_warnings_are_human_readable():
    notes = _warnings(
        {"status": "timeout", "message_zh": "raw api error"},
        {"status": "ok"},
        [
            {
                "injuries": {"status": "error"},
                "lineup": {"status": "checked_empty"},
                "weather": {"status": "fallback_estimated"},
                "news": {"status": "checked_empty"},
            }
        ],
    )
    text = "\n".join(notes)
    assert "覆盖审计：API-Football 当前未稳定返回" in text
    assert "覆盖审计：1 场天气使用城市兜底估算" in text
    assert "覆盖审计：1 场新闻已检索但未返回公开报道" in text

from src.learning.observation_snapshot import build_observation_snapshot


def test_snapshot_preserves_ai_research_status():
    preview = {
        "selected_date": "2026-06-10",
        "provider_used": "mock",
        "matches_count": 2,
        "credibility_gate": {"combo_gate": "closed", "reason_zh": "可信度不足"},
        "optimizer": {"selected_portfolio": {}, "no_combo_reason": "暂不组合"},
        "ai_combo_research": {
            "ds_status": "loaded",
            "ds_attempted": True,
            "ds_completed": True,
            "token_in": 88,
            "token_out": 22,
            "token_total": 110,
            "ai_summary": {"text": "研究摘要"},
        },
        "trader_review": {"final_call_zh": "暂不强行串联"},
    }
    snapshot = build_observation_snapshot(preview)
    assert snapshot["ai_research"]["ds_status"] == "loaded"
    assert snapshot["ai_research"]["ds_completed"] is True
    assert snapshot["ai_research"]["token_total"] == 110
    assert snapshot["trader_review"]["final_call_zh"] == "暂不强行串联"

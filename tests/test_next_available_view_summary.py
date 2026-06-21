from src.view_models.next_available_view import build_next_available_view


def test_next_available_view_exposes_ai_combo_and_learning_summaries():
    preview = {
        "date": "2026-06-10",
        "selected_date": "2026-06-10",
        "provider_used": "mock",
        "matches_count": 2,
        "attempts": [],
        "scan_window": {"complete": True},
        "warnings": [],
        "source_coverage": {"warnings": [], "match_coverage": [], "by_match_id": {}},
        "intelligence_completeness": {"score": 42, "main_gaps_zh": ["伤停", "首发"]},
        "reliability_summary": {},
        "prematch_workflow": {"stage": "t_plus_1", "stage_label_zh": "T+1 预观察"},
        "optimizer": {
            "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
            "candidate_rankings": {},
            "no_combo_reason": "缺失情报较多，暂不组合。",
            "best_parlay_summary": {
                "user_combo_board": {},
                "no_combo_reason": "缺失情报较多，暂不组合。",
                "rejected_combos": [],
            },
        },
        "credibility_gate": {"combo_gate": "closed", "label_zh": "暂不最终串联", "reason_zh": "等待补齐情报。"},
        "top_single_observations": [],
        "top_total_goals_observations": [],
        "top_score_observations": [],
        "missing_signals": ["伤停", "首发"],
        "data_source_status": {},
    }
    view = build_next_available_view(preview)
    assert "combo_gate_summary_zh" in view
    assert view["combo_gate_summary_zh"]
    assert "daily_learning_summary_zh" in view
    assert isinstance(view.get("daily_learning_digest"), dict)
    assert isinstance(view.get("window_learning_digests"), list)
    assert isinstance(view.get("daily_learning_report"), dict)
    assert isinstance(view.get("window_learning_reports"), list)
    assert isinstance(view.get("daily_learning_metrics"), list)
    assert isinstance(view.get("window_learning_metrics"), list)
    assert isinstance(view.get("window_learning_summaries_zh"), list)
    assert "ai_research_layer" in view
    assert "ds_attempted" in view["ai_research_layer"]
    assert "ds_completed" in view["ai_research_layer"]
    assert "last_token_total" in view["ai_research_layer"]
    assert "config_status_zh" in view["ai_research_layer"]
    assert "next_step_zh" in view["ai_research_layer"]
    assert "llm_status" in view
    assert "ai_research_status" in view
    assert view["ai_research_status"]["label_zh"]
    assert view["ai_research_status"]["summary_zh"]
    assert isinstance(view.get("coverage_summary_cards"), list)
    assert isinstance(view.get("critical_gap_list_zh"), list)
    assert isinstance(view.get("homepage_missing_actions"), list)
    assert view.get("today_focus_summary_zh")
    assert view.get("final_decision_card", {}).get("verdict_zh")
    assert "single_summary_zh" in view["final_decision_card"]
    assert "combo_summary_zh" in view["final_decision_card"]
    assert isinstance(view["final_decision_card"].get("main_blockers_zh"), list)

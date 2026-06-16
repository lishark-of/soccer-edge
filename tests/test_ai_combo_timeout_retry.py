import src.explain.ai_combo_research as mod


def test_ai_combo_research_retries_timeout_with_compact_packet(monkeypatch):
    calls = []

    def fake_explain(kind, payload, context=None):
        calls.append({"kind": kind, "payload": payload, "context": dict(context or {})})
        if len(calls) == 1:
            return {
                "provider": "local",
                "enabled": True,
                "status": "error",
                "status_zh": "DS 请求失败",
                "text": "本地摘要",
                "warnings": [],
                "provider_requested": "auto",
                "provider_resolved": "local",
                "ds_status": "error",
                "ds_status_zh": "DS 请求失败",
                "ds_attempted": True,
                "ds_completed": False,
                "ds_error_code": "request_timeout",
                "token_in": None,
                "token_out": None,
                "token_total": None,
                "fallback_reason": "DeepSeek 请求超时，已改用本地摘要。",
                "display_status_zh": "DeepSeek 请求超时，已改用本地摘要。",
            }
        return {
            "provider": "deepseek",
            "enabled": True,
            "status": "loaded",
            "status_zh": "DS Pro 已参与",
            "text": "DS 研究摘要\nSTRUCTURED_NOTES_JSON:{\"daily_summary_zh\":\"今日先看单关。\",\"single_notes\":[],\"combo_notes\":[],\"total_goals_notes\":[],\"score_notes\":[],\"rejected_combo_notes\":[],\"match_notes\":[]}",
            "warnings": [],
            "provider_requested": "auto",
            "provider_resolved": "deepseek",
            "ds_status": "loaded",
            "ds_status_zh": "DS Pro 已参与",
            "ds_attempted": True,
            "ds_completed": True,
            "ds_error_code": "",
            "token_in": 100,
            "token_out": 40,
            "token_total": 140,
            "fallback_reason": "",
            "display_status_zh": "DS Pro 已参与本次研究。",
        }

    monkeypatch.setattr(mod, "explain_with_optional_deepseek", fake_explain)
    monkeypatch.setattr(mod, "build_learning_history", lambda: {"settled_count": 0, "hit_rate": None, "brier_score": None, "log_loss": None, "calibration_bins": [], "bucket_rows": [], "lessons": []})
    monkeypatch.setattr(mod, "build_odds_learning_view", lambda history: {"plain_language_rules": [], "lightweight_learning_path": []})
    monkeypatch.setattr(mod, "llm_status_payload", lambda: {"status": "ready", "status_zh": "可自动研究", "max_output_tokens": 4000, "max_input_tokens": 24000, "ready_for_auto": True})

    result = mod.build_ai_combo_research(
        {
            "date": "2026-06-10",
            "selected_date": "2026-06-10",
            "provider_used": "mock",
            "matches_analyzed": 2,
            "risk_profile": "aggressive",
            "credibility_gate": {"combo_gate": "closed", "reason_zh": "可信度不足"},
            "best_parlay_summary": {
                "credibility_gate": {"combo_gate": "closed", "reason_zh": "可信度不足"},
                "user_combo_board": {
                    "headline_zh": "今日不强行组合",
                    "user_verdict_zh": "先看单关。",
                    "closing_line_review": {},
                    "primary_action_zh": "先看单关",
                },
                "best_single": {"match": "A vs B 客胜", "odds": 2.1, "model_prob": 0.55},
                "best_2x1": {"status": "empty", "message_zh": "暂无"},
                "best_3x1_if_allowed": {"status": "empty", "message_zh": "暂无"},
                "daily_2x1_candidate": {"status": "empty", "message_zh": "暂无"},
                "daily_3x1_candidate": {"status": "empty", "message_zh": "暂无"},
                "best_risk_adjusted_combo": {"status": "empty", "message_zh": "暂无"},
                "rejected_combos": [],
            },
        },
        run_ai=True,
        ai_provider="auto",
    )

    assert len(calls) >= 2
    assert calls[0]["context"]["max_tokens_override"] == 900
    assert calls[1]["payload"]["timeout_compact_retry_only"] is True
    assert result["ds_completed"] is True
    assert result["provider_resolved"] == "deepseek"
    assert result["timeout_retry"]["attempted"] is True
    assert result["timeout_retry"]["success"] is True


def test_ai_combo_research_retries_empty_content_with_compact_packet(monkeypatch):
    calls = []

    def fake_explain(kind, payload, context=None):
        calls.append({"kind": kind, "payload": payload, "context": dict(context or {})})
        if len(calls) == 1:
            return {
                "provider": "local",
                "enabled": True,
                "status": "error",
                "status_zh": "DS 请求失败",
                "text": "本地摘要",
                "warnings": [],
                "provider_requested": "auto",
                "provider_resolved": "local",
                "ds_status": "error",
                "ds_status_zh": "DS 请求失败",
                "ds_attempted": True,
                "ds_completed": False,
                "ds_error_code": "empty_content",
                "token_in": None,
                "token_out": None,
                "token_total": None,
                "fallback_reason": "DeepSeek 未返回有效解释内容，已改用本地摘要。",
                "display_status_zh": "DeepSeek 未返回有效解释内容，已改用本地摘要。",
            }
        return {
            "provider": "deepseek",
            "enabled": True,
            "status": "loaded",
            "status_zh": "DS Pro 已参与",
            "text": "DS 研究摘要",
            "warnings": [],
            "provider_requested": "auto",
            "provider_resolved": "deepseek",
            "ds_status": "loaded",
            "ds_status_zh": "DS Pro 已参与",
            "ds_attempted": True,
            "ds_completed": True,
            "ds_error_code": "",
            "token_in": 88,
            "token_out": 28,
            "token_total": 116,
            "fallback_reason": "",
            "display_status_zh": "DS Pro 已参与本次研究。",
        }

    monkeypatch.setattr(mod, "explain_with_optional_deepseek", fake_explain)
    monkeypatch.setattr(mod, "build_learning_history", lambda: {"settled_count": 0, "hit_rate": None, "brier_score": None, "log_loss": None, "calibration_bins": [], "bucket_rows": [], "lessons": []})
    monkeypatch.setattr(mod, "build_odds_learning_view", lambda history: {"plain_language_rules": [], "lightweight_learning_path": []})
    monkeypatch.setattr(mod, "llm_status_payload", lambda: {"status": "ready", "status_zh": "可自动研究", "max_output_tokens": 4000, "max_input_tokens": 24000, "ready_for_auto": True})

    result = mod.build_ai_combo_research(
        {
            "date": "2026-06-10",
            "selected_date": "2026-06-10",
            "provider_used": "mock",
            "matches_analyzed": 2,
            "risk_profile": "aggressive",
            "credibility_gate": {"combo_gate": "closed", "reason_zh": "可信度不足"},
            "best_parlay_summary": {
                "credibility_gate": {"combo_gate": "closed", "reason_zh": "可信度不足"},
                "user_combo_board": {
                    "headline_zh": "今日不强行组合",
                    "user_verdict_zh": "先看单关。",
                    "closing_line_review": {},
                    "primary_action_zh": "先看单关",
                },
                "best_single": {"match": "A vs B 客胜", "odds": 2.1, "model_prob": 0.55},
                "best_2x1": {"status": "empty", "message_zh": "暂无"},
                "best_3x1_if_allowed": {"status": "empty", "message_zh": "暂无"},
                "daily_2x1_candidate": {"status": "empty", "message_zh": "暂无"},
                "daily_3x1_candidate": {"status": "empty", "message_zh": "暂无"},
                "best_risk_adjusted_combo": {"status": "empty", "message_zh": "暂无"},
                "rejected_combos": [],
            },
        },
        run_ai=True,
        ai_provider="auto",
    )

    assert len(calls) >= 2
    assert calls[1]["payload"]["timeout_compact_retry_only"] is True
    assert result["ds_completed"] is True
    assert result["timeout_retry"]["attempted"] is True

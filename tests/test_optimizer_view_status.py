from src.view_models.optimizer_view import build_optimizer_view


def test_optimizer_view_exposes_no_combo_state_and_ai_status():
    view = build_optimizer_view(
        {
            "risk_profile": "aggressive",
            "risk_profile_label": "进取",
            "provider_used": "mock",
            "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
            "candidate_rankings": {},
            "credibility_audit": {"credibility_score": 39, "grade": "D", "reasons": ["情报不足"]},
            "credibility_gate": {"label_zh": "不建议串联", "reason_zh": "可信度不足", "missing_information": ["伤停", "首发"]},
            "no_combo_reason": "可信度不足、情报缺失较多、组合风险高于模型优势。",
            "ai_combo_research": {"ds_status_zh": "DS 请求失败", "display_status_zh": "已回退本地摘要。"},
            "candidate_rankings": {
                "parlay_2x1": [
                    {
                        "type": "parlay_2x1",
                        "match": "A；B",
                        "odds": 3.2,
                        "ev": 0.08,
                        "edge": 0.03,
                        "confidence_score": 0.41,
                        "risk_level": "medium",
                        "status": "未入选",
                        "reject_reason": "未通过可信度门控",
                        "decision_reason_zh": "校准概率未覆盖赔率。",
                        "parlay_policy_zh": "当前更适合只保留单关观察。",
                        "hit_rate_discipline_zh": "命中率纪律不足。",
                    }
                ]
            },
            "best_parlay_summary": {"status": "no_combo", "label_zh": "暂无优秀串联观察", "no_combo_reason": "可信度不足"},
            "daily_learning_digest": {"summary_zh": "今日赛后学习摘要", "next_step_zh": "继续累计样本"},
            "window_learning_digests": [{"summary_zh": "近7天摘要", "next_step_zh": "补 CLV"}],
        }
    )
    assert view["no_combo_state"]["status"] == "no_combo"
    assert view["no_combo_state"]["reason_zh"]
    assert view["combo_gate_summary_zh"]
    assert view["ai_status_summary_zh"]
    assert view["ai_research_status"]["status"] == "fallback"
    assert view["ai_research_status"]["label_zh"] == "已回退本地摘要"
    assert any(card["label"] == "AI研究" for card in view["summary_cards"])
    assert view["daily_learning_digest"]["summary_zh"]
    assert view["window_learning_digests"][0]["summary_zh"]
    assert view["ai_research_layer"]["display_status_zh"]
    row = view["candidate_rankings"]["parlay_2x1"][0]
    assert "未入选原因" in row["discipline_summary_zh"]
    assert "情报缺口" in row["discipline_summary_zh"]
    assert row["missing_signals_zh"] == ["伤停", "首发"]


def test_optimizer_view_classifies_invalid_key_status():
    view = build_optimizer_view(
        {
            "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
            "ai_combo_research": {
                "ds_attempted": True,
                "ds_completed": False,
                "ds_error_code": "invalid_api_key",
                "fallback_reason": "DeepSeek Key 无效，已改用本地摘要。",
            },
            "llm_status": {
                "status": "ready",
                "last_error_label_zh": "Key 无效",
                "runtime_notice_zh": "本轮 DS 已自动尝试，但未成功返回；当前原因：Key 无效。",
            },
        }
    )
    assert view["ai_research_status"]["status"] == "fallback"
    assert view["ai_research_status"]["label_zh"] == "Key 无效"
    assert "Key 无效" in view["ai_research_status"]["summary_zh"]


def test_optimizer_view_filters_technical_fallback_warning():
    view = build_optimizer_view(
        {
            "warnings": [
                "sporttery provider failed: <urlopen error>; fallback to mock（实时公开数据暂不可用，已平静切换；mock 只用于演示流程，不会伪装成 Sporttery。）"
            ],
            "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
        }
    )
    assert view["warnings"] == []

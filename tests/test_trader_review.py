from src.audit.trader_review import build_trader_review


def test_trader_review_has_final_call():
    preview = {"provider_used": "sporttery", "intelligence_completeness": {"score": 60}, "optimizer": {"selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []}, "candidate_rankings": {}}}
    result = build_trader_review(preview)
    assert result["final_call_zh"]
    assert result["conclusions_zh"]


def test_trader_review_reviews_daily_paper_combos_when_gate_closed():
    preview = {"provider_used": "sporttery", "intelligence_completeness": {"score": 42}}
    optimizer = {
        "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
        "best_parlay_summary": {
            "daily_2x1_candidate": {
                "status": "paper_candidate",
                "legs": "A vs B 主胜；C vs D 客胜",
                "selected_reason_zh": "用于 T+1 复盘和赛后学习，不是通过门控的强组合。",
            },
            "daily_3x1_candidate": {
                "status": "paper_candidate",
                "legs": "A vs B 主胜；C vs D 客胜；E vs F 平",
                "selected_reason_zh": "用于验证系统是否过度拒绝 3串1。",
            },
        },
    }
    result = build_trader_review(preview, optimizer)
    joined = "\n".join(result["conclusions_zh"])
    assert "每日2串1纸面候选已进入赛后复盘" in joined
    assert "每日3串1纸面候选已进入赛后复盘" in joined
    assert "验证系统是否过度拒绝组合" in result["post_match_review_policy_zh"]

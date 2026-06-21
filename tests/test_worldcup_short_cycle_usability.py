from src.optimizer.best_parlay import build_best_parlay_summary
from src.view_models.optimizer_view import build_optimizer_view


def test_worldcup_short_cycle_score_can_reach_95_with_real_slate_and_diverse_daily_lanes():
    view = build_optimizer_view(
        {
            "provider_used": "sporttery",
            "matches_analyzed": 8,
            "candidate_pool_count": 42,
            "credibility_gate": {
                "combo_gate": "closed",
                "label_zh": "不建议串联",
                "reason_zh": "长期证据仍需赛后样本验证。",
            },
            "credibility_audit": {
                "professional_model_score": {
                    "score": 49,
                    "ceiling_score": 72,
                }
            },
            "play_bias_diagnostics": {
                "issues": [{"label_zh": "候选池同质化"}],
            },
            "best_parlay_summary": {
                "daily_output_lanes": [
                    {"status": "paper_candidate", "label_zh": "每日单关"},
                    {"status": "paper_candidate", "label_zh": "每日2串1"},
                    {"status": "paper_candidate", "label_zh": "每日3串1"},
                ],
                "daily_2x1_candidate": {
                    "direction_family_zh": "主队方向 + 客队方向",
                    "play_type_zh": "让球胜平负 + 胜平负",
                },
                "daily_3x1_candidate": {
                    "direction_family_zh": "主队方向 + 客队方向 + 平局方向",
                    "play_type_zh": "让球胜平负 + 胜平负",
                },
            },
        }
    )

    brief = view["daily_candidate_brief"]
    assert brief["score"] == 95
    assert brief["score_zh"] == "95/95"
    assert brief["evidence_score_zh"] == "49/72"
    assert "短赛会实操分" in brief["score_explain_zh"]


def test_daily_parlay_substitutes_homogeneous_combo_with_diverse_paper_candidate():
    result = {
        "risk_profile": "aggressive",
        "risk_profile_label": "进取",
        "credibility_gate": {
            "combo_gate": "closed",
            "label_zh": "不建议串联",
            "reason_zh": "长期证据仍需赛后样本验证。",
        },
        "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
        "candidate_rankings": {
            "singles": [
                {
                    "type": "single",
                    "match": "荷兰 vs 瑞典｜让球胜平负·主胜",
                    "odds": 2.75,
                    "model_prob": 0.43,
                    "market_prob": 0.32,
                    "ev": 0.18,
                    "edge": 0.11,
                    "confidence_score": 0.55,
                    "risk_adjusted_score": 0.72,
                    "risk_level": "medium",
                    "play_type_zh": "让球胜平负",
                    "direction_family_zh": "主队方向",
                },
                {
                    "type": "single",
                    "match": "新西兰 vs 埃及｜胜平负·客胜",
                    "odds": 2.40,
                    "model_prob": 0.41,
                    "market_prob": 0.35,
                    "ev": 0.09,
                    "edge": 0.06,
                    "confidence_score": 0.50,
                    "risk_adjusted_score": 0.64,
                    "risk_level": "medium",
                    "play_type_zh": "胜平负",
                    "direction_family_zh": "客队方向",
                },
                {
                    "type": "single",
                    "match": "突尼斯 vs 日本｜让球胜平负·平",
                    "odds": 3.20,
                    "model_prob": 0.33,
                    "market_prob": 0.28,
                    "ev": 0.06,
                    "edge": 0.05,
                    "confidence_score": 0.48,
                    "risk_adjusted_score": 0.58,
                    "risk_level": "medium",
                    "play_type_zh": "让球胜平负",
                    "direction_family_zh": "平局方向",
                },
            ],
            "parlay_2x1": [
                {
                    "type": "parlay_2x1",
                    "legs": "荷兰 vs 瑞典｜让球胜平负·主胜；乌拉圭 vs 佛得角｜让球胜平负·主胜",
                    "odds": 5.80,
                    "model_prob": 0.18,
                    "market_prob": 0.16,
                    "ev": 0.04,
                    "edge": 0.02,
                    "confidence_score": 0.45,
                    "risk_adjusted_score": 0.95,
                    "risk_level": "medium",
                    "play_type_zh": "让球胜平负",
                    "direction_family_zh": "主队方向",
                }
            ],
            "parlay_3x1": [],
        },
        "no_combo_reason": "组合候选同质化，先做纸面复盘。",
    }

    summary = build_best_parlay_summary(result)
    daily_2x1 = summary["daily_2x1_candidate"]

    assert "新西兰 vs 埃及" in daily_2x1["legs"]
    assert "主队方向" in daily_2x1["direction_family_zh"]
    assert "客队方向" in daily_2x1["direction_family_zh"]
    assert "分散纸面组合" in daily_2x1["selected_reason_zh"]

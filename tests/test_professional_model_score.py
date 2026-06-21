from src.audit.credibility import audit_credibility
from src.audit.pro_model_score import build_professional_model_score
from src.api.routes import dispatch_route
from src.cli.professional_model_score import build_professional_score_payload
from src.view_models.optimizer_view import build_optimizer_view


def _preview(stage="t_plus_1", provider="sporttery"):
    return {
        "provider_used": provider,
        "prematch_workflow": {"stage": stage, "stage_label_zh": "T+1 明日预观察"},
        "intelligence_completeness": {"score": 50, "main_gaps_zh": ["伤停", "首发"]},
        "contexts": [{"top_scores": [{"score": "1-0"}], "hhad_probs": {"home": 0.5}}],
        "source_coverage": {
            "match_coverage": [
                {
                    "injuries": {"status": "checked_empty"},
                    "lineup": {"status": "not_connected"},
                    "weather": {"status": "fallback_estimated"},
                    "news": {"status": "checked_empty"},
                }
            ]
        },
    }


def _optimizer():
    return {
        "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
        "candidate_rankings": {
            "parlay_2x1": [
                {
                    "type": "parlay_2x1",
                    "legs": "A vs B｜胜平负·主胜；C vs D｜让球胜平负·主胜",
                    "odds": 4.2,
                    "model_prob": 0.28,
                    "market_prob": 0.22,
                    "ev": 0.12,
                    "edge": 0.06,
                    "risk_level": "medium",
                    "play_diversity": {"hard_block": False},
                    "combo_homogeneity": {"hard_block": False, "penalty": 0.0},
                    "combo_homogeneity_reason_zh": "组合玩法、方向、赔率段和解释因子相对分散。",
                    "play_type_mix_zh": "胜平负 + 让球胜平负",
                    "play_diversity_reason_zh": "玩法分散：胜平负 + 让球胜平负，组合结构更均衡。",
                }
            ]
        },
        "clv_tracking": {"tracked_count": 0},
    }


def test_professional_score_reports_ceiling_and_missing_to_95():
    score = build_professional_model_score(_preview(), _optimizer(), {})
    assert score["score"] <= score["ceiling_score"]
    assert score["ceiling_score"] < 95
    assert score["missing_to_95"]
    assert score["roadmap_to_95"]["items"]
    assert score["roadmap_to_95"]["next_best_actions"][0]["estimated_score_gain"] >= 0
    assert "priority_zh" in score["roadmap_to_95"]["next_best_actions"][0]
    assert round(sum(item["weight"] for item in score["components"]), 6) == 1.0
    assert any(item["key"] == "clv_market_test" for item in score["components"])
    assert any(item["key"] == "favorite_longshot_bias_control" for item in score["components"])
    assert any(item["key"] == "play_bias_control" for item in score["components"])
    assert any(item["key"] == "odds_conversion_quality" for item in score["components"])
    assert score["evidence_requirements"]["rows"]
    assert score["evidence_requirements"]["next_gate"]["level"] in {60, 75, 85, 95}
    assert score["score_trend"]["status"] in {"ok", "empty"}
    assert score["ai_research_quality"]["score"] >= 0
    progress = score["evidence_requirements"]["sample_progress"]
    assert "settled_missing" in progress
    assert "clv_missing" in progress
    assert progress["next_action_zh"]
    assert score["evidence_requirements"]["gate_checklist"]
    assert any(item["level"] == 95 for item in score["evidence_requirements"]["gate_checklist"])
    assert "market_benchmark" in score["learning_evidence"]
    assert any(item["key"] == "closing_line_tested" for item in score["industry_benchmark_zh"])
    assert any(item["key"] == "odds_conversion_checked" for item in score["industry_benchmark_zh"])
    assert any(item["key"] == "play_bias_controlled" for item in score["industry_benchmark_zh"])
    assert score["score_gap_radar"]
    assert {"key", "score", "target_score", "gap_to_target", "weighted_gap", "impact_zh", "next_step_zh"} <= set(score["score_gap_radar"][0])
    weighted = [item["weighted_gap"] for item in score["score_gap_radar"]]
    assert weighted == sorted(weighted, reverse=True)
    portfolio_component = next(item for item in score["components"] if item["key"] == "portfolio_discipline")
    assert "同质化" in portfolio_component["detail_zh"]


def test_professional_score_caps_when_source_falls_back_to_mock():
    preview = {
        **_preview(provider="mock"),
        "matches_count": 2,
        "fallback_used": True,
        "attempts": [
            {"date": "2026-06-10", "matches_count": 0, "provider_used": "mock", "status": "fallback"},
            {"date": "2026-06-11", "matches_count": 2, "provider_used": "mock", "status": "fallback"},
        ],
        "scan_window": {"start_date": "2026-06-10", "end_date": "2026-06-13", "days_checked": 4, "complete": True},
    }
    score = build_professional_model_score(preview, _optimizer(), {})
    market = next(item for item in score["components"] if item["key"] == "market_baseline")
    assert score["ceiling_score"] <= 64
    assert market["score"] <= 45
    assert "mock" in market["detail_zh"]


def test_professional_score_penalizes_degraded_source_window():
    preview = {
        **_preview(provider="sporttery"),
        "matches_count": 2,
        "attempts": [
            {"date": "2026-06-10", "matches_count": 2, "provider_used": "sporttery", "status": "available"},
            {"date": "2026-06-11", "matches_count": 0, "provider_used": "mock", "status": "fallback"},
        ],
        "scan_window": {"start_date": "2026-06-10", "end_date": "2026-06-13", "days_checked": 4, "complete": True},
    }
    score = build_professional_model_score(preview, _optimizer(), {})
    market = next(item for item in score["components"] if item["key"] == "market_baseline")
    assert score["ceiling_score"] <= 90
    assert market["score"] < 90
    assert "mock/fallback" in market["detail_zh"]


def test_credibility_includes_professional_model_score():
    credibility = audit_credibility(_preview(), _optimizer())
    assert credibility["professional_model_score"]["score"] > 0
    assert "市场" in " ".join(credibility["professional_model_score"]["principles_zh"])


def test_optimizer_view_exposes_professional_score_and_play_diversity():
    credibility = audit_credibility(_preview(), _optimizer())
    result = {
        **_optimizer(),
        "credibility_audit": credibility,
        "credibility_gate": credibility["credibility_gate"],
        "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
    }
    view = build_optimizer_view(result)
    assert any(card["label"] == "职业模型分" for card in view["summary_cards"])
    row = view["candidate_rankings"]["parlay_2x1"][0]
    assert row["play_type_mix_zh"] == "胜平负 + 让球胜平负"


def test_optimizer_view_exposes_combo_homogeneity_reason():
    optimizer = _optimizer()
    optimizer["candidate_rankings"]["parlay_2x1"][0]["combo_homogeneity"] = {
        "level": "crowded",
        "penalty": 0.08,
        "hard_block": False,
    }
    optimizer["candidate_rankings"]["parlay_2x1"][0]["combo_homogeneity_reason_zh"] = "组合存在隐性同质化：同赔率段 2.00-3.00×2。"
    view = build_optimizer_view(optimizer)
    row = view["candidate_rankings"]["parlay_2x1"][0]
    assert "隐性同质化" in row["combo_homogeneity_reason_zh"]
    assert "同质化审计" in row["discipline_summary_zh"]


def test_optimizer_view_exposes_market_probability_audit():
    optimizer = _optimizer()
    optimizer["candidate_rankings"]["singles"] = [
        {
            "type": "single",
            "match": "A vs B",
            "odds": 8.8,
            "model_prob": 0.14,
            "market_prob": 0.10,
            "ev": 0.232,
            "edge": 0.04,
            "market_probability_audit": {
                "label_zh": "市场转换可用",
                "max_method_shift": 0.041,
                "message_zh": "已进行三方法去水交叉检查。",
            },
            "market_bias_audit": {
                "label_zh": "存在冷门偏差风险",
                "outcome_bias_bucket": "longshot",
                "outcome_method_shift": 0.041,
                "outcome_message_zh": "该方向属于低概率方向。",
            },
        }
    ]
    view = build_optimizer_view(optimizer)
    row = view["candidate_rankings"]["singles"][0]
    assert "市场转换" in row["market_audit_zh"]
    assert row["market_bias_zh"] == "冷门偏差风险"
    assert row["market_method_shift_zh"] == "4.1%"


def test_optimizer_view_exposes_play_bias_diagnostics():
    optimizer = {
        **_optimizer(),
        "play_bias_diagnostics": {
            "status": "biased",
            "label_zh": "存在玩法偏置",
            "summary_zh": "2串1候选集中在让球胜平负。",
            "sections": [{"label_zh": "2串1候选", "top_play_type": "让球胜平负", "top_play_share": 1.0, "message_zh": "高度集中。"}],
        },
    }
    view = build_optimizer_view(optimizer)
    assert view["play_bias_diagnostics"]["status"] == "biased"
    assert any(card["label"] == "玩法偏置" for card in view["summary_cards"])
    assert any("让球胜平负" in line for line in view["explanations"])


def test_optimizer_view_exposes_play_concentration_reason():
    optimizer = _optimizer()
    optimizer["candidate_rankings"]["singles"] = [
        {
            "type": "single",
            "match": "A vs B",
            "odds": 2.2,
            "model_prob": 0.58,
            "market_prob": 0.48,
            "ev": 0.20,
            "edge": 0.10,
            "play_concentration_reason_zh": "让球胜平负 同类候选已出现 3 次，排序已小幅降权。",
        }
    ]
    view = build_optimizer_view(optimizer)
    row = view["candidate_rankings"]["singles"][0]
    assert "排序已小幅降权" in row["play_concentration_reason_zh"]
    assert "玩法拥挤" in row["discipline_summary_zh"]


def test_optimizer_view_exposes_play_type_learning_reason():
    optimizer = _optimizer()
    optimizer["candidate_rankings"]["singles"] = [
        {
            "type": "single",
            "match": "A vs B",
            "odds": 2.2,
            "model_prob": 0.58,
            "market_prob": 0.48,
            "ev": 0.20,
            "edge": 0.10,
            "play_type_learning_reason_zh": "让球胜平负 历史纸面 ROI -18.0%，先降权观察。",
            "play_type_learning": {"status": "penalized", "penalty": 0.08},
        }
    ]
    view = build_optimizer_view(optimizer)
    row = view["candidate_rankings"]["singles"][0]
    assert "历史纸面 ROI" in row["play_type_learning_reason_zh"]
    assert "玩法复盘" in row["discipline_summary_zh"]


def test_optimizer_view_exposes_model_disagreement_reason():
    optimizer = _optimizer()
    optimizer["candidate_rankings"]["singles"] = [
        {
            "type": "single",
            "match": "A vs B",
            "odds": 2.45,
            "model_prob": 0.66,
            "market_prob": 0.42,
            "ev": 0.42,
            "edge": 0.24,
            "model_market_gap": 0.24,
            "model_disagreement_penalty": 0.12,
            "model_disagreement_reason_zh": "模型与市场概率相差 24.0%，高分歧；不能把高 EV 直接升级为强观察。",
        }
    ]
    view = build_optimizer_view(optimizer)
    row = view["candidate_rankings"]["singles"][0]
    assert "高分歧" in row["model_disagreement_reason_zh"]
    assert "模型分歧" in row["discipline_summary_zh"]


def test_optimizer_view_exposes_strategy_adjustment_reason():
    optimizer = _optimizer()
    optimizer["candidate_rankings"]["singles"] = [
        {
            "type": "single",
            "match": "A vs B",
            "odds": 2.20,
            "model_prob": 0.58,
            "market_prob": 0.48,
            "ev": 0.20,
            "edge": 0.10,
            "strategy_adjustment_reason_zh": "赛后学习调参：降低让球胜平负权重：历史 ROI 偏弱。",
            "strategy_adjustment_penalty": 0.08,
        }
    ]
    optimizer["strategy_adjustment_status"] = {
        "status": "loaded",
        "adjustment_count": 1,
        "reason_zh": "已读取赛后调参建议。",
    }
    view = build_optimizer_view(optimizer)
    row = view["candidate_rankings"]["singles"][0]
    assert "赛后学习调参" in row["strategy_adjustment_reason_zh"]
    assert "学习调参" in row["discipline_summary_zh"]
    card = next(item for item in view["summary_cards"] if item["label"] == "学习调参")
    assert card["value"] == "已接入 1 条"


def test_optimizer_view_exposes_play_type_learning_status_card():
    optimizer = {
        **_optimizer(),
        "play_type_learning_status": {
            "status": "loaded",
            "reason_zh": "已读取赛后玩法复盘。",
            "play_type_count": 3,
        },
    }
    view = build_optimizer_view(optimizer)
    card = next(item for item in view["summary_cards"] if item["label"] == "玩法复盘")
    assert card["value"] == "已读取 3 类"
    assert "赛后玩法复盘" in card["help"]


def test_professional_score_uses_learning_and_clv_evidence():
    optimizer = {
        **_optimizer(),
        "learning_history": {
            "settled_count": 36,
            "hit_rate": 0.52,
            "brier_score": 0.21,
            "log_loss": 0.63,
            "probability_quality": {"sample_count": 36, "message_zh": "已有稳定小样本。"},
        },
        "clv_history": {
            "settled_count": 24,
            "average_clv_pct": 0.012,
            "summary_zh": "平均 CLV 偏正。",
        },
    }
    score = build_professional_model_score(_preview(provider="sporttery"), optimizer, {})
    evidence = score["learning_evidence"]
    assert evidence["settled_count"] == 36
    assert evidence["clv_settled_count"] == 24
    assert score["roadmap_to_95"]["evidence_snapshot"]["clv_settled_count"] == 24
    assert any(item["key"] == "clv_market_test" and item["score"] >= 70 for item in score["components"])


def test_professional_score_exposes_play_type_learning_evidence():
    optimizer = {
        **_optimizer(),
        "learning_history": {
            "settled_count": 42,
            "hit_rate": 0.48,
            "brier_score": 0.23,
            "log_loss": 0.66,
            "probability_quality": {"sample_count": 42, "message_zh": "已有玩法复盘样本。"},
            "play_type_rows": [
                {
                    "play_type": "hhad",
                    "label_zh": "让球胜平负",
                    "attempts": 18,
                    "hits": 4,
                    "hit_rate": 0.222222,
                    "paper_roi": -0.18,
                    "brier_score": 0.31,
                },
                {
                    "play_type": "had",
                    "label_zh": "胜平负",
                    "attempts": 14,
                    "hits": 8,
                    "hit_rate": 0.571429,
                    "paper_roi": 0.08,
                    "brier_score": 0.21,
                },
            ],
        },
        "clv_history": {"settled_count": 8, "average_clv_pct": 0.002},
    }

    score = build_professional_model_score(_preview(provider="sporttery"), optimizer, {})
    evidence = score["learning_evidence"]

    assert evidence["play_type_sample_count"] == 2
    assert evidence["play_type_weak_count"] == 1
    assert evidence["play_type_best"]["label_zh"] == "胜平负"
    assert evidence["play_type_weakest"]["label_zh"] == "让球胜平负"
    assert "玩法" in evidence["play_type_summary_zh"]
    assert any(item["key"] == "play_type_learning" for item in score["roadmap_to_95"]["items"])


def test_professional_score_penalizes_play_bias_diagnostics():
    optimizer = {
        **_optimizer(),
        "play_bias_diagnostics": {
            "status": "biased",
            "label_zh": "存在玩法偏置",
            "summary_zh": "单关候选高度集中在让球胜平负。",
            "sections": [
                {
                    "label_zh": "单关候选",
                    "status": "very_concentrated",
                    "top_play_type": "让球胜平负",
                    "top_play_share": 0.92,
                    "message_zh": "单关候选高度集中在让球胜平负。",
                }
            ],
            "issues": [{"label_zh": "单关候选", "status": "very_concentrated"}],
            "next_step_zh": "提高同玩法惩罚。",
        },
    }

    score = build_professional_model_score(_preview(provider="sporttery"), optimizer, {})
    component = next(item for item in score["components"] if item["key"] == "play_bias_control")

    assert component["score"] <= 52
    assert "让球胜平负" in component["detail_zh"]
    assert any(item["key"] == "play_bias_control" for item in score["score_gap_radar"])
    assert any(item["key"] == "play_bias_control" for item in score["roadmap_to_95"]["items"])


def test_professional_score_counts_ai_verifiable_hypotheses():
    optimizer = {
        **_optimizer(),
        "ai_combo_research": {
            "ds_completed": True,
            "token_total": 780,
            "structured_notes": {"single_notes": [{"target": "A", "note_zh": "赔率有价值"}]},
            "verifiable_hypotheses": [
                {
                    "label_zh": "单关假设",
                    "target": "A vs B",
                    "hypothesis_zh": "市场低估主胜。",
                    "validation_rule_zh": "赛后看命中与 CLV。",
                }
            ],
        },
        "research_archive": {"latest_path": "data/research_archive/latest.json"},
    }
    score = build_professional_model_score(_preview(provider="sporttery"), optimizer, {})
    ai = score["ai_research_quality"]
    assert ai["verifiable_hypothesis_count"] == 1
    assert ai["score"] >= 50


def test_professional_score_uses_ai_hypothesis_review_history():
    optimizer = {
        **_optimizer(),
        "ai_combo_research": {
            "ds_completed": True,
            "token_total": 1200,
            "structured_notes": {
                "single_notes": [{"target": "A", "note_zh": "赔率有价值"}],
                "combo_notes": [{"target": "B", "note_zh": "组合只作纸面观察"}],
                "rejected_combo_notes": [{"target": "C", "note_zh": "拒绝原因需要复盘"}],
            },
            "verifiable_hypotheses": [{"target": "A", "hypothesis_zh": "市场低估。"}],
        },
        "research_archive": {"latest_path": "data/research_archive/latest.json"},
        "ai_hypothesis_review_history": {
            "reviewed_count": 12,
            "supported_count": 8,
            "failed_count": 2,
            "supported_rate": 0.666667,
            "factor_rows": [
                {"ai_factor": "market_value", "ai_factor_zh": "赔率价值", "reviewed": 8, "supported_rate": 0.75, "failed_rate": 0.125},
                {"ai_factor": "combo_risk", "ai_factor_zh": "组合风险", "reviewed": 6, "supported_rate": 0.5, "failed_rate": 0.5},
            ],
            "summary_zh": "累计复盘 12 条 AI 假设，支持率 66.7%。",
        },
    }
    score = build_professional_model_score(_preview(provider="sporttery"), optimizer, {})
    ai = score["ai_research_quality"]
    evidence = score["learning_evidence"]
    assert ai["reviewed_hypothesis_count"] == 12
    assert ai["supported_hypothesis_rate"] == 0.666667
    assert evidence["ai_hypothesis_reviewed_count"] == 12
    assert evidence["ai_factor_rows"]
    assert "AI 因子复盘" in evidence["ai_factor_summary_zh"]
    assert ai["supported_factor_count"] >= 1
    assert "AI 假设" in ai["summary_zh"]


def test_professional_score_api_shape():
    payload = dispatch_route("/api/audit/professional-model-score", {"provider": "mock", "date": "2026-06-10"})
    data = payload["data"]
    assert data["title"] == "职业模型评分审计"
    assert data["professional_model_score"]["score"] <= data["professional_model_score"]["ceiling_score"]
    assert data["missing_to_95"]
    assert data["next_best_actions"]


def test_professional_score_cli_payload_shape():
    payload = build_professional_score_payload("mock", "2026-06-10", 10000.0, "aggressive", None)
    assert payload["title"] == "职业模型评分审计"
    assert payload["score"] <= payload["ceiling_score"]
    assert payload["evidence_requirements"]["rows"]
    assert "score_trend" in payload
    assert "ai_research_quality" in payload
    assert payload["roadmap_to_95"]["next_best_actions"]


def test_professional_score_reports_market_skill_against_market_probability():
    optimizer = _optimizer()
    optimizer["learning_history"] = {
        "settled_count": 4,
        "rows": [
            {"model_prob": 0.70, "market_prob": 0.55, "hit": True},
            {"model_prob": 0.65, "market_prob": 0.52, "hit": True},
            {"model_prob": 0.28, "market_prob": 0.44, "hit": False},
            {"model_prob": 0.35, "market_prob": 0.48, "hit": False},
        ],
    }

    score = build_professional_model_score(_preview(), optimizer, {})

    benchmark = score["learning_evidence"]["market_benchmark"]
    assert benchmark["sample_count"] == 4
    assert benchmark["brier_skill_score"] > 0
    assert "模型相对市场" in benchmark["summary_zh"]
    level_85 = next(row for row in score["evidence_requirements"]["rows"] if row["level"] == 85)
    assert any(item["key"] == "market_skill_score" for item in level_85["checks"])

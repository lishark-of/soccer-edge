from src.optimizer.portfolio_optimizer import optimize_portfolio


def _candidate(match_id, home, away, outcome, odds, model_prob, market_prob, ev, edge, confidence=0.62):
    return {
        "candidate_type": "single",
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "play_type": "had",
        "outcome_key": outcome,
        "outcome_label": outcome,
        "odds": odds,
        "model_prob": model_prob,
        "market_prob": market_prob,
        "ev": ev,
        "edge": edge,
        "risk_level": "medium",
        "observation_confidence": confidence,
    }


def test_aggressive_profile_exposes_hit_rate_discipline_limits():
    result = optimize_portfolio(
        [
            _candidate("m1", "A", "B", "主胜", 2.2, 0.58, 0.48, 0.27, 0.10),
            _candidate("m2", "C", "D", "客胜", 2.1, 0.55, 0.47, 0.15, 0.08),
        ],
        bankroll=10000,
        config={"risk_profile": "aggressive"},
    )
    limits = result["risk_summary"]["profile_limits"]
    assert limits["min_parlay_2x1_prob"] == 0.20
    assert limits["min_parlay_3x1_prob"] == 0.12
    assert limits["min_leg_confidence"] == 0.50
    assert "串联命中率纪律" in " ".join(result["explanations"])


def test_low_combo_probability_is_rejected_with_reason():
    result = optimize_portfolio(
        [
            _candidate("m1", "A", "B", "主胜", 3.2, 0.32, 0.25, 0.05, 0.07),
            _candidate("m2", "C", "D", "客胜", 2.9, 0.36, 0.29, 0.04, 0.07),
        ],
        bankroll=10000,
        config={"risk_profile": "aggressive"},
    )
    reasons = " ".join(row.get("reject_reason", "") for row in result["candidate_rankings"]["parlay_2x1"])
    assert "组合命中概率低于纪律门槛" in reasons


def test_longshot_single_is_not_parlay_core():
    result = optimize_portfolio(
        [
            _candidate("m1", "A", "B", "客胜", 8.0, 0.18, 0.10, 0.44, 0.08),
            _candidate("m2", "C", "D", "主胜", 2.0, 0.58, 0.50, 0.16, 0.08),
        ],
        bankroll=10000,
        config={"risk_profile": "aggressive"},
    )
    longshot_single = next(row for row in result["candidate_rankings"]["singles"] if row["odds"] >= 6)
    assert longshot_single["longshot_warning"]
    assert longshot_single["parlay_eligible"] is False
    reasons = " ".join(row.get("reject_reason", "") for row in result["candidate_rankings"]["parlay_2x1"])
    assert "高赔率冷门腿不适合作为串联核心" in reasons


def test_same_play_type_2x1_is_blocked_for_diversity():
    first = _candidate("m1", "A", "B", "主胜", 2.2, 0.62, 0.48, 0.36, 0.14, confidence=0.78)
    second = _candidate("m2", "C", "D", "客胜", 2.15, 0.60, 0.47, 0.29, 0.13, confidence=0.78)
    first["play_type"] = "hhad"
    second["play_type"] = "hhad"

    result = optimize_portfolio([first, second], bankroll=10000, config={"risk_profile": "aggressive"})

    rows = result["candidate_rankings"]["parlay_2x1"]
    assert rows
    assert not result["selected_portfolio"]["parlay_2x1"]
    assert "玩法过于集中" in rows[0]["reject_reason"]
    assert rows[0]["play_diversity"]["hard_block"] is True
    assert rows[0]["combo_homogeneity"]["hard_block"] is True


def test_mixed_play_type_2x1_can_pass_diversity_gate():
    first = _candidate("m1", "A", "B", "主胜", 2.2, 0.62, 0.48, 0.36, 0.14, confidence=0.78)
    second = _candidate("m2", "C", "D", "让胜", 2.15, 0.60, 0.47, 0.29, 0.13, confidence=0.78)
    first["play_type"] = "had"
    second["play_type"] = "hhad"

    result = optimize_portfolio([first, second], bankroll=10000, config={"risk_profile": "aggressive"})

    rows = result["candidate_rankings"]["parlay_2x1"]
    assert rows
    assert rows[0]["play_diversity"]["hard_block"] is False
    assert "玩法分散" in rows[0]["play_diversity_reason_zh"]


def test_single_play_concentration_is_penalized_but_not_removed():
    candidates = []
    for idx in range(4):
        item = _candidate(f"m{idx}", f"H{idx}", f"A{idx}", "让胜", 2.1 + idx * 0.02, 0.61, 0.47, 0.28, 0.14, confidence=0.78)
        item["play_type"] = "hhad"
        candidates.append(item)

    result = optimize_portfolio(candidates, bankroll=10000, config={"risk_profile": "aggressive"})

    rows = result["candidate_rankings"]["singles"]
    assert len(rows) >= 4
    assert any(row.get("play_concentration", {}).get("penalty", 0) > 0 for row in rows)
    assert any("排序已小幅降权" in row.get("play_concentration_reason_zh", "") for row in rows)


def test_play_type_learning_penalizes_weak_historical_play_type():
    hhad = _candidate("m1", "A", "B", "让胜", 2.25, 0.62, 0.48, 0.35, 0.14, confidence=0.78)
    hhad["play_type"] = "hhad"
    had = _candidate("m2", "C", "D", "主胜", 2.20, 0.61, 0.48, 0.34, 0.13, confidence=0.78)
    had["play_type"] = "had"

    result = optimize_portfolio(
        [hhad, had],
        bankroll=10000,
        config={
            "risk_profile": "aggressive",
            "play_type_learning_rows": [
                {
                    "play_type": "hhad",
                    "label_zh": "让球胜平负",
                    "attempts": 18,
                    "hits": 4,
                    "hit_rate": 0.222222,
                    "paper_roi": -0.18,
                    "brier_score": 0.31,
                    "model_action_zh": "让球胜平负 先降权观察。",
                }
            ],
        },
    )

    hhad_row = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("A vs B"))
    assert hhad_row["play_type_learning"]["status"] == "penalized"
    assert hhad_row["play_type_learning"]["penalty"] > 0
    assert "历史纸面 ROI" in hhad_row["play_type_learning_reason_zh"]


def test_model_market_disagreement_is_penalized_and_explained():
    wide_gap = _candidate("m1", "A", "B", "让胜", 2.45, 0.66, 0.42, 0.42, 0.24, confidence=0.80)
    wide_gap["play_type"] = "hhad"
    aligned = _candidate("m2", "C", "D", "主胜", 2.20, 0.58, 0.52, 0.28, 0.06, confidence=0.80)
    aligned["play_type"] = "had"

    result = optimize_portfolio([wide_gap, aligned], bankroll=10000, config={"risk_profile": "aggressive"})

    wide_row = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("A vs B"))
    assert wide_row["model_disagreement_penalty"] >= 0.08
    assert "模型与市场概率相差" in wide_row["model_disagreement_reason_zh"]
    reasons = " ".join(row.get("reject_reason", "") for row in result["candidate_rankings"]["parlay_2x1"])
    assert "模型与市场分歧较大" in reasons


def test_strategy_adjustments_penalize_weak_play_type_and_parlay_leg():
    hhad = _candidate("m1", "A", "B", "让胜", 2.25, 0.62, 0.48, 0.35, 0.14, confidence=0.78)
    hhad["play_type"] = "hhad"
    had = _candidate("m2", "C", "D", "主胜", 2.20, 0.61, 0.48, 0.34, 0.13, confidence=0.78)
    had["play_type"] = "had"

    result = optimize_portfolio(
        [hhad, had],
        bankroll=10000,
        config={
            "risk_profile": "aggressive",
            "strategy_adjustments": [
                {
                    "key": "play_type_hhad_downweight",
                    "label_zh": "降低让球胜平负权重",
                    "action": "downweight_play_type",
                    "priority": 86,
                    "confidence": 0.80,
                    "target": {"play_type": "hhad"},
                    "reason_zh": "让球胜平负历史 ROI 偏弱，不应继续机械刷屏。",
                    "expected_effect_zh": "降低该玩法排序分。",
                }
            ],
        },
    )

    hhad_row = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("A vs B"))
    assert hhad_row["strategy_adjustment_penalty"] > 0
    assert "赛后学习调参" in hhad_row["strategy_adjustment_reason_zh"]

    reasons = " ".join(row.get("reject_reason", "") for row in result["candidate_rankings"]["parlay_2x1"])
    assert "赛后学习调参" in reasons


def test_fragile_robust_value_leg_is_rejected_for_parlay():
    first = _candidate("m1", "A", "B", "主胜", 2.05, 0.56, 0.49, 0.148, 0.07, confidence=0.40)
    second = _candidate("m2", "C", "D", "让胜", 2.20, 0.62, 0.48, 0.36, 0.14, confidence=0.78)
    second["play_type"] = "hhad"

    result = optimize_portfolio(
        [first, second],
        bankroll=10000,
        config={
            "risk_profile": "aggressive",
            "learning_settled_count": 4,
            "learning_probability_quality": {"sample_count": 4},
            "learning_clv_summary": {"settled_count": 0},
        },
    )

    fragile = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("A vs B"))
    assert fragile["robust_value_status"] in {"fragile", "thin"}
    reasons = " ".join(row.get("reject_reason", "") for row in result["candidate_rankings"]["parlay_2x1"])
    assert "稳健价值不足" in reasons


def test_negative_clv_bucket_adjustment_penalizes_matching_odds_bucket():
    first = _candidate("m1", "A", "B", "主胜", 2.25, 0.62, 0.48, 0.35, 0.14, confidence=0.78)
    second = _candidate("m2", "C", "D", "客胜", 4.2, 0.36, 0.25, 0.20, 0.11, confidence=0.72)

    result = optimize_portfolio(
        [first, second],
        bankroll=10000,
        config={
            "risk_profile": "aggressive",
            "strategy_adjustments": [
                {
                    "key": "clv_bucket_2_00_3_00_downweight",
                    "label_zh": "降低均衡赔率CLV自信",
                    "action": "downweight_odds_bucket",
                    "priority": 87,
                    "confidence": 0.66,
                    "target": {"bucket": "2.00-3.00"},
                    "reason_zh": "均衡赔率平均 CLV 偏负，后续同赔率段不能只凭 EV 升级。",
                    "expected_effect_zh": "同赔率段候选轻量降权。",
                }
            ],
        },
    )

    adjusted = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("A vs B"))
    untouched = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("C vs D"))
    assert adjusted["strategy_adjustment_penalty"] > 0
    assert "均衡赔率" in adjusted["strategy_adjustment_reason_zh"]
    assert untouched["strategy_adjustment_penalty"] == 0


def test_competition_segment_adjustment_penalizes_matching_context():
    friendly = _candidate("m1", "A", "B", "主胜", 2.25, 0.62, 0.48, 0.35, 0.14, confidence=0.78)
    friendly["league"] = "International Friendly"
    league = _candidate("m2", "C", "D", "主胜", 2.20, 0.61, 0.48, 0.34, 0.13, confidence=0.78)
    league["league"] = "Premier League"

    result = optimize_portfolio(
        [friendly, league],
        bankroll=10000,
        config={
            "risk_profile": "aggressive",
            "strategy_adjustments": [
                {
                    "key": "competition_friendly_downweight",
                    "label_zh": "降低友谊赛语境自信",
                    "action": "downweight_competition_segment",
                    "priority": 85,
                    "confidence": 0.70,
                    "target": {"competition_segment": "friendly"},
                    "reason_zh": "友谊赛历史 ROI 偏弱，不能和常规联赛同权重。",
                    "expected_effect_zh": "同类赛事候选轻量降权。",
                }
            ],
        },
    )

    adjusted = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("A vs B"))
    untouched = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("C vs D"))
    assert adjusted["competition_segment"] == "friendly"
    assert adjusted["strategy_adjustment_penalty"] > 0
    assert "友谊赛" in adjusted["strategy_adjustment_reason_zh"]
    assert untouched["strategy_adjustment_penalty"] == 0


def test_ai_factor_adjustment_penalizes_matching_candidates():
    value_case = _candidate("m1", "A", "B", "主胜", 2.25, 0.62, 0.48, 0.35, 0.14, confidence=0.78)
    weather_case = _candidate("m2", "C", "D", "主胜", 2.20, 0.61, 0.48, 0.34, 0.13, confidence=0.78)
    weather_case["hypothesis_zh"] = "天气降雨和大风可能压低比赛节奏"

    result = optimize_portfolio(
        [value_case, weather_case],
        bankroll=10000,
        config={
            "risk_profile": "aggressive",
            "strategy_adjustments": [
                {
                    "key": "ai_factor_market_value_downweight",
                    "label_zh": "降低赔率价值因子自信",
                    "action": "downweight_ai_factor",
                    "priority": 84,
                    "confidence": 0.70,
                    "target": {"ai_factor": "market_value"},
                    "reason_zh": "AI 赛后复盘显示赔率价值类理由失败率偏高。",
                    "expected_effect_zh": "同类解释候选轻量降权。",
                }
            ],
        },
    )

    adjusted = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("A vs B"))
    untouched = next(row for row in result["candidate_rankings"]["singles"] if row["match"].startswith("C vs D"))
    assert adjusted["ai_factor"] == "market_value"
    assert adjusted["strategy_adjustment_penalty"] > 0
    assert "AI 赛后复盘" in adjusted["strategy_adjustment_reason_zh"]
    assert untouched["ai_factor"] == "weather"
    assert untouched["strategy_adjustment_penalty"] == 0


def test_combo_homogeneity_penalizes_same_odds_bucket_and_ai_factor():
    first = _candidate("m1", "A", "B", "主胜", 2.25, 0.62, 0.48, 0.35, 0.14, confidence=0.78)
    second = _candidate("m2", "C", "D", "让胜", 2.20, 0.61, 0.48, 0.34, 0.13, confidence=0.78)
    first["play_type"] = "had"
    second["play_type"] = "hhad"

    result = optimize_portfolio([first, second], bankroll=10000, config={"risk_profile": "aggressive"})

    rows = result["candidate_rankings"]["parlay_2x1"]
    assert rows
    row = rows[0]
    assert row["play_diversity"]["hard_block"] is False
    assert row["combo_homogeneity"]["penalty"] > 0
    assert "隐性同质化" in row["combo_homogeneity_reason_zh"]

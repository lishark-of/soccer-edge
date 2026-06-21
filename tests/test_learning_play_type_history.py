from src.learning.history import aggregate_play_type_rows, build_strategy_adjustments


def test_aggregate_play_type_rows_tracks_hhad_separately():
    rows = [
        {
            "play_type": "hhad",
            "hit": True,
            "paper_stake": 100,
            "settlement_profit": 90,
            "brier_score": 0.16,
            "log_loss": 0.42,
        },
        {
            "play_type": "hhad",
            "hit": False,
            "paper_stake": 100,
            "settlement_profit": -100,
            "brier_score": 0.26,
            "log_loss": 0.88,
        },
        {
            "play_type": "had",
            "hit": True,
            "paper_stake": 100,
            "settlement_profit": 75,
            "brier_score": 0.18,
            "log_loss": 0.50,
        },
    ]

    result = aggregate_play_type_rows(rows)
    by_type = {row["play_type"]: row for row in result}

    assert by_type["hhad"]["label_zh"] == "让球胜平负"
    assert by_type["hhad"]["attempts"] == 2
    assert by_type["hhad"]["hits"] == 1
    assert by_type["hhad"]["hit_rate"] == 0.5
    assert by_type["hhad"]["paper_roi"] == -0.05
    assert "样本" in by_type["hhad"]["model_action_zh"]


def test_aggregate_play_type_rows_warns_before_reweighting_small_samples():
    rows = [{"play_type": "total_goals", "hit": True, "paper_stake": 20, "settlement_profit": 18}]

    result = aggregate_play_type_rows(rows)

    assert result[0]["label_zh"] == "总进球"
    assert result[0]["sample_quality_zh"] == "样本很少"
    assert "暂不调权" in result[0]["model_action_zh"]


def test_strategy_adjustments_downweight_weak_play_type():
    adjustments = build_strategy_adjustments(
        play_type_rows=[
            {
                "play_type": "hhad",
                "label_zh": "让球胜平负",
                "attempts": 18,
                "paper_roi": -0.12,
                "brier_score": 0.31,
            }
        ],
        category_rows=[],
        bucket_rows=[],
        combo_discipline={"status": "empty"},
        probability_quality={"grade_zh": "样本不足"},
        clv_summary={"settled_count": 0},
        settled_count=18,
    )

    assert adjustments
    first = adjustments[0]
    assert first["action"] == "downweight_play_type"
    assert first["target"]["play_type"] == "hhad"
    assert "让球胜平负" in first["label_zh"]


def test_strategy_adjustments_use_negative_clv_by_play_type_and_bucket():
    adjustments = build_strategy_adjustments(
        play_type_rows=[],
        category_rows=[],
        bucket_rows=[],
        combo_discipline={},
        probability_quality={},
        clv_summary={
            "settled_count": 12,
            "average_clv_pct": -0.01,
            "play_type_rows": [
                {"play_type": "hhad", "label_zh": "让球胜平负", "attempts": 10, "average_clv_pct": -0.024}
            ],
            "bucket_rows": [
                {"bucket": "2_00_2_99", "signal_bucket": "2.00-3.00", "bucket_label_zh": "均衡赔率", "attempts": 9, "average_clv_pct": -0.022}
            ],
        },
        settled_count=40,
    )

    actions = {(row["action"], row["target"].get("play_type") or row["target"].get("bucket")) for row in adjustments}
    assert ("downweight_play_type", "hhad") in actions
    assert ("downweight_odds_bucket", "2.00-3.00") in actions
    assert any("CLV" in row["reason_zh"] for row in adjustments)


def test_strategy_adjustments_use_failed_ai_factor():
    adjustments = build_strategy_adjustments(
        play_type_rows=[],
        category_rows=[],
        bucket_rows=[],
        combo_discipline={},
        probability_quality={},
        clv_summary={"settled_count": 0},
        settled_count=24,
        ai_review_history={
            "factor_rows": [
                {
                    "ai_factor": "market_value",
                    "ai_factor_zh": "赔率价值",
                    "reviewed": 8,
                    "failed_rate": 0.50,
                    "supported_rate": 0.25,
                }
            ]
        },
    )

    ai_rows = [row for row in adjustments if row["action"] == "downweight_ai_factor"]
    assert ai_rows
    assert ai_rows[0]["target"]["ai_factor"] == "market_value"
    assert "AI因子" in ai_rows[0]["reason_zh"]

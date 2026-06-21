from src.learning.competition_segments import classify_competition_segment
from src.learning.history import aggregate_competition_segment_rows, build_strategy_adjustments


def test_classify_competition_segment_detects_national_team():
    result = classify_competition_segment({"league": "World Cup Qualifiers", "home_team": "Portugal", "away_team": "England"})

    assert result["competition_segment"] == "national_team"
    assert "国家队" in result["competition_segment_zh"]


def test_aggregate_competition_segment_rows_tracks_roi_and_brier():
    rows = [
        {"competition_segment": "friendly", "competition_segment_zh": "友谊赛", "hit": False, "paper_stake": 100, "settlement_profit": -100, "brier_score": 0.36},
        {"competition_segment": "friendly", "competition_segment_zh": "友谊赛", "hit": False, "paper_stake": 100, "settlement_profit": -100, "brier_score": 0.30},
    ]

    result = aggregate_competition_segment_rows(rows)

    assert result[0]["competition_segment"] == "friendly"
    assert result[0]["paper_roi"] == -1.0
    assert result[0]["brier_score"] == 0.33


def test_strategy_adjustments_downweight_weak_competition_segment():
    adjustments = build_strategy_adjustments(
        play_type_rows=[],
        competition_rows=[
            {
                "competition_segment": "friendly",
                "label_zh": "友谊赛",
                "attempts": 12,
                "paper_roi": -0.16,
                "brier_score": 0.33,
            }
        ],
        category_rows=[],
        bucket_rows=[],
        combo_discipline={},
        probability_quality={},
        clv_summary={"settled_count": 0},
        settled_count=40,
    )

    first = adjustments[0]
    assert first["action"] == "downweight_competition_segment"
    assert first["target"]["competition_segment"] == "friendly"
    assert "友谊赛" in first["reason_zh"]

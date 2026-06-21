from pathlib import Path

from src.learning.daily_snapshots import auto_review_yesterday, build_daily_decision_board, save_daily_snapshot
from src.learning.result_feedback import evaluate_observation_hit


def _preview():
    return {
        "selected_date": "2026-06-21",
        "provider_used": "sporttery",
        "matches_count": 2,
        "optimizer": {
            "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
            "best_parlay_summary": {
                "daily_single_candidate": {"status": "paper_candidate", "match": "A vs B｜胜平负·主胜", "play_type": "had", "direction": "主胜", "odds": 2.1},
                "daily_2x1_candidate": {"status": "paper_candidate", "legs": "A vs B｜胜平负·主胜；C vs D｜胜平负·客胜", "odds": 3.2},
                "daily_3x1_candidate": {"status": "paper_candidate", "legs": "A vs B；C vs D；E vs F", "odds": 6.0},
            },
            "candidate_rankings": {"parlay_2x1": [], "parlay_3x1": []},
        },
    }


def test_save_daily_snapshot_keeps_daily_paper_candidates(tmp_path):
    result = save_daily_snapshot(_preview(), snapshot_root=tmp_path, prepare_learning=False)
    assert result["status"] == "saved"
    assert "每日纸面2串1" in result["summary_zh"]
    assert Path(result["pre_match_path"]).exists()
    board = build_daily_decision_board("2026-06-21")
    assert board["status"] in {"available", "missing"}


def test_unknown_handicap_result_stays_unsettled():
    hit = evaluate_observation_hit(
        {"play_type": "hhad", "direction": "主胜"},
        {"actual_handicap_outcome_zh": "未知"},
    )
    assert hit is None

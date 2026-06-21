from pathlib import Path

from src.learning.ai_hypothesis_review import build_ai_hypothesis_review, build_ai_hypothesis_review_history, save_ai_hypothesis_review


def _archive():
    return {
        "selected_date": "2026-06-19",
        "ai_research": {
            "verifiable_hypotheses": [
                {
                    "id": "single_notes_1",
                    "category": "daily_single_candidate",
                    "target": "土耳其 vs 巴拉圭 主胜",
                    "hypothesis_zh": "市场可能低估土耳其主胜。",
                    "status": "pending_result",
                },
                {
                    "id": "rejected_combo_notes_1",
                    "category": "rejected_combo_review",
                    "target": "美国 vs 澳大利亚 主胜；瑞士 vs 波黑 主胜",
                    "hypothesis_zh": "该组合相关性和风险过高，应继续拒绝。",
                    "status": "pending_result",
                },
            ]
        },
    }


def _feedback():
    return {
        "date": "2026-06-19",
        "report": {
            "rows": [
                {
                    "match": "土耳其 vs 巴拉圭",
                    "play_type": "胜平负",
                    "direction": "主胜",
                    "learning_track": "daily_single_candidate",
                    "hit": True,
                }
            ]
        },
        "rejected_combo_reviews": [
            {
                "match": "美国 vs 澳大利亚 主胜；瑞士 vs 波黑 主胜",
                "combo_hit": False,
                "combo_miss": True,
                "leg_reviews": [],
            }
        ],
    }


def test_ai_hypothesis_review_scores_supported_rows():
    review = build_ai_hypothesis_review(_feedback(), archive=_archive())
    assert review["status"] == "reviewed"
    assert review["summary_counts"]["total"] == 2
    assert review["summary_counts"]["supported"] == 2
    assert review["hypotheses"][0]["review_status"] == "supported"
    assert review["hypotheses"][1]["review_status"] == "supported"
    assert review["hypotheses"][0]["ai_factor"] == "market_value"
    assert review["factor_rows"]


def test_ai_hypothesis_review_marks_failed_single():
    feedback = _feedback()
    feedback["report"]["rows"][0]["hit"] = False
    review = build_ai_hypothesis_review(feedback, archive=_archive())
    assert review["summary_counts"]["failed"] == 1
    assert review["hypotheses"][0]["review_status_zh"] == "假设未通过"


def test_save_ai_hypothesis_review_writes_local_file(tmp_path):
    saved = save_ai_hypothesis_review(_feedback(), archive=_archive(), output_dir=tmp_path / "ai_reviews")
    assert saved["status"] == "saved"
    assert Path(saved["path"]).exists()
    assert saved["review"]["summary_counts"]["supported"] == 2


def test_ai_hypothesis_review_history_aggregates_support_rate(tmp_path):
    output_dir = tmp_path / "ai_reviews"
    save_ai_hypothesis_review(_feedback(), archive=_archive(), output_dir=output_dir)
    history = build_ai_hypothesis_review_history(output_dir)
    assert history["files_loaded"] == 1
    assert history["reviewed_count"] == 2
    assert history["supported_count"] == 2
    assert history["supported_rate"] == 1.0
    assert history["factor_rows"]
    assert history["factor_rows"][0]["reviewed"] >= 1

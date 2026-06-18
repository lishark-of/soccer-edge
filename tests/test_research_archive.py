from pathlib import Path

from src.learning.observation_snapshot import build_observation_snapshot
from src.learning.research_archive import load_latest_research_archive, save_research_archive


def _best_parlay_summary():
    return {
        "daily_single_candidate": {
            "match": "土耳其 vs 巴拉圭",
            "play_type": "胜平负",
            "direction": "主胜",
            "odds": 2.1,
            "model_prob": 0.52,
            "market_prob": 0.47,
            "ev": 0.092,
            "edge": 0.05,
            "status": "纸面候选",
        },
        "daily_2x1_candidate": {
            "legs": "美国 vs 澳大利亚 主胜；瑞士 vs 波黑 主胜",
            "combo_odds": 3.4,
            "combo_prob": 0.31,
            "ev": 0.054,
            "status": "纸面候选",
            "reject_reason": "未通过可信度门控。",
        },
        "daily_3x1_candidate": {
            "legs": "捷克 vs 南非 主胜；墨西哥 vs 韩国 主胜；土耳其 vs 巴拉圭 主胜",
            "combo_odds": 6.8,
            "combo_prob": 0.16,
            "ev": 0.088,
            "status": "纸面候选",
            "reject_reason": "3串1 风险过高。",
        },
        "rejected_combos": [],
    }


def _preview_and_optimizer():
    best = _best_parlay_summary()
    optimizer = {
        "selected_date": "2026-06-19",
        "provider_used": "sporttery",
        "risk_profile": "aggressive",
        "selected_portfolio": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
        "candidate_rankings": {"singles": [], "parlay_2x1": [], "parlay_3x1": []},
        "best_parlay_summary": best,
        "no_combo_reason": "可信度不足，组合只作纸面候选。",
    }
    preview = {
        "selected_date": "2026-06-19",
        "provider_used": "sporttery",
        "matches_count": 8,
        "credibility_gate": {"combo_gate": "closed", "label_zh": "不建议串联"},
        "optimizer": optimizer,
        "top_single_observations": [best["daily_single_candidate"]],
        "top_total_goals_observations": [],
        "top_score_observations": [],
    }
    return preview, optimizer


def test_snapshot_includes_daily_paper_candidates():
    preview, _optimizer = _preview_and_optimizer()
    snapshot = build_observation_snapshot(preview)
    tracks = {row.get("learning_track") for row in snapshot["daily_candidate_observations"]}
    assert {"daily_single_candidate", "daily_2x1_candidate", "daily_3x1_candidate"}.issubset(tracks)
    assert snapshot["daily_candidate_count"] >= 3


def test_research_archive_saves_ai_telemetry_and_learning_pack(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    preview, optimizer = _preview_and_optimizer()
    ai_research = {
        "ds_status": "loaded",
        "ds_completed": True,
        "token_in": 600,
        "token_out": 180,
        "token_total": 780,
        "ai_summary": {"provider": "deepseek", "text": "DS 研究摘要"},
        "ai_cost_ledger": {"deepseek_call_count": 1, "message_zh": "本次调用 DS Pro 1 次。"},
    }
    saved = save_research_archive(preview, optimizer, ai_research, output_dir="data/research_archive")
    assert saved["status"] == "saved"
    assert Path(saved["path"]).exists()
    assert saved["ds_completed"] is True
    assert saved["token_total"] == 780
    assert saved["observations_path"]
    assert saved["results_path"]
    assert saved["closing_odds_path"]
    archive = saved["archive"]
    assert archive["daily_candidates"]["daily_2x1_candidate"]["learning_track"] == "daily_2x1_candidate"
    latest = load_latest_research_archive("2026-06-19", archive_dir="data/research_archive")
    assert latest["status"] == "available"
    assert latest["latest"]["token_total"] == 780

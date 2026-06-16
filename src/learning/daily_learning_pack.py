from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from src.learning.closing_odds_template import save_closing_odds_template_from_observations
from src.learning.feedback_builder import save_feedback_from_files
from src.learning.history import build_learning_history
from src.learning.observation_snapshot import save_observation_snapshot
from src.learning.result_template import save_result_template_from_observations
from src.market.clv import save_clv_review


def prepare_daily_learning_pack(preview: dict) -> dict:
    snapshot = save_observation_snapshot(preview)
    observations_path = snapshot.get("path", "")
    result_template = save_result_template_from_observations(observations_path)
    closing_template = save_closing_odds_template_from_observations(observations_path)
    return {
        "status": "prepared",
        "observations_path": observations_path,
        "results_path": result_template.get("path", ""),
        "closing_odds_path": closing_template.get("path", ""),
        "observations_count": snapshot.get("observations_count", 0),
        "rejected_combo_count": snapshot.get("rejected_combo_count", 0),
        "matches_count": result_template.get("matches_count", 0),
        "closing_rows_count": closing_template.get("rows_count", 0),
        "snapshot": snapshot,
        "result_template": result_template,
        "closing_template": closing_template,
        "summary_zh": "已一键准备赛前学习包：观察快照、比分模板、收盘赔率模板和被拒组合复盘样本都已生成。",
        "next_step_zh": "赛后只需要填写比分模板中的进球数，以及可选填写收盘赔率模板中的 closing_odds，然后保存学习样本和 CLV 样本。",
        "privacy_zh": "学习包全部保存在本机 data/learning_* 目录，均已加入 gitignore。",
        "disclaimer": "学习包只用于模型校准和纸面复盘，不构成任何真实投注建议。",
    }


def save_daily_learning_results(
    observations_json: str,
    results_csv: str,
    closing_odds_csv: str | None = None,
) -> dict:
    feedback = save_feedback_from_files(observations_json, results_csv)
    clv = None
    if closing_odds_csv:
        clv = save_clv_review(observations_json, closing_odds_csv)
    history = build_learning_history()
    feedback_date = str((feedback.get("feedback") or {}).get("date") or "")
    latest_daily = next((row for row in history.get("daily_metrics", []) or [] if row.get("date") == feedback_date), None)
    return {
        "status": "saved",
        "feedback": feedback,
        "clv": clv,
        "feedback_path": feedback.get("path"),
        "clv_path": (clv or {}).get("path"),
        "daily_metrics": latest_daily,
        "window_metrics": history.get("window_metrics", []),
        "daily_digest": history.get("daily_digest", {}),
        "window_digests": history.get("window_digests", []),
        "learning_history_summary": history.get("probability_quality", {}),
        "summary_zh": "已一键保存赛后学习：赛果反馈已进入本地学习库，CLV 样本已按可用收盘赔率保存。",
        "next_step_zh": "下次打开 App 时，赔率段、概率段和 CLV 价格学习会自动读取这些本地样本。",
        "privacy_zh": "所有学习样本只保存在本机 data/learning_* 目录，均已加入 gitignore。",
        "disclaimer": "赛后学习只用于模型校准和纸面复盘，不构成任何真实投注建议。",
    }


def save_quick_learning_results(
    observations_json: str,
    rows: list[dict],
) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("data/learning_results")
    closing_dir = Path("data/learning_closing_odds")
    results_dir.mkdir(parents=True, exist_ok=True)
    closing_dir.mkdir(parents=True, exist_ok=True)
    results_path = results_dir / f"quick_results_{timestamp}.csv"
    closing_path = closing_dir / f"quick_closing_odds_{timestamp}.csv"
    cleaned_rows = [_clean_quick_row(row) for row in rows or []]
    result_rows = [row for row in cleaned_rows if row.get("home_goals") != "" and row.get("away_goals") != ""]
    closing_rows = [row for row in cleaned_rows if row.get("closing_odds")]
    with results_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["date", "match_id", "match_no", "match", "home_team", "away_team", "home_goals", "away_goals", "actual_handicap_outcome_zh"],
        )
        writer.writeheader()
        for row in result_rows:
            writer.writerow({
                "date": row.get("date", ""),
                "match_id": row.get("match_id", ""),
                "match_no": row.get("match_no", ""),
                "match": row.get("match", ""),
                "home_team": row.get("home_team", ""),
                "away_team": row.get("away_team", ""),
                "home_goals": row.get("home_goals", ""),
                "away_goals": row.get("away_goals", ""),
                "actual_handicap_outcome_zh": row.get("actual_handicap_outcome_zh", ""),
            })
    closing_csv_path = ""
    if closing_rows:
        with closing_path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["key", "match", "play_type", "direction", "entry_odds", "closing_odds"])
            writer.writeheader()
            for row in closing_rows:
                writer.writerow({
                    "key": row.get("key", ""),
                    "match": row.get("match", ""),
                    "play_type": row.get("play_type", ""),
                    "direction": row.get("direction", ""),
                    "entry_odds": row.get("entry_odds", ""),
                    "closing_odds": row.get("closing_odds", ""),
                })
        closing_csv_path = str(closing_path)
    saved = save_daily_learning_results(observations_json, str(results_path), closing_csv_path or None)
    return {
        **saved,
        "quick_results_path": str(results_path),
        "quick_closing_odds_path": closing_csv_path,
        "quick_rows_received": len(rows or []),
        "quick_results_saved": len(result_rows),
        "quick_closing_saved": len(closing_rows),
        "summary_zh": f"已从页面快速填写保存赛后学习：比分 {len(result_rows)} 场，收盘赔率 {len(closing_rows)} 项。",
        "next_step_zh": "下次刷新累计学习时，这些比分、赔率段和 CLV 会进入本地学习统计。",
    }


def _clean_quick_row(row: dict) -> dict:
    def text(key: str) -> str:
        return str(row.get(key) or "").strip()

    return {
        "date": text("date"),
        "match_id": text("match_id"),
        "match_no": text("match_no") or text("match_num"),
        "match": text("match"),
        "home_team": text("home_team"),
        "away_team": text("away_team"),
        "home_goals": _int_text(row.get("home_goals")),
        "away_goals": _int_text(row.get("away_goals")),
        "actual_handicap_outcome_zh": text("actual_handicap_outcome_zh"),
        "key": text("key"),
        "play_type": text("play_type"),
        "direction": text("direction"),
        "entry_odds": text("entry_odds"),
        "closing_odds": _float_text(row.get("closing_odds")),
    }


def _int_text(value) -> str:
    try:
        return str(int(float(str(value).strip())))
    except (TypeError, ValueError):
        return ""


def _float_text(value) -> str:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return ""
    return str(number) if number > 1 else ""

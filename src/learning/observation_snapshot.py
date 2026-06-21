from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.learning.competition_segments import classify_competition_segment
from src.optimizer.best_parlay import build_best_parlay_summary


def build_observation_snapshot(preview: dict) -> dict:
    optimizer = preview.get("optimizer", {}) or {}
    portfolio = optimizer.get("selected_portfolio", {}) or {}
    selected_date = preview.get("selected_date") or preview.get("date")
    ai_research = preview.get("ai_combo_research") or {}
    ai_summary = ai_research.get("ai_summary") or {}
    trader_review = preview.get("trader_review") or {}
    rows: list[dict] = []
    rows.extend(_compact(row, "single", selected_date) for row in preview.get("top_single_observations", []) or [])
    rows.extend(_compact(row, "total_goals", selected_date) for row in preview.get("top_total_goals_observations", []) or [])
    rows.extend(_compact(row, "correct_score", selected_date) for row in preview.get("top_score_observations", []) or [])
    for combo_type in ("parlay_2x1", "parlay_3x1"):
        for row in portfolio.get(combo_type, []) or []:
            rows.append(_compact_combo(row, combo_type, selected_date))
    best_parlay = optimizer.get("best_parlay_summary") or preview.get("best_parlay_summary") or build_best_parlay_summary(optimizer)
    daily_candidate_rows = _daily_candidate_rows(best_parlay, selected_date)
    rows.extend(daily_candidate_rows)
    rejected_combo_rows = _rejected_combo_rows(optimizer)
    rows.extend(rejected_combo_rows)
    return {
        "snapshot_version": "phase2_learning_observation_snapshot_v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selected_date": selected_date,
        "provider_used": preview.get("provider_used"),
        "matches_count": preview.get("matches_count"),
        "credibility_gate": preview.get("credibility_gate", {}),
        "no_combo_reason": optimizer.get("no_combo_reason") or (preview.get("credibility_gate") or {}).get("reason_zh", ""),
        "top_signals_summary": {
            "top_single": (preview.get("top_single_observations") or [None])[0],
            "top_total_goals": (preview.get("top_total_goals_observations") or [None])[0],
            "top_score": (preview.get("top_score_observations") or [None])[0],
        },
        "trader_review": {
            "final_call_zh": trader_review.get("final_call_zh", ""),
            "no_combo_reason": trader_review.get("no_combo_reason", ""),
            "credibility_gate": trader_review.get("credibility_gate", {}),
        },
        "ai_research": {
            "provider": ai_summary.get("provider") or ai_research.get("ai_provider_resolved") or "local",
            "ds_status": ai_research.get("ds_status") or ai_summary.get("ds_status") or "not_requested",
            "ds_attempted": ai_research.get("ds_attempted", ai_summary.get("ds_attempted", False)),
            "ds_completed": ai_research.get("ds_completed", ai_summary.get("ds_completed", False)),
            "ds_error_code": ai_research.get("ds_error_code") or ai_summary.get("ds_error_code") or "",
            "token_in": ai_research.get("token_in", ai_summary.get("token_in")),
            "token_out": ai_research.get("token_out", ai_summary.get("token_out")),
            "token_total": ai_research.get("token_total", ai_summary.get("token_total")),
            "fallback_reason": ai_research.get("fallback_reason") or ai_summary.get("fallback_reason") or "",
            "summary_text": ai_summary.get("text") or ai_research.get("local_summary_zh") or "",
        },
        "observations": rows,
        "daily_candidate_observations": daily_candidate_rows,
        "rejected_combo_observations": rejected_combo_rows,
        "daily_candidate_count": len(daily_candidate_rows),
        "rejected_combo_count": len(rejected_combo_rows),
        "selected_portfolio": portfolio,
        "disclaimer": "赛前观察快照只用于赛后学习和纸面复盘，不构成任何真实投注建议。",
    }


def save_observation_snapshot(preview: dict, output_dir: str | Path = "data/learning_observations") -> dict:
    snapshot = build_observation_snapshot(preview)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    date_part = str(snapshot.get("selected_date") or datetime.now().strftime("%Y%m%d")).replace("/", "-").replace(" ", "_")
    path = directory / f"observations_{date_part}_{datetime.now().strftime('%H%M%S')}.json"
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": "saved",
        "path": str(path),
        "snapshot": snapshot,
        "observations_count": len(snapshot.get("observations", []) or []),
        "rejected_combo_count": int(snapshot.get("rejected_combo_count") or 0),
        "summary_zh": "已保存赛前观察快照；赛后可用它和比分 CSV 生成学习反馈。",
        "privacy_zh": "文件只保存在本机 data/learning_observations/，该目录已加入 gitignore。",
        "next_step_zh": "赛后在赛后学习页选择赛果 CSV，然后点击保存学习样本。",
    }


def _compact(row: dict, fallback_play_type: str, selected_date: str | None) -> dict:
    segment = classify_competition_segment(row)
    return {
        "date": row.get("date") or selected_date,
        "league": row.get("league") or row.get("competition") or row.get("tournament"),
        "match_id": row.get("match_id"),
        "match_no": row.get("match_no"),
        "match": row.get("match") or f"{row.get('home_team','')} vs {row.get('away_team','')}".strip(),
        "home_team": row.get("home_team"),
        "away_team": row.get("away_team"),
        "play_type": row.get("play_type") or fallback_play_type,
        "direction": row.get("direction") or row.get("outcome_label"),
        "outcome_label": row.get("outcome_label") or row.get("direction"),
        "odds": row.get("official_odds") or row.get("odds"),
        "official_odds": row.get("official_odds") or row.get("odds"),
        "model_prob": row.get("model_prob") or row.get("calibrated_prob"),
        "market_prob": row.get("market_prob"),
        "ev": row.get("ev") or row.get("calibrated_ev"),
        "edge": row.get("edge"),
        "confidence_score": row.get("confidence_score") or row.get("observation_confidence"),
        "paper_stake": row.get("paper_stake") or row.get("suggested_paper_stake"),
        "status": row.get("status"),
        "risk_level": row.get("risk_level"),
        "signal_category_zh": row.get("signal_category_zh"),
        "decision_label_zh": row.get("decision_label_zh"),
        "learning_score_summary_zh": row.get("learning_score_summary_zh"),
        **segment,
    }


def _compact_combo(row: dict, combo_type: str, selected_date: str | None) -> dict:
    legs = row.get("legs", [])
    leg_rows = legs if isinstance(legs, list) else []
    match_label = "；".join(_leg_label(leg) for leg in leg_rows) if leg_rows else str(row.get("match") or row.get("legs") or "")
    segment = classify_competition_segment(row if not leg_rows else leg_rows[0])
    return {
        "date": row.get("date") or selected_date,
        "league": row.get("league") or row.get("competition") or row.get("tournament"),
        "type": combo_type,
        "candidate_type": combo_type,
        "match": match_label,
        "play_type": combo_type,
        "direction": "组合观察",
        "odds": row.get("combo_odds") or row.get("odds"),
        "model_prob": row.get("combo_prob") or row.get("model_prob"),
        "market_prob": row.get("market_prob"),
        "ev": row.get("ev"),
        "edge": row.get("edge"),
        "confidence_score": row.get("confidence_score"),
        "paper_stake": row.get("paper_stake") or row.get("suggested_paper_stake"),
        "risk_level": row.get("risk_level"),
        "legs": leg_rows,
        "status": row.get("status") or row.get("selection_status") or "",
        "reject_reason": row.get("reject_reason") or row.get("discipline_summary_zh") or "",
        "learning_track": row.get("learning_track") or "selected_combo",
        **segment,
    }


def _rejected_combo_rows(optimizer: dict, limit_per_type: int = 5) -> list[dict]:
    rankings = optimizer.get("candidate_rankings") or {}
    rows: list[dict] = []
    for combo_type in ("parlay_2x1", "parlay_3x1"):
        picked = 0
        for row in rankings.get(combo_type, []) or []:
            status = str(row.get("status") or row.get("selection_status") or "")
            if status in {"selected", "selected_after_gate", "通过门控", "pass"} or status.lower() == "selected":
                continue
            compact = _compact_combo({**row, "learning_track": "rejected_combo"}, combo_type, optimizer.get("date") or optimizer.get("selected_date"))
            compact["direction"] = "被拒组合复盘"
            compact["decision_label_zh"] = "被拒组合"
            compact["learning_score_summary_zh"] = row.get("reject_reason") or row.get("discipline_summary_zh") or "用于验证组合纪律是否有效。"
            rows.append(compact)
            picked += 1
            if picked >= limit_per_type:
                break
    return rows


def _daily_candidate_rows(best_parlay: dict, selected_date: str | None) -> list[dict]:
    rows: list[dict] = []
    specs = [
        ("daily_single_candidate", "single", "daily_single_candidate", "每日单关纸面候选"),
        ("daily_2x1_candidate", "parlay_2x1", "daily_2x1_candidate", "每日2串1纸面候选"),
        ("daily_3x1_candidate", "parlay_3x1", "daily_3x1_candidate", "每日3串1纸面候选"),
    ]
    seen: set[str] = set()
    for key, candidate_type, track, label in specs:
        item = best_parlay.get(key) or {}
        if not _candidate_has_identity(item):
            continue
        compact = (
            _compact(item, "single", selected_date)
            if candidate_type == "single"
            else _compact_combo(item, candidate_type, selected_date)
        )
        compact["learning_track"] = track
        compact["decision_label_zh"] = label
        compact["learning_score_summary_zh"] = item.get("selected_reason_zh") or item.get("reject_reason") or "每日纸面候选，用于赛后验证。"
        dedupe_key = f"{track}|{compact.get('match')}|{compact.get('direction')}|{compact.get('odds')}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        rows.append(compact)
    return rows


def _candidate_has_identity(item: dict) -> bool:
    return isinstance(item, dict) and item.get("status") != "empty" and bool(item.get("match") or item.get("legs") or item.get("message_zh"))


def _leg_label(leg: dict) -> str:
    return f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label') or leg.get('direction') or ''}".strip()

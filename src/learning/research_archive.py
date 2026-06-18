from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.learning.daily_learning_pack import prepare_daily_learning_pack
from src.optimizer.best_parlay import build_best_parlay_summary

ARCHIVE_VERSION = "phase2r_research_archive_v0"
DEFAULT_ARCHIVE_DIR = Path("data/research_archive")
DISCLAIMER = "赛前研究档案只用于纸面观察、赛后复盘和模型校准，不构成任何真实投注建议。"


def save_research_archive(
    preview: dict,
    optimizer_result: dict,
    ai_research: dict | None = None,
    *,
    output_dir: str | Path = DEFAULT_ARCHIVE_DIR,
) -> dict:
    """Save a timestamped prematch research archive and linked learning pack."""
    ai_research = ai_research or {}
    preview_for_learning = dict(preview or {})
    optimizer_for_learning = dict(optimizer_result or {})
    best_parlay = optimizer_for_learning.get("best_parlay_summary") or build_best_parlay_summary(optimizer_for_learning)
    optimizer_for_learning["best_parlay_summary"] = best_parlay
    preview_for_learning["optimizer"] = optimizer_for_learning
    preview_for_learning["ai_combo_research"] = ai_research
    preview_for_learning["best_parlay_summary"] = best_parlay
    if optimizer_for_learning.get("selected_date") and not preview_for_learning.get("selected_date"):
        preview_for_learning["selected_date"] = optimizer_for_learning.get("selected_date")
    learning_pack = prepare_daily_learning_pack(preview_for_learning)
    archive = build_research_archive_payload(preview_for_learning, optimizer_for_learning, ai_research, learning_pack)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    selected_date = _safe_date_part(archive.get("selected_date"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    provider = _safe_slug(archive.get("provider_used") or archive.get("provider") or "unknown")
    path = directory / f"research_{selected_date}_{provider}_{timestamp}.json"
    path.write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path = directory / "latest_research_archive.json"
    latest_path.write_text(json.dumps({"path": str(path), "archive": archive}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": "saved",
        "archive_version": ARCHIVE_VERSION,
        "path": str(path),
        "latest_path": str(latest_path),
        "archive": archive,
        "learning_pack": learning_pack,
        "observations_path": learning_pack.get("observations_path", ""),
        "results_path": learning_pack.get("results_path", ""),
        "closing_odds_path": learning_pack.get("closing_odds_path", ""),
        "observations_count": learning_pack.get("observations_count", 0),
        "rejected_combo_count": learning_pack.get("rejected_combo_count", 0),
        "ai_status": archive.get("ai_research", {}).get("ds_status"),
        "ds_completed": archive.get("ai_research", {}).get("ds_completed"),
        "token_total": archive.get("ai_research", {}).get("token_total"),
        "summary_zh": "已保存本次赛前研究档案，并同步准备赛果模板与收盘赔率模板。",
        "next_step_zh": "赛后填写比分模板；如果有收盘赔率，也填写赔率模板，再保存学习样本计算 Brier、Log Loss、ROI 和 CLV。",
        "privacy_zh": "研究档案只保存在本机 data/research_archive/，不会提交到 Git。",
        "disclaimer": DISCLAIMER,
    }


def build_research_archive_payload(preview: dict, optimizer_result: dict, ai_research: dict, learning_pack: dict) -> dict:
    best_parlay = optimizer_result.get("best_parlay_summary") or build_best_parlay_summary(optimizer_result)
    ai_summary = ai_research.get("ai_summary") or {}
    structured = ai_research.get("structured_notes") or {}
    cost = ai_research.get("ai_cost_ledger") or {}
    selected_date = preview.get("selected_date") or optimizer_result.get("selected_date") or preview.get("date") or optimizer_result.get("date")
    daily_candidates = _daily_candidates(best_parlay)
    return {
        "archive_version": ARCHIVE_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selected_date": selected_date,
        "provider": preview.get("provider") or optimizer_result.get("provider"),
        "provider_used": preview.get("provider_used") or optimizer_result.get("provider_used"),
        "matches_count": preview.get("matches_count") or optimizer_result.get("matches_analyzed"),
        "bankroll": optimizer_result.get("bankroll") or preview.get("bankroll") or 10000,
        "risk_profile": optimizer_result.get("risk_profile") or preview.get("risk_profile"),
        "data_source_status": preview.get("data_source_status", {}),
        "credibility_gate": preview.get("credibility_gate") or optimizer_result.get("credibility_gate") or {},
        "credibility_audit": preview.get("credibility_audit") or optimizer_result.get("credibility_audit") or {},
        "missing_signals": preview.get("missing_signals") or optimizer_result.get("missing_signals") or [],
        "top_observations": {
            "singles": preview.get("top_single_observations") or [],
            "total_goals": preview.get("top_total_goals_observations") or optimizer_result.get("top_total_goals_observations") or [],
            "scores": preview.get("top_score_observations") or optimizer_result.get("top_score_observations") or [],
        },
        "daily_candidates": daily_candidates,
        "best_parlay_summary": best_parlay,
        "selected_portfolio": optimizer_result.get("selected_portfolio", {}),
        "candidate_rankings": optimizer_result.get("candidate_rankings", {}),
        "rejected_candidates": optimizer_result.get("rejected_candidates") or best_parlay.get("rejected_combos") or [],
        "trader_review": optimizer_result.get("trader_review") or preview.get("trader_review") or {},
        "ai_research": {
            "provider_requested": ai_research.get("provider_requested") or ai_research.get("ai_provider_requested"),
            "provider_resolved": ai_research.get("provider_resolved") or ai_research.get("ai_provider_resolved") or ai_summary.get("provider"),
            "ds_status": ai_research.get("ds_status") or ai_summary.get("ds_status"),
            "ds_status_zh": ai_research.get("ds_status_zh") or ai_summary.get("ds_status_zh"),
            "ds_attempted": ai_research.get("ds_attempted", ai_summary.get("ds_attempted", False)),
            "ds_completed": ai_research.get("ds_completed", ai_summary.get("ds_completed", False)),
            "ds_error_code": ai_research.get("ds_error_code") or ai_summary.get("ds_error_code") or "",
            "fallback_reason": ai_research.get("fallback_reason") or ai_summary.get("fallback_reason") or "",
            "display_status_zh": ai_research.get("display_status_zh") or ai_summary.get("display_status_zh") or "",
            "token_in": ai_research.get("token_in") or ai_summary.get("token_in"),
            "token_out": ai_research.get("token_out") or ai_summary.get("token_out"),
            "token_total": ai_research.get("token_total") or ai_summary.get("token_total"),
            "deepseek_call_count": cost.get("deepseek_call_count", 0),
            "cost_message_zh": cost.get("message_zh", ""),
            "summary_text": ai_summary.get("text") or ai_research.get("local_summary_zh") or "",
            "structured_notes": structured,
            "local_summary_zh": ai_research.get("local_summary_zh", ""),
        },
        "learning_pack": {
            "observations_path": learning_pack.get("observations_path", ""),
            "results_path": learning_pack.get("results_path", ""),
            "closing_odds_path": learning_pack.get("closing_odds_path", ""),
            "observations_count": learning_pack.get("observations_count", 0),
            "rejected_combo_count": learning_pack.get("rejected_combo_count", 0),
            "matches_count": learning_pack.get("matches_count", 0),
            "closing_rows_count": learning_pack.get("closing_rows_count", 0),
        },
        "postmatch_learning_plan": [
            "赛后填写比分模板中的主客队进球。",
            "如能拿到收盘赔率，填写 closing_odds 模板用于 CLV。",
            "保存赛后学习后，系统会计算 Brier、Log Loss、ROI、CLV，并复盘被拒组合是否应该继续拒绝。",
        ],
        "safety_zh": "DS Pro 只做解释、质检和复盘摘要，不改写概率、不绕过可信度门控。",
        "disclaimer": DISCLAIMER,
    }


def load_latest_research_archive(date: str | None = None, *, archive_dir: str | Path = DEFAULT_ARCHIVE_DIR, limit: int = 12) -> dict:
    directory = Path(archive_dir)
    if not directory.exists():
        return _empty_archive_view(date)
    files = sorted(directory.glob("research_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    rows = []
    for file_path in files:
        try:
            archive = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if date and str(archive.get("selected_date") or "") != str(date):
            continue
        rows.append(_archive_row(file_path, archive))
        if len(rows) >= limit:
            break
    if not rows:
        return _empty_archive_view(date)
    latest = rows[0]
    return {
        "status": "available",
        "latest": latest,
        "archives": rows,
        "archive_count": len(rows),
        "summary_zh": "已找到本地赛前研究档案，可用于赛后回填和学习。",
        "disclaimer": DISCLAIMER,
    }


def _archive_row(path: Path, archive: dict) -> dict:
    ai = archive.get("ai_research", {}) or {}
    pack = archive.get("learning_pack", {}) or {}
    daily = archive.get("daily_candidates", {}) or {}
    return {
        "path": str(path),
        "created_at": archive.get("created_at", ""),
        "selected_date": archive.get("selected_date", ""),
        "provider_used": archive.get("provider_used", ""),
        "matches_count": archive.get("matches_count", 0),
        "ds_status": ai.get("ds_status") or "unknown",
        "ds_completed": bool(ai.get("ds_completed")),
        "token_total": ai.get("token_total"),
        "summary_preview": _short(ai.get("summary_text") or ai.get("local_summary_zh") or ""),
        "daily_single": _candidate_label(daily.get("daily_single_candidate")),
        "daily_2x1": _candidate_label(daily.get("daily_2x1_candidate")),
        "daily_3x1": _candidate_label(daily.get("daily_3x1_candidate")),
        "observations_path": pack.get("observations_path", ""),
        "results_path": pack.get("results_path", ""),
        "closing_odds_path": pack.get("closing_odds_path", ""),
    }


def _daily_candidates(best_parlay: dict) -> dict:
    return {
        "daily_single_candidate": _mark_learning_track(best_parlay.get("daily_single_candidate") or best_parlay.get("best_single"), "daily_single_candidate"),
        "daily_2x1_candidate": _mark_learning_track(best_parlay.get("daily_2x1_candidate") or best_parlay.get("best_2x1"), "daily_2x1_candidate"),
        "daily_3x1_candidate": _mark_learning_track(best_parlay.get("daily_3x1_candidate") or best_parlay.get("best_3x1_if_allowed"), "daily_3x1_candidate"),
    }


def _mark_learning_track(candidate: Any, track: str) -> dict:
    if not isinstance(candidate, dict):
        return {}
    if candidate.get("status") == "empty" and not (candidate.get("match") or candidate.get("legs")):
        return dict(candidate)
    return {**candidate, "learning_track": candidate.get("learning_track") or track}


def _candidate_label(candidate: Any) -> str:
    if not isinstance(candidate, dict) or not candidate:
        return "暂无"
    return str(candidate.get("legs") or candidate.get("match") or candidate.get("message_zh") or candidate.get("label_zh") or "暂无")


def _empty_archive_view(date: str | None = None) -> dict:
    return {
        "status": "empty",
        "latest": {},
        "archives": [],
        "archive_count": 0,
        "selected_date": date,
        "summary_zh": "暂无本地赛前研究档案。刷新今日观察并完成 AI/本地研究后会自动保存。",
        "disclaimer": DISCLAIMER,
    }


def _safe_date_part(value: Any) -> str:
    text = str(value or datetime.now().strftime("%Y-%m-%d")).strip().replace("/", "-").replace(" ", "_")
    return text or datetime.now().strftime("%Y-%m-%d")


def _safe_slug(value: Any) -> str:
    text = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value or "unknown"))
    return text.strip("_") or "unknown"


def _short(text: str, limit: int = 180) -> str:
    clean = " ".join(str(text or "").split())
    return clean if len(clean) <= limit else clean[:limit] + "..."

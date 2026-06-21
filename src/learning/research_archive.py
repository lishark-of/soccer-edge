from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.learning.daily_learning_pack import prepare_daily_learning_pack
from src.learning.ai_factor_taxonomy import classify_ai_factor
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
        "clv_followup": archive.get("clv_followup", {}),
        "clv_pending_count": archive.get("clv_followup", {}).get("pending_count", 0),
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
    clv_followup = _clv_followup(learning_pack)
    hypotheses = _verifiable_hypotheses(structured, daily_candidates, best_parlay, preview, optimizer_result)
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
            "verifiable_hypotheses": hypotheses,
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
        "clv_followup": clv_followup,
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
        "verifiable_hypothesis_count": len(ai.get("verifiable_hypotheses") or []),
        "summary_preview": _short(ai.get("summary_text") or ai.get("local_summary_zh") or ""),
        "daily_single": _candidate_label(daily.get("daily_single_candidate")),
        "daily_2x1": _candidate_label(daily.get("daily_2x1_candidate")),
        "daily_3x1": _candidate_label(daily.get("daily_3x1_candidate")),
        "observations_path": pack.get("observations_path", ""),
        "results_path": pack.get("results_path", ""),
        "closing_odds_path": pack.get("closing_odds_path", ""),
        "clv_pending_count": (archive.get("clv_followup") or {}).get("pending_count", 0),
        "clv_priority_rows": (archive.get("clv_followup") or {}).get("priority_rows", [])[:3],
    }


def _daily_candidates(best_parlay: dict) -> dict:
    return {
        "daily_single_candidate": _mark_learning_track(best_parlay.get("daily_single_candidate") or best_parlay.get("best_single"), "daily_single_candidate"),
        "daily_2x1_candidate": _mark_learning_track(best_parlay.get("daily_2x1_candidate") or best_parlay.get("best_2x1"), "daily_2x1_candidate"),
        "daily_3x1_candidate": _mark_learning_track(best_parlay.get("daily_3x1_candidate") or best_parlay.get("best_3x1_if_allowed"), "daily_3x1_candidate"),
    }


def _clv_followup(learning_pack: dict) -> dict:
    snapshot = learning_pack.get("snapshot") or {}
    observations = snapshot.get("observations") or []
    rows = []
    seen: set[str] = set()
    for row in observations:
        if not isinstance(row, dict) or row.get("legs"):
            continue
        key = _observation_key(row)
        entry_odds = _float_or_none(row.get("odds") or row.get("official_odds") or row.get("entry_odds"))
        if not key or key in seen or entry_odds is None or entry_odds <= 1.0:
            continue
        seen.add(key)
        rows.append({
            "key": key,
            "match": row.get("match") or f"{row.get('home_team','')} vs {row.get('away_team','')}".strip(),
            "play_type": row.get("play_type") or row.get("type") or "",
            "direction": row.get("direction") or row.get("outcome_label") or "",
            "entry_odds": round(entry_odds, 4),
            "closing_odds": "",
            "learning_track": row.get("learning_track") or "",
            "status": "pending_closing_odds",
            "status_zh": "等待收盘赔率",
            "why_needed_zh": "用于检查赛前赔率是否跑赢临近开赛/赛后收盘赔率；这是评估模型是否早于市场的重要证据。",
        })
    priority = sorted(rows, key=_clv_priority_key, reverse=True)
    return {
        "status": "prepared" if rows else "empty",
        "pending_count": len(rows),
        "template_path": learning_pack.get("closing_odds_path", ""),
        "priority_rows": priority[:8],
        "field_requirements": ["key", "match", "play_type", "direction", "entry_odds", "closing_odds"],
        "summary_zh": (
            f"已准备 {len(rows)} 条 CLV 待回填项；优先填写 Top 单关、每日纸面候选和高 EV 候选的 closing_odds。"
            if rows
            else "当前没有可用于 CLV 的单腿赔率观察项。"
        ),
        "next_step_zh": "赛后或临近开赛后，在收盘赔率模板中填写 closing_odds，再保存 CLV 复盘；长期看平均 CLV 是否为正。",
        "disclaimer": "CLV 只用于赛前价格质量复盘，不构成真实投注建议。",
    }


def _clv_priority_key(row: dict) -> tuple:
    track = str(row.get("learning_track") or "")
    track_score = {
        "daily_single_candidate": 5,
        "daily_2x1_candidate": 4,
        "daily_3x1_candidate": 3,
    }.get(track, 1)
    return (track_score, _float_or_none(row.get("entry_odds")) or 0.0)


def _observation_key(row: dict) -> str:
    parts = [
        row.get("match_id") or row.get("match_no") or row.get("match") or "",
        row.get("play_type") or row.get("type") or "",
        row.get("outcome_key") or row.get("direction") or row.get("outcome_label") or "",
    ]
    return "|".join(str(part).strip() for part in parts)


def _float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _verifiable_hypotheses(structured: dict, daily_candidates: dict, best_parlay: dict, preview: dict, optimizer_result: dict) -> list[dict]:
    hypotheses: list[dict] = []
    selected_date = preview.get("selected_date") or optimizer_result.get("selected_date") or preview.get("date") or optimizer_result.get("date")
    for key, candidate_key, label in (
        ("single_notes", "daily_single_candidate", "单关假设"),
        ("combo_notes", "daily_2x1_candidate", "2串1假设"),
        ("rejected_combo_notes", "rejected_combo_review", "被拒组合假设"),
        ("total_goals_notes", "total_goals", "总进球假设"),
        ("score_notes", "score", "比分假设"),
    ):
        for index, note in enumerate(structured.get(key) or []):
            if not isinstance(note, dict):
                continue
            actual_candidate_key = _combo_note_category(note, daily_candidates) if key == "combo_notes" else candidate_key
            actual_label = "3串1假设" if actual_candidate_key == "daily_3x1_candidate" else label
            candidate = daily_candidates.get(actual_candidate_key) if actual_candidate_key in daily_candidates else {}
            factor = classify_ai_factor(note, actual_candidate_key)
            hypotheses.append(
                {
                    "id": f"{key}_{index + 1}",
                    "date": selected_date,
                    "category": actual_candidate_key,
                    "label_zh": actual_label,
                    "target": note.get("target") or _candidate_label(candidate),
                    "hypothesis_zh": note.get("note_zh") or note.get("usage_zh") or "AI 提供了该观察项的研究解释。",
                    "validation_metric": _hypothesis_metric(actual_candidate_key),
                    "validation_rule_zh": _hypothesis_validation_rule(actual_candidate_key),
                    "expected_after_match_fields": _hypothesis_fields(actual_candidate_key),
                    "source": structured.get("structured_source") or structured.get("source") or "local_fallback",
                    "status": "pending_result",
                    "status_zh": "等待赛后验证",
                    "learning_track": candidate.get("learning_track") if isinstance(candidate, dict) else actual_candidate_key,
                    **factor,
                }
            )
    if not hypotheses:
        hypotheses.append(
            {
                "id": "local_summary_1",
                "date": selected_date,
                "category": "ai_summary",
                "label_zh": "AI摘要假设",
                "target": "本次赛前研究",
                "hypothesis_zh": "AI/本地摘要已生成，但缺少可拆分结构化假设；赛后只能做整体复盘。",
                "validation_metric": "archive_presence",
                "validation_rule_zh": "先要求 AI 输出结构化假设，再进入逐项赛后验证。",
                "expected_after_match_fields": ["structured_notes", "result_scores", "closing_odds"],
                "source": "local_fallback",
                "status": "needs_structure",
                "status_zh": "缺少结构化假设",
                **classify_ai_factor("AI 摘要缺少结构化假设", "ai_summary"),
            }
        )
    return hypotheses[:16]


def _hypothesis_metric(category: str) -> str:
    if category in {"daily_single_candidate", "total_goals", "score"}:
        return "hit_brier_logloss_clv"
    if category in {"daily_2x1_candidate", "daily_3x1_candidate"}:
        return "combo_hit_clv_drawdown"
    if category == "rejected_combo_review":
        return "rejected_combo_would_have_hit"
    return "postmatch_review"


def _hypothesis_validation_rule(category: str) -> str:
    if category == "daily_single_candidate":
        return "赛后检查该方向是否命中、Brier/Log Loss 是否合理，以及入场赔率是否跑赢收盘赔率。"
    if category == "daily_2x1_candidate":
        return "赛后检查每一腿是否命中、组合是否全中、CLV 是否支持，以及组合回撤是否可接受。"
    if category == "daily_3x1_candidate":
        return "赛后检查三条腿是否全部命中、组合波动是否过大，以及是否应该继续默认降权。"
    if category == "rejected_combo_review":
        return "赛后检查被拒组合是否全中；若长期全中率偏高，复查当时拒绝规则是否过严。"
    if category == "total_goals":
        return "赛后检查总进球节奏是否接近模型分布，不把单场比分当长期结论。"
    if category == "score":
        return "赛后检查 Top 比分是否落在高概率区间，主要用于校准比分矩阵分散度。"
    return "赛后用结果、收盘赔率和概率质量复盘该解释是否有用。"


def _hypothesis_fields(category: str) -> list[str]:
    fields = ["home_goals", "away_goals", "closing_odds"]
    if category in {"daily_2x1_candidate", "rejected_combo_review"}:
        fields.append("leg_results")
    if category == "daily_3x1_candidate":
        fields.append("leg_results")
    if category in {"score", "total_goals"}:
        fields.append("total_goals")
    return fields


def _combo_note_category(note: dict, daily_candidates: dict) -> str:
    text = " ".join(str(note.get(key) or "") for key in ("target", "note_zh", "usage_zh", "reason_zh"))
    normalized = text.lower()
    if "3串1" in normalized or "3x1" in normalized or "三串" in normalized:
        return "daily_3x1_candidate"
    candidate_3x1 = daily_candidates.get("daily_3x1_candidate") or {}
    candidate_2x1 = daily_candidates.get("daily_2x1_candidate") or {}
    if _candidate_label(candidate_3x1) != "暂无" and _candidate_label(candidate_2x1) == "暂无":
        return "daily_3x1_candidate"
    return "daily_2x1_candidate"


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

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.learning.ai_factor_taxonomy import classify_ai_factor


DEFAULT_ARCHIVE_DIR = Path("data/research_archive")
DEFAULT_OUTPUT_DIR = Path("data/learning_ai_hypotheses")
DISCLAIMER = "AI 假设复盘只用于赛后学习和模型校准，不构成任何真实投注建议。"


def build_ai_hypothesis_review(
    feedback: dict,
    clv_review: dict | None = None,
    *,
    archive: dict | None = None,
    date: str | None = None,
    archive_dir: str | Path = DEFAULT_ARCHIVE_DIR,
) -> dict:
    """Evaluate saved AI/local research hypotheses against post-match feedback."""
    feedback = feedback or {}
    selected_date = str(date or feedback.get("date") or "").strip()
    archive_payload, archive_path = (archive or {}, "")
    if not archive_payload:
        archive_payload, archive_path = load_latest_archive_payload(selected_date or None, archive_dir=archive_dir)
    hypotheses = ((archive_payload.get("ai_research") or {}).get("verifiable_hypotheses") or [])
    if not hypotheses:
        return {
            "status": "no_hypotheses" if archive_payload else "no_archive",
            "date": selected_date or (archive_payload.get("selected_date") if archive_payload else ""),
            "archive_path": archive_path,
            "hypotheses": [],
            "summary_counts": _summary_counts([]),
            "summary_zh": "暂无可评分的 AI 研究假设；需要先生成赛前研究档案并让 AI 输出结构化假设。",
            "next_action_zh": "下一次 T+1 自动研究应保存 single/combo/score/total-goals 的结构化假设，赛后再回填比分和收盘赔率。",
            "disclaimer": DISCLAIMER,
        }

    report = feedback.get("report") or {}
    rows = report.get("rows") or []
    rejected_reviews = feedback.get("rejected_combo_reviews") or report.get("rejected_combo_reviews") or []
    clv_rows = (clv_review or {}).get("rows") or []
    reviews = [_review_hypothesis(hypothesis, rows, rejected_reviews, clv_rows) for hypothesis in hypotheses]
    counts = _summary_counts(reviews)
    return {
        "status": "reviewed",
        "date": selected_date or archive_payload.get("selected_date", ""),
        "archive_path": archive_path,
        "hypotheses": reviews,
        "summary_counts": counts,
        "factor_rows": _factor_rows(reviews),
        "summary_zh": _summary_message(counts),
        "next_action_zh": _next_action_message(counts),
        "quality_zh": _quality_message(counts),
        "disclaimer": DISCLAIMER,
    }


def save_ai_hypothesis_review(
    feedback: dict,
    clv_review: dict | None = None,
    *,
    archive: dict | None = None,
    date: str | None = None,
    archive_dir: str | Path = DEFAULT_ARCHIVE_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict:
    review = build_ai_hypothesis_review(
        feedback,
        clv_review,
        archive=archive,
        date=date,
        archive_dir=archive_dir,
    )
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_date = _safe_slug(review.get("date") or date or datetime.now().strftime("%Y%m%d"))
    path = directory / f"ai_hypothesis_review_{safe_date}_{datetime.now().strftime('%H%M%S')}.json"
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": "saved",
        "path": str(path),
        "review": review,
        "summary_zh": review.get("summary_zh", "已保存 AI 假设复盘。"),
        "next_step_zh": review.get("next_action_zh", "继续累计赛后样本。"),
        "privacy_zh": "AI 假设复盘只保存在本机 data/learning_ai_hypotheses/，不会提交到 Git。",
        "disclaimer": DISCLAIMER,
    }


def build_ai_hypothesis_review_history(review_dir: str | Path = DEFAULT_OUTPUT_DIR) -> dict:
    directory = Path(review_dir)
    files = sorted(directory.glob("ai_hypothesis_review_*.json")) if directory.exists() else []
    reviews = []
    errors = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["source_path"] = str(path)
            reviews.append(payload)
        except Exception as exc:
            errors.append({"path": str(path), "message_zh": f"读取失败：{str(exc).splitlines()[0]}"})
    rows = [row for review in reviews for row in review.get("hypotheses", []) or []]
    counts = _summary_counts(rows)
    factor_rows = _factor_rows(rows)
    reviewed = counts["supported"] + counts["failed"] + counts["mixed"]
    supported_rate = round(counts["supported"] / reviewed, 6) if reviewed else None
    failed_rate = round(counts["failed"] / reviewed, 6) if reviewed else None
    return {
        "history_version": "phase2_ai_hypothesis_review_history_v0",
        "files_loaded": len(reviews),
        "errors": errors,
        "hypothesis_count": counts["total"],
        "reviewed_count": reviewed,
        "supported_count": counts["supported"],
        "failed_count": counts["failed"],
        "mixed_count": counts["mixed"],
        "needs_more_data_count": counts["needs_more_data"],
        "supported_rate": supported_rate,
        "failed_rate": failed_rate,
        "rows": rows[-30:],
        "factor_rows": factor_rows,
        "factor_stats": {row["ai_factor"]: row for row in factor_rows},
        "summary_zh": _history_summary(len(reviews), counts, supported_rate),
        "next_action_zh": _history_next_action(counts, supported_rate),
        "disclaimer": DISCLAIMER,
    }


def load_latest_archive_payload(
    date: str | None = None,
    *,
    archive_dir: str | Path = DEFAULT_ARCHIVE_DIR,
) -> tuple[dict, str]:
    directory = Path(archive_dir)
    if not directory.exists():
        return {}, ""
    candidates = sorted(directory.glob("research_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            archive = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if date and str(archive.get("selected_date") or "") != str(date):
            continue
        return archive if isinstance(archive, dict) else {}, str(path)
    latest_path = directory / "latest_research_archive.json"
    if latest_path.exists():
        try:
            payload = json.loads(latest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}, ""
        archive = payload.get("archive") if isinstance(payload, dict) else {}
        if isinstance(archive, dict) and (not date or str(archive.get("selected_date") or "") == str(date)):
            return archive, str(payload.get("path") or latest_path)
    return {}, ""


def _review_hypothesis(hypothesis: dict, rows: list[dict], rejected_reviews: list[dict], clv_rows: list[dict]) -> dict:
    category = str(hypothesis.get("category") or "")
    target = str(hypothesis.get("target") or "")
    matched_rows = _match_rows(target, category, rows)
    matched_rejected = _match_rejected(target, rejected_reviews)
    matched_clv = _match_clv(target, clv_rows)
    status, status_zh, evidence = _status_for(category, matched_rows, matched_rejected, matched_clv)
    factor = classify_ai_factor(hypothesis, category)
    return {
        **hypothesis,
        "ai_factor": hypothesis.get("ai_factor") or factor["ai_factor"],
        "ai_factor_zh": hypothesis.get("ai_factor_zh") or factor["ai_factor_zh"],
        "ai_factor_reason_zh": hypothesis.get("ai_factor_reason_zh") or factor["ai_factor_reason_zh"],
        "review_status": status,
        "review_status_zh": status_zh,
        "matched_feedback_count": len(matched_rows),
        "matched_rejected_combo_count": len(matched_rejected),
        "matched_clv_count": len(matched_clv),
        "hit_count": len([row for row in matched_rows if row.get("hit") is True]),
        "miss_count": len([row for row in matched_rows if row.get("hit") is False]),
        "positive_clv_count": len([row for row in matched_clv if float(row.get("clv_pct") or 0.0) > 0]),
        "negative_clv_count": len([row for row in matched_clv if float(row.get("clv_pct") or 0.0) < 0]),
        "evidence_zh": evidence,
    }


def _status_for(category: str, rows: list[dict], rejected: list[dict], clv_rows: list[dict]) -> tuple[str, str, str]:
    if category == "rejected_combo_review":
        settled = [row for row in rejected if row.get("combo_hit") is not None]
        if not settled:
            return "needs_more_data", "等待更多赛果", "被拒组合还没有完整赛果，暂不能判断拒绝纪律是否正确。"
        if any(row.get("combo_hit") is True for row in settled):
            return "failed", "假设被挑战", "至少一条被拒组合赛后全中，需要复查当时的拒绝原因是否过严。"
        if any(row.get("combo_miss") is True for row in settled):
            return "supported", "假设得到支持", "被拒组合赛后未全中，说明当时的组合纪律得到一次样本支持。"
        return "needs_more_data", "等待更多赛果", "赛后结果暂时中性，继续累计样本。"

    settled_rows = [row for row in rows if row.get("hit") is not None]
    if not settled_rows:
        return "needs_more_data", "等待更多赛果", "没有匹配到可结算观察，暂不能评价该 AI 假设。"
    hit_count = len([row for row in settled_rows if row.get("hit") is True])
    miss_count = len([row for row in settled_rows if row.get("hit") is False])
    positive_clv = len([row for row in clv_rows if float(row.get("clv_pct") or 0.0) > 0])
    negative_clv = len([row for row in clv_rows if float(row.get("clv_pct") or 0.0) < 0])
    if hit_count > 0 and negative_clv == 0:
        return "supported", "假设得到支持", _row_evidence(hit_count, miss_count, positive_clv, negative_clv)
    if miss_count > 0 and positive_clv == 0:
        return "failed", "假设未通过", _row_evidence(hit_count, miss_count, positive_clv, negative_clv)
    return "mixed", "结果混合", _row_evidence(hit_count, miss_count, positive_clv, negative_clv)


def _row_evidence(hit_count: int, miss_count: int, positive_clv: int, negative_clv: int) -> str:
    parts = [f"命中 {hit_count} 项", f"未命中 {miss_count} 项"]
    if positive_clv or negative_clv:
        parts.append(f"CLV 正向 {positive_clv} 项、负向 {negative_clv} 项")
    return "；".join(parts) + "。"


def _match_rows(target: str, category: str, rows: list[dict]) -> list[dict]:
    target_norm = _norm(target)
    category_tracks = {
        "daily_single_candidate": {"daily_single_candidate", "observation"},
        "daily_2x1_candidate": {"daily_2x1_candidate", "parlay_2x1"},
        "daily_3x1_candidate": {"daily_3x1_candidate", "parlay_3x1"},
        "total_goals": {"total_goals"},
        "score": {"score", "correct_score"},
    }.get(category, set())
    matches = []
    for row in rows or []:
        row_text = _row_text(row)
        track = str(row.get("learning_track") or row.get("play_type") or "")
        if target_norm and (_norm(row_text) in target_norm or target_norm in _norm(row_text)):
            matches.append(row)
        elif category_tracks and track in category_tracks:
            matches.append(row)
    return matches


def _match_rejected(target: str, reviews: list[dict]) -> list[dict]:
    target_norm = _norm(target)
    out = []
    for row in reviews or []:
        row_text = " ".join([
            str(row.get("match") or ""),
            str(row.get("reject_reason") or ""),
            " ".join(str((leg or {}).get("match") or "") for leg in row.get("leg_reviews") or []),
        ])
        if not target_norm or target_norm in _norm(row_text) or _norm(row_text) in target_norm:
            out.append(row)
    return out


def _match_clv(target: str, rows: list[dict]) -> list[dict]:
    target_norm = _norm(target)
    out = []
    for row in rows or []:
        row_text = " ".join([
            str(row.get("match") or ""),
            str(row.get("play") or ""),
            str(row.get("direction") or ""),
            str(row.get("key") or ""),
        ])
        if target_norm and (target_norm in _norm(row_text) or _norm(row_text) in target_norm):
            out.append(row)
    return out


def _summary_counts(reviews: list[dict]) -> dict:
    return {
        "total": len(reviews),
        "supported": len([row for row in reviews if row.get("review_status") == "supported"]),
        "failed": len([row for row in reviews if row.get("review_status") == "failed"]),
        "mixed": len([row for row in reviews if row.get("review_status") == "mixed"]),
        "needs_more_data": len([row for row in reviews if row.get("review_status") == "needs_more_data"]),
    }


def _factor_rows(reviews: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in reviews or []:
        factor = str(row.get("ai_factor") or classify_ai_factor(row, row.get("category")).get("ai_factor") or "unknown")
        label = row.get("ai_factor_zh") or classify_ai_factor(row, row.get("category")).get("ai_factor_zh")
        item = grouped.setdefault(factor, {"ai_factor": factor, "ai_factor_zh": label, "total": 0, "supported": 0, "failed": 0, "mixed": 0, "needs_more_data": 0})
        item["total"] += 1
        status = str(row.get("review_status") or "")
        if status in {"supported", "failed", "mixed", "needs_more_data"}:
            item[status] += 1
    out = []
    for item in grouped.values():
        reviewed = int(item["supported"]) + int(item["failed"]) + int(item["mixed"])
        supported_rate = round(int(item["supported"]) / reviewed, 6) if reviewed else None
        failed_rate = round(int(item["failed"]) / reviewed, 6) if reviewed else None
        out.append({
            **item,
            "reviewed": reviewed,
            "supported_rate": supported_rate,
            "failed_rate": failed_rate,
            "message_zh": _factor_message(item["ai_factor_zh"], reviewed, supported_rate, failed_rate),
        })
    return sorted(out, key=lambda row: (row["reviewed"], row.get("supported_rate") or 0), reverse=True)


def _factor_message(label: str, reviewed: int, supported_rate: float | None, failed_rate: float | None) -> str:
    if reviewed <= 0:
        return f"{label} 因子还没有可结算假设。"
    if supported_rate is not None and supported_rate >= 0.60:
        return f"{label} 因子支持率暂时较好，但仍要结合 CLV 和更多日期验证。"
    if failed_rate is not None and failed_rate >= 0.40:
        return f"{label} 因子失败率偏高，后续 AI 摘要不应提高该类信号权重。"
    return f"{label} 因子结果混合，继续累计样本。"


def _summary_message(counts: dict) -> str:
    total = int(counts.get("total") or 0)
    if total <= 0:
        return "暂无可验证 AI 假设。"
    return (
        f"已复盘 {total} 条 AI/本地研究假设："
        f"支持 {counts.get('supported', 0)}，失败 {counts.get('failed', 0)}，"
        f"混合 {counts.get('mixed', 0)}，待更多数据 {counts.get('needs_more_data', 0)}。"
    )


def _history_summary(files_count: int, counts: dict, supported_rate: float | None) -> str:
    if files_count <= 0 or int(counts.get("total") or 0) <= 0:
        return "还没有 AI 假设复盘历史；赛后保存学习后才会累计。"
    reviewed = int(counts.get("supported") or 0) + int(counts.get("failed") or 0) + int(counts.get("mixed") or 0)
    if reviewed <= 0:
        return f"已读取 {files_count} 个 AI 假设复盘文件，但多数仍等待赛果或 CLV。"
    return f"累计复盘 {reviewed} 条 AI 假设，支持率 {_pct(supported_rate)}。"


def _history_next_action(counts: dict, supported_rate: float | None) -> str:
    reviewed = int(counts.get("supported") or 0) + int(counts.get("failed") or 0) + int(counts.get("mixed") or 0)
    if reviewed < 10:
        return "AI 假设复盘样本仍少，先继续让每日研究输出可验证假设。"
    if supported_rate is not None and supported_rate >= 0.6:
        return "AI 假设支持率暂时较好；继续观察是否伴随正 CLV 和更低 Brier/Log Loss。"
    return "AI 假设支持率不足，降低 AI 摘要权重，优先复查失败假设。"


def _next_action_message(counts: dict) -> str:
    if int(counts.get("failed") or 0) > 0:
        return "优先复查失败假设对应的玩法、赔率段和情报缺口，不要直接提高模型自信。"
    if int(counts.get("supported") or 0) > 0:
        return "继续累计同类样本；只有长期支持并伴随正 CLV，才逐步提高该类信号权重。"
    return "继续补赛果和收盘赔率，让 AI 解释从文字摘要变成可评分样本。"


def _quality_message(counts: dict) -> str:
    total = int(counts.get("total") or 0)
    if total < 10:
        return "AI 研究样本仍少，只能用于方向审计，不能证明模型已优于市场。"
    failed = int(counts.get("failed") or 0)
    supported = int(counts.get("supported") or 0)
    if supported > failed:
        return "AI 研究假设暂时有正向证据，但仍需要更多日期和玩法验证。"
    return "AI 研究假设暂未形成稳定优势，建议降低摘要权重。"


def _pct(value: float | None) -> str:
    if value is None:
        return "暂无"
    return f"{value:.1%}"


def _row_text(row: dict) -> str:
    return " ".join([
        str(row.get("match") or ""),
        str(row.get("play_type") or ""),
        str(row.get("direction") or ""),
        str(row.get("learning_track") or ""),
    ])


def _norm(value: Any) -> str:
    return "".join(str(value or "").lower().replace("暂无", "").split())


def _safe_slug(value: Any) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value or "unknown")).strip("_") or "unknown"

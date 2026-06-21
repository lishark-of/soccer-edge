from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.learning.daily_learning_pack import prepare_daily_learning_pack
from src.learning.data_expansion import build_data_expansion_summary
from src.learning.feedback_builder import build_feedback_from_observations_and_results
from src.learning.observation_snapshot import build_observation_snapshot
from src.optimizer.best_parlay import build_best_parlay_summary
from src.providers.sporttery_provider import SportteryProvider


SNAPSHOT_VERSION = "phase2s_daily_snapshot_v0"
DEFAULT_DAILY_SNAPSHOT_DIR = Path("data/daily_snapshots")
DISCLAIMER = "每日快照和赛后复盘只用于纸面观察、模型校准和学习，不构成任何真实投注建议。"


def save_daily_snapshot(
    preview: dict,
    optimizer_result: dict | None = None,
    *,
    snapshot_root: str | Path = DEFAULT_DAILY_SNAPSHOT_DIR,
    prepare_learning: bool = True,
) -> dict:
    selected_date = str(preview.get("selected_date") or preview.get("date") or datetime.now().date().isoformat())
    optimizer = dict(optimizer_result or preview.get("optimizer") or {})
    best_parlay = optimizer.get("best_parlay_summary") or preview.get("best_parlay_summary") or build_best_parlay_summary(optimizer)
    optimizer["best_parlay_summary"] = best_parlay
    preview_payload = {**preview, "optimizer": optimizer, "best_parlay_summary": best_parlay}
    directory = _date_dir(selected_date, snapshot_root)
    directory.mkdir(parents=True, exist_ok=True)
    learning_pack = prepare_daily_learning_pack(preview_payload) if prepare_learning else {}
    data_expansion = build_data_expansion_summary(selected_date)
    pre_match = {
        "snapshot_version": SNAPSHOT_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selected_date": selected_date,
        "provider_used": preview.get("provider_used") or optimizer.get("provider_used"),
        "matches_count": preview.get("matches_count") or optimizer.get("matches_analyzed") or 0,
        "preview": preview_payload,
        "daily_candidates": {
            "daily_single_candidate": best_parlay.get("daily_single_candidate") or best_parlay.get("best_single"),
            "daily_2x1_candidate": best_parlay.get("daily_2x1_candidate") or best_parlay.get("best_2x1"),
            "daily_3x1_candidate": best_parlay.get("daily_3x1_candidate") or best_parlay.get("best_3x1_if_allowed"),
        },
        "best_parlay_summary": best_parlay,
        "data_expansion": data_expansion,
        "learning_pack": learning_pack,
        "disclaimer": DISCLAIMER,
    }
    provider_status = _provider_status(preview, optimizer)
    provider_status["data_expansion"] = data_expansion
    _write_json(directory / "pre_match.json", pre_match)
    _write_json(directory / "provider_status.json", provider_status)
    _write_json(directory / "latest_optimizer.json", optimizer)
    latest_path = Path(snapshot_root) / "latest_snapshot.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(latest_path, {"path": str(directory / "pre_match.json"), "selected_date": selected_date, "created_at": pre_match["created_at"]})
    return {
        "status": "saved",
        "status_zh": "已保存 T+1 赛前快照",
        "snapshot_version": SNAPSHOT_VERSION,
        "selected_date": selected_date,
        "snapshot_dir": str(directory),
        "pre_match_path": str(directory / "pre_match.json"),
        "provider_status_path": str(directory / "provider_status.json"),
        "optimizer_path": str(directory / "latest_optimizer.json"),
        "learning_pack": learning_pack,
        "data_expansion": data_expansion,
        "daily_single": _candidate_label(pre_match["daily_candidates"].get("daily_single_candidate")),
        "daily_2x1": _candidate_label(pre_match["daily_candidates"].get("daily_2x1_candidate")),
        "daily_3x1": _candidate_label(pre_match["daily_candidates"].get("daily_3x1_candidate")),
        "summary_zh": "今日单关、每日纸面2串1、每日纸面3串1和被拒原因已落盘，赛后必须进入复盘。",
        "disclaimer": DISCLAIMER,
    }


def refresh_t1_snapshot(
    provider: str = "auto",
    date: str | None = None,
    *,
    bankroll: float = 10000.0,
    risk_profile: str = "aggressive",
    external_signals_path: str | None = None,
) -> dict:
    from src.intelligence.fusion import build_next_available_preview
    from src.api.routes import _optimizer_result_from_preview  # local import avoids route startup cost until CLI/API call

    preview = build_next_available_preview(
        provider,
        date,
        bankroll=bankroll,
        risk_profile=risk_profile,
        external_signals_path=external_signals_path,
    )
    optimizer = _optimizer_result_from_preview(
        preview,
        {
            "provider": provider,
            "date": preview.get("selected_date") or preview.get("date") or date or "",
            "bankroll": str(bankroll),
            "risk_profile": risk_profile,
            "external_signals": external_signals_path or "",
        },
    )
    saved = save_daily_snapshot(preview, optimizer)
    return {
        "status": "saved",
        "preview": preview,
        "optimizer": optimizer,
        "snapshot_status": saved,
        "summary_zh": "已刷新 T+1 快照并保存赛后学习包。",
        "disclaimer": DISCLAIMER,
    }


def load_latest_snapshot(date: str | None = None, *, snapshot_root: str | Path = DEFAULT_DAILY_SNAPSHOT_DIR) -> dict:
    root = Path(snapshot_root)
    candidates: list[Path]
    if date:
        candidates = [_date_dir(date, root) / "pre_match.json"]
    else:
        candidates = sorted(root.glob("*/pre_match.json"), key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        return {
            "status": "available",
            "status_zh": "已读取本地每日快照",
            "path": str(path),
            "snapshot_dir": str(path.parent),
            "snapshot": payload,
            "selected_date": payload.get("selected_date"),
            "created_at": payload.get("created_at"),
            "summary_zh": "首页可先显示本地快照，再后台刷新真实数据源。",
            "disclaimer": DISCLAIMER,
        }
    return {
        "status": "missing",
        "status_zh": "暂无本地每日快照",
        "selected_date": date,
        "summary_zh": "还没有可复用的 T+1 快照，需要先运行刷新。",
        "disclaimer": DISCLAIMER,
    }


def auto_review_yesterday(
    date: str | None = None,
    *,
    snapshot_root: str | Path = DEFAULT_DAILY_SNAPSHOT_DIR,
    provider: str = "sporttery",
) -> dict:
    target_date = date or _yesterday()
    latest = load_latest_snapshot(target_date, snapshot_root=snapshot_root)
    if latest.get("status") != "available" and not date:
        latest = load_latest_snapshot(None, snapshot_root=snapshot_root)
        target_date = str(latest.get("selected_date") or target_date)
    if latest.get("status") != "available":
        return {
            "status": "missing_snapshot",
            "status_zh": "暂无可复盘的赛前快照",
            "selected_date": target_date,
            "summary_zh": "先生成 T+1 赛前快照，赛后才能自动复盘。",
            "disclaimer": DISCLAIMER,
        }
    snapshot = latest.get("snapshot") or {}
    observations = _snapshot_observations(snapshot)
    results, result_status = _load_sporttery_results(target_date if target_date else snapshot.get("selected_date"), provider=provider)
    if not results:
        review = {
            "status": "pending_results",
            "status_zh": "等待赛果",
            "selected_date": target_date,
            "snapshot_path": latest.get("path"),
            "result_status": result_status,
            "observation_count": len(observations),
            "summary_zh": "已找到赛前快照，但 Sporttery 尚未返回可匹配赛果；不会伪造结果。",
            "disclaimer": DISCLAIMER,
        }
        _write_post_match_review(latest, review, snapshot_root)
        return review
    feedback = build_feedback_from_observations_and_results(observations, results, date=target_date)
    report = feedback.get("report") or {}
    review = {
        "status": "reviewed",
        "status_zh": "已完成昨日自动复盘",
        "selected_date": target_date,
        "snapshot_path": latest.get("path"),
        "result_status": result_status,
        "feedback": feedback,
        "report": report,
        "daily_lane_review": _daily_lane_review(report),
        "combo_learning": report.get("combo_discipline_learning", {}),
        "probability_quality": report.get("probability_quality", {}),
        "paper_roi": report.get("paper_roi"),
        "brier_score": report.get("brier_score"),
        "log_loss": report.get("log_loss"),
        "summary_zh": _auto_review_summary(report),
        "disclaimer": DISCLAIMER,
    }
    review_path = _write_post_match_review(latest, review, snapshot_root)
    feedback_path = _save_feedback_json(feedback, target_date)
    review["post_match_review_path"] = review_path
    review["feedback_path"] = feedback_path
    return review


def build_daily_decision_board(date: str | None = None) -> dict:
    latest = load_latest_snapshot(date)
    snapshot = latest.get("snapshot") or {}
    pre = snapshot.get("preview") or {}
    best = snapshot.get("best_parlay_summary") or {}
    review = _load_post_match_review(snapshot.get("selected_date") or date)
    return {
        "status": "available" if snapshot else "missing",
        "selected_date": snapshot.get("selected_date") or date,
        "snapshot_status": latest,
        "provider_used": snapshot.get("provider_used") or pre.get("provider_used"),
        "matches_count": snapshot.get("matches_count") or pre.get("matches_count") or 0,
        "today_single": _candidate_brief((best.get("daily_single_candidate") or best.get("best_single") or {})),
        "today_2x1": _candidate_brief((best.get("daily_2x1_candidate") or best.get("best_2x1") or {})),
        "today_3x1": _candidate_brief((best.get("daily_3x1_candidate") or best.get("best_3x1_if_allowed") or {})),
        "why_selected_zh": _why_selected(best),
        "main_opposition_zh": _main_opposition(best),
        "yesterday_review": review,
        "play_type_learning": (pre.get("optimizer") or {}).get("play_type_learning_status") or {},
        "strategy_adjustment_status": (pre.get("optimizer") or {}).get("strategy_adjustment_status") or {},
        "data_expansion": snapshot.get("data_expansion") or build_data_expansion_summary(snapshot.get("selected_date") or date),
        "summary_zh": "先看今日三条纸面候选，再看昨日是否打脸模型；这是 T+1 学习闭环主屏。",
        "disclaimer": DISCLAIMER,
    }


def _snapshot_observations(snapshot: dict) -> list[dict]:
    pack = snapshot.get("learning_pack") or {}
    snap = (pack.get("snapshot") or {}) if isinstance(pack, dict) else {}
    rows = snap.get("observations") if isinstance(snap, dict) else None
    if isinstance(rows, list) and rows:
        return rows
    return build_observation_snapshot(snapshot.get("preview") or {}).get("observations", [])


def _load_sporttery_results(date: str | None, *, provider: str = "sporttery") -> tuple[list[dict], dict]:
    if not date:
        return [], {"status": "missing_date", "status_zh": "缺少复盘日期"}
    try:
        matches = SportteryProvider(timeout=10).get_matches(str(date))
    except Exception as exc:
        return [], {"status": "error", "status_zh": "赛果读取失败", "message_zh": str(exc).splitlines()[0][:180]}
    rows = [_match_result_row(match) for match in matches]
    rows = [row for row in rows if row]
    return rows, {
        "status": "loaded" if rows else "empty",
        "status_zh": "已读取 Sporttery 赛果" if rows else "Sporttery 暂未返回赛果",
        "provider": provider,
        "result_count": len(rows),
    }


def _match_result_row(match: Any) -> dict:
    metadata = getattr(match, "metadata", {}) or {}
    home_goals = metadata.get("home_goals")
    away_goals = metadata.get("away_goals")
    if home_goals is None or away_goals is None:
        return {}
    home_goals = int(home_goals)
    away_goals = int(away_goals)
    outcome = "home" if home_goals > away_goals else "away" if away_goals > home_goals else "draw"
    return {
        "date": getattr(match, "date", ""),
        "league": getattr(match, "league", ""),
        "match_id": getattr(match, "match_id", ""),
        "match_no": getattr(match, "match_no", ""),
        "match": f"{getattr(match, 'home_team', '')} vs {getattr(match, 'away_team', '')}".strip(),
        "home_team": getattr(match, "home_team", ""),
        "away_team": getattr(match, "away_team", ""),
        "home_goals": home_goals,
        "away_goals": away_goals,
        "result": {
            "score": f"{home_goals}-{away_goals}",
            "home_goals": home_goals,
            "away_goals": away_goals,
            "actual_outcome": outcome,
            "actual_outcome_zh": {"home": "主胜", "draw": "平", "away": "客胜"}[outcome],
            "actual_handicap_outcome_zh": "未知",
            "total_goals": home_goals + away_goals,
        },
    }


def _daily_lane_review(report: dict) -> dict:
    rows = report.get("rows") or []
    out: dict[str, dict] = {}
    for track in ("daily_single_candidate", "daily_2x1_candidate", "daily_3x1_candidate", "rejected_combo"):
        items = [row for row in rows if row.get("learning_track") == track]
        settled = [row for row in items if row.get("hit") is not None]
        out[track] = {
            "count": len(items),
            "settled_count": len(settled),
            "hit_count": len([row for row in settled if row.get("hit")]),
            "status_zh": "已复盘" if settled else "等待赛果或玩法结果",
            "message_zh": _lane_message(track, items, settled),
        }
    return out


def _lane_message(track: str, items: list[dict], settled: list[dict]) -> str:
    label = {
        "daily_single_candidate": "每日单关",
        "daily_2x1_candidate": "每日2串1",
        "daily_3x1_candidate": "每日3串1",
        "rejected_combo": "被拒组合",
    }.get(track, track)
    if not items:
        return f"{label}没有进入本次快照。"
    if not settled:
        return f"{label}已进入复盘，但赛果或让球结果暂未完整匹配。"
    hits = len([row for row in settled if row.get("hit")])
    return f"{label}已结算 {len(settled)} 条，命中 {hits} 条。"


def _auto_review_summary(report: dict) -> str:
    if not report:
        return "暂无可复盘报告。"
    settled = int(report.get("settled_count") or 0)
    hit_rate = report.get("hit_rate")
    roi = report.get("paper_roi")
    parts = [f"已结算 {settled} 条观察"]
    if hit_rate is not None:
        parts.append(f"命中率 {float(hit_rate):.1%}")
    if roi is not None:
        parts.append(f"纸面 ROI {float(roi):+.1%}")
    combo = report.get("combo_discipline_learning") or {}
    if combo.get("message_zh"):
        parts.append(combo["message_zh"])
    return "；".join(parts) + "。"


def _provider_status(preview: dict, optimizer: dict) -> dict:
    provider_used = preview.get("provider_used") or optimizer.get("provider_used") or "unknown"
    source = preview.get("data_source_status") or {}
    return {
        "status": "real_snapshot" if provider_used == "sporttery" else ("mock_snapshot" if provider_used == "mock" else "snapshot"),
        "status_zh": "已读取真实 Sporttery 快照" if provider_used == "sporttery" else ("暂无真实缓存，使用演示数据" if provider_used == "mock" else "已保存数据源快照"),
        "provider_used": provider_used,
        "matches_count": preview.get("matches_count") or optimizer.get("matches_analyzed") or 0,
        "source": source,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


def _write_post_match_review(latest: dict, review: dict, snapshot_root: str | Path) -> str:
    selected_date = str(review.get("selected_date") or latest.get("selected_date") or datetime.now().date().isoformat())
    path = _date_dir(selected_date, snapshot_root) / "post_match_review.json"
    _write_json(path, review)
    return str(path)


def _load_post_match_review(date: str | None) -> dict:
    if not date:
        return {"status": "missing", "status_zh": "暂无赛后复盘"}
    path = _date_dir(str(date), DEFAULT_DAILY_SNAPSHOT_DIR) / "post_match_review.json"
    if not path.exists():
        return {"status": "missing", "status_zh": "暂无赛后复盘", "path": str(path)}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"status": "error", "status_zh": "赛后复盘读取失败", "path": str(path)}


def _save_feedback_json(feedback: dict, date: str | None) -> str:
    directory = Path("data/learning_feedback")
    directory.mkdir(parents=True, exist_ok=True)
    safe_date = str(date or datetime.now().date().isoformat()).replace("/", "-")
    path = directory / f"auto_feedback_{safe_date}_{datetime.now().strftime('%H%M%S')}.json"
    _write_json(path, feedback)
    return str(path)


def _date_dir(date: str, root: str | Path) -> Path:
    safe = str(date or "unknown").replace("/", "-").replace(" ", "_")
    return Path(root) / safe


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _candidate_label(candidate: dict | None) -> str:
    if not isinstance(candidate, dict) or not candidate:
        return "暂无"
    return str(candidate.get("match") or candidate.get("legs") or candidate.get("message_zh") or "暂无")


def _candidate_brief(candidate: dict) -> dict:
    return {
        "match": candidate.get("match") or candidate.get("legs") or "暂无",
        "play_type": candidate.get("play_type_zh") or candidate.get("play_type") or "",
        "direction": candidate.get("direction") or "",
        "odds": candidate.get("odds"),
        "model_prob": candidate.get("model_prob"),
        "ev": candidate.get("ev"),
        "status": candidate.get("status") or candidate.get("selection_status") or "",
        "reason_zh": candidate.get("selected_reason_zh") or candidate.get("reject_reason") or "",
    }


def _why_selected(best: dict) -> str:
    item = best.get("daily_single_candidate") or best.get("best_single") or {}
    return item.get("selected_reason_zh") or item.get("learning_score_summary_zh") or "优先看赔率覆盖、模型概率和赛后玩法学习。"


def _main_opposition(best: dict) -> str:
    for key in ("daily_2x1_candidate", "daily_3x1_candidate", "best_2x1", "best_3x1_if_allowed"):
        item = best.get(key) or {}
        reason = item.get("opposing_factors_zh") or item.get("reject_reason")
        if reason:
            return reason
    return best.get("no_combo_reason") or "暂无主要反对理由。"


def _yesterday() -> str:
    return (datetime.now().date() - timedelta(days=1)).isoformat()

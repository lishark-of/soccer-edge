from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timedelta
from pathlib import Path

from src.learning.result_feedback import build_feedback_report, load_feedback
from src.learning.ai_hypothesis_review import build_ai_hypothesis_review_history
from src.learning.odds_bucket_calibrator import bayesian_bucket_rate
from src.market.clv import build_clv_history

DEFAULT_FEEDBACK_FILES = [Path("data/fixtures/result_feedback_20260611.json")]
DEFAULT_FEEDBACK_DIR = Path("data/learning_feedback")


def discover_feedback_files(feedback_dir: str | Path | None = None, include_fixtures: bool = True) -> list[Path]:
    files: list[Path] = []
    if include_fixtures:
        files.extend(path for path in DEFAULT_FEEDBACK_FILES if path.exists())
    directory = Path(feedback_dir) if feedback_dir else DEFAULT_FEEDBACK_DIR
    if directory.exists():
        files.extend(sorted(directory.glob("*.json")))
    return _unique_paths(files)


def build_learning_history(feedback_dir: str | Path | None = None, include_fixtures: bool = True) -> dict:
    files = discover_feedback_files(feedback_dir, include_fixtures=include_fixtures)
    reports = []
    errors = []
    for path in files:
        try:
            report = build_feedback_report(load_feedback(path))
            report["source_path"] = str(path)
            reports.append(report)
        except Exception as exc:
            errors.append({"path": str(path), "message_zh": f"读取失败：{str(exc).splitlines()[0]}"})
    rows = [
        {
            **row,
            "date": row.get("date") or report.get("date"),
            "source_path": report.get("source_path"),
        }
        for report in reports
        for row in report.get("rows", []) or []
    ]
    combo_reviews = [row for report in reports for row in report.get("rejected_combo_reviews", []) or []]
    settled = [row for row in rows if row.get("hit") is not None]
    hit_count = len([row for row in settled if row.get("hit")])
    rejected_combo_rows = [row for row in rows if row.get("learning_track") == "rejected_combo"]
    bucket_rows = _aggregate_buckets(settled)
    category_rows = _aggregate_categories(settled)
    play_type_rows = aggregate_play_type_rows(settled)
    competition_rows = aggregate_competition_segment_rows(settled)
    probability_quality = _aggregate_probability_quality(settled)
    calibration_bins = _aggregate_calibration_bins(settled)
    clv_history = _safe_build_clv_history(errors)
    ai_review_history = _safe_build_ai_review_history(errors)
    daily_metrics = _daily_metrics(rows, clv_history.get("rows", []) or [])
    window_metrics = _window_metrics(rows, clv_history.get("rows", []) or [], daily_metrics)
    latest_daily = daily_metrics[0] if daily_metrics else {}
    daily_digest = _daily_digest(latest_daily)
    window_digests = [_window_digest(row) for row in window_metrics]
    daily_report = _daily_report(latest_daily)
    window_reports = [_window_report(row) for row in window_metrics]
    return {
        "history_version": "phase2t_learning_history_v0",
        "files_loaded": len(reports),
        "files": [report.get("source_path") for report in reports],
        "errors": errors,
        "observation_count": len(rows),
        "settled_count": len(settled),
        "hit_count": hit_count,
        "rejected_combo_review_count": len(rejected_combo_rows),
        "combo_discipline_learning": _combo_discipline_history(rejected_combo_rows, combo_reviews),
        "hit_rate": round(hit_count / len(settled), 6) if settled else None,
        "probability_quality": probability_quality,
        "brier_score": probability_quality.get("brier_score"),
        "log_loss": probability_quality.get("log_loss"),
        "clv_history_summary": {
            "files_loaded": clv_history.get("files_loaded", 0),
            "settled_count": clv_history.get("settled_count", 0),
            "average_clv_pct": clv_history.get("average_clv_pct"),
            "summary_zh": clv_history.get("summary_zh", ""),
        },
        "ai_hypothesis_review_history": ai_review_history,
        "calibration_bins": calibration_bins,
        "bucket_rows": bucket_rows,
        "category_rows": category_rows,
        "play_type_rows": play_type_rows,
        "competition_segment_rows": competition_rows,
        "daily_metrics": daily_metrics,
        "window_metrics": window_metrics,
        "latest_daily_summary_zh": _daily_summary_zh(latest_daily),
        "window_summaries_zh": [_window_summary_zh(row) for row in window_metrics],
        "daily_digest": daily_digest,
        "window_digests": window_digests,
        "daily_report": daily_report,
        "window_reports": window_reports,
        "strategy_adjustments": build_strategy_adjustments(
            play_type_rows=play_type_rows,
            competition_rows=competition_rows,
            category_rows=category_rows,
            bucket_rows=bucket_rows,
            combo_discipline=_combo_discipline_history(rejected_combo_rows, combo_reviews),
            probability_quality=probability_quality,
            clv_summary=clv_history,
            ai_review_history=ai_review_history,
            settled_count=len(settled),
        ),
        "lessons": _lessons(bucket_rows, category_rows, play_type_rows, len(settled), probability_quality),
        "next_actions_zh": [
            "每天赛后把观察快照和赛果生成 feedback JSON，放入 data/learning_feedback/。",
            "累计样本不足时，模型更靠近市场概率；高赔率冷门保持降权。",
            "当某个赔率段或玩法长期命中率稳定后，再逐步调整排序权重。",
        ],
        "disclaimer": "累计学习只用于模型校准和纸面复盘，不构成投注建议。",
    }


def build_strategy_adjustments(
    *,
    play_type_rows: list[dict],
    category_rows: list[dict],
    bucket_rows: list[dict],
    combo_discipline: dict,
    probability_quality: dict,
    clv_summary: dict,
    settled_count: int,
    competition_rows: list[dict] | None = None,
    ai_review_history: dict | None = None,
) -> list[dict]:
    adjustments: list[dict] = []
    for row in (ai_review_history or {}).get("factor_rows", []) or []:
        reviewed = int(row.get("reviewed") or 0)
        failed_rate = _float_or_none(row.get("failed_rate"))
        if reviewed >= 5 and failed_rate is not None and failed_rate >= 0.40:
            adjustments.append(
                _strategy_adjustment(
                    key=f"ai_factor_{row.get('ai_factor')}_downweight",
                    label=f"降低AI因子：{row.get('ai_factor_zh') or row.get('ai_factor')}",
                    action="downweight_ai_factor",
                    priority=83,
                    confidence=0.66 if reviewed >= 12 else 0.54,
                    target={"ai_factor": row.get("ai_factor")},
                    reason=f"AI 因子「{row.get('ai_factor_zh') or row.get('ai_factor')}」已有 {reviewed} 条复盘，失败率 {_pct_text(failed_rate)}，不应继续提高同类候选自信。",
                    effect="下一轮同类 AI 因子候选只作辅助解释，不能凭摘要提高排序。",
                )
            )
    for row in competition_rows or []:
        attempts = int(row.get("attempts") or 0)
        roi = _float_or_none(row.get("paper_roi"))
        brier = _float_or_none(row.get("brier_score"))
        if attempts >= 10 and ((roi is not None and roi < -0.03) or (brier is not None and brier > 0.30)):
            adjustments.append(
                _strategy_adjustment(
                    key=f"competition_{row.get('competition_segment')}_downweight",
                    label=f"降低{row.get('label_zh') or row.get('competition_segment')}语境自信",
                    action="downweight_competition_segment",
                    priority=85,
                    confidence=0.64 if attempts >= 30 else 0.52,
                    target={"competition_segment": row.get("competition_segment")},
                    reason=f"{row.get('label_zh') or row.get('competition_segment')} 历史 ROI {_pct_text(roi)}，Brier {brier if brier is not None else 'N/A'}；该赛事语境暂不应和常规联赛同权重。",
                    effect="下一轮同类赛事候选需要更强市场一致性、情报覆盖和稳健价值下沿。",
                )
            )
    for row in play_type_rows:
        attempts = int(row.get("attempts") or 0)
        roi = _float_or_none(row.get("paper_roi"))
        brier = _float_or_none(row.get("brier_score"))
        if attempts >= 10 and ((roi is not None and roi < -0.02) or (brier is not None and brier > 0.28)):
            adjustments.append(
                _strategy_adjustment(
                    key=f"play_type_{row.get('play_type')}_downweight",
                    label=f"降低{row.get('label_zh') or row.get('play_type')}权重",
                    action="downweight_play_type",
                    priority=86,
                    confidence=0.66 if attempts >= 30 else 0.52,
                    target={"play_type": row.get("play_type")},
                    reason=f"{row.get('label_zh') or row.get('play_type')} 历史 ROI {_pct_text(roi)}，Brier {brier if brier is not None else 'N/A'}，不应继续机械刷屏。",
                    effect="优化器应降低该玩法排序分，并要求更多 CLV/赛后样本后再恢复权重。",
                )
            )
    longshot = next((row for row in category_rows if row.get("category") == "longshot_watch"), None)
    if longshot and int(longshot.get("attempts") or 0) >= 5 and int(longshot.get("hits") or 0) <= 0:
        adjustments.append(
            _strategy_adjustment(
                key="longshot_gate_tighten",
                label="收紧高赔率冷门门槛",
                action="tighten_longshot_gate",
                priority=82,
                confidence=0.58,
                target={"odds_min": 6.0},
                reason="冷门观察已有样本但暂未兑现，高赔率不能因为表面 EV 被放大。",
                effect="赔率 >= 6 的候选继续保留观察，但默认不做串联核心。",
            )
        )
    weak_buckets = [row for row in bucket_rows if int(row.get("attempts") or 0) >= 5 and int(row.get("hits") or 0) <= 0]
    if weak_buckets:
        bucket = weak_buckets[0]
        adjustments.append(
            _strategy_adjustment(
                key=f"odds_bucket_{bucket.get('bucket')}_prior_down",
                label=f"降低{bucket.get('bucket_label_zh') or bucket.get('bucket')}先验",
                action="downweight_odds_bucket",
                priority=74,
                confidence=0.54,
                target={"bucket": bucket.get("bucket")},
                reason=f"{bucket.get('bucket_label_zh') or bucket.get('bucket')} 已有 {bucket.get('attempts')} 条样本但暂未命中。",
                effect="下一次同赔率段候选应更靠近市场概率，减少模型自信。",
            )
        )
    combo = combo_discipline or {}
    if int(combo.get("over_strict_candidate_count") or 0) > 0:
        adjustments.append(
            _strategy_adjustment(
                key="review_combo_gate_over_strict",
                label="复查组合门控是否过严",
                action="review_combo_gate",
                priority=70,
                confidence=0.50,
                target={"rule": "combo_gate"},
                reason=f"已有 {combo.get('over_strict_candidate_count')} 条被拒组合赛后全中，需要复查当时被拒原因。",
                effect="不是直接放宽组合，而是定位是相关性、玩法集中、可信度还是命中概率门槛过严。",
            )
        )
    if int(settled_count or 0) < 30:
        adjustments.append(
            _strategy_adjustment(
                key="sample_size_guard",
                label="保持小样本保护",
                action="keep_small_sample_guard",
                priority=68,
                confidence=0.80,
                target={"settled_target": 30},
                reason=f"当前已结算 {settled_count} 条，未到 30 条稳定样本。",
                effect="学习建议只轻微影响排序，不自动大幅调权。",
            )
        )
    avg_clv = _float_or_none((clv_summary or {}).get("average_clv_pct"))
    clv_count = int((clv_summary or {}).get("settled_count") or 0)
    for row in (clv_summary or {}).get("play_type_rows", []) or []:
        attempts = int(row.get("attempts") or 0)
        avg = _float_or_none(row.get("average_clv_pct"))
        if attempts >= 8 and avg is not None and avg < -0.015:
            adjustments.append(
                _strategy_adjustment(
                    key=f"clv_play_type_{row.get('play_type')}_downweight",
                    label=f"降低{row.get('label_zh') or row.get('play_type')}CLV自信",
                    action="downweight_play_type",
                    priority=89,
                    confidence=0.68 if attempts >= 20 else 0.56,
                    target={"play_type": row.get("play_type")},
                    reason=f"{row.get('label_zh') or row.get('play_type')} 已有 {attempts} 条 CLV 样本，平均 CLV {_pct_text(avg)}，说明该玩法赛前价格暂未跑赢收盘市场。",
                    effect="下一轮同玩法候选需要更强市场一致性、稳健 Edge 和情报支撑。",
                )
            )
    for row in (clv_summary or {}).get("bucket_rows", []) or []:
        attempts = int(row.get("attempts") or 0)
        avg = _float_or_none(row.get("average_clv_pct"))
        if attempts >= 8 and avg is not None and avg < -0.015:
            adjustments.append(
                _strategy_adjustment(
                    key=f"clv_bucket_{row.get('signal_bucket') or row.get('bucket')}_downweight",
                    label=f"降低{row.get('bucket_label_zh') or row.get('signal_bucket') or row.get('bucket')}CLV自信",
                    action="downweight_odds_bucket",
                    priority=87,
                    confidence=0.66 if attempts >= 20 else 0.55,
                    target={"bucket": row.get("signal_bucket") or row.get("bucket")},
                    reason=f"{row.get('bucket_label_zh') or row.get('signal_bucket') or row.get('bucket')} 已有 {attempts} 条 CLV 样本，平均 CLV {_pct_text(avg)}，后续同赔率段不能只凭 EV 升级。",
                    effect="下一轮同赔率段候选会被轻量降权，并要求概率下沿仍覆盖赔率。",
                )
            )
    if clv_count >= 10 and avg_clv is not None and avg_clv < 0:
        adjustments.append(
            _strategy_adjustment(
                key="negative_clv_reduce_confidence",
                label="CLV 偏负，降低模型自信",
                action="reduce_confidence_on_negative_clv",
                priority=88,
                confidence=0.70,
                target={"average_clv_pct": avg_clv},
                reason=f"已有 {clv_count} 条 CLV 样本，平均 CLV {_pct_text(avg_clv)}，说明赛前价格判断没有跑赢终盘。",
                effect="高 EV 候选需要更强市场一致性和更高安全边际。",
            )
        )
    if (probability_quality or {}).get("grade_zh") == "需要降权":
        adjustments.append(
            _strategy_adjustment(
                key="probability_quality_downweight",
                label="概率质量偏弱，降低模型概率权重",
                action="downweight_model_probability",
                priority=84,
                confidence=0.64,
                target={"brier_score": probability_quality.get("brier_score"), "log_loss": probability_quality.get("log_loss")},
                reason=probability_quality.get("message_zh") or "Brier/Log Loss 显示概率质量偏弱。",
                effect="模型概率应更靠近市场概率，避免过度自信。",
            )
        )
    return sorted(adjustments, key=lambda row: (row["priority"], row["confidence"]), reverse=True)[:8]


def _strategy_adjustment(key: str, label: str, action: str, priority: int, confidence: float, target: dict, reason: str, effect: str) -> dict:
    return {
        "key": key,
        "label_zh": label,
        "action": action,
        "priority": priority,
        "confidence": round(float(confidence), 6),
        "target": target,
        "reason_zh": reason,
        "expected_effect_zh": effect,
        "apply_mode_zh": "建议进入下一次排序的轻量调权；样本不足时只提示，不大幅改权重。",
    }


def bucket_prior_hit_rates(feedback_dir: str | Path | None = None) -> dict[str, dict]:
    history = build_learning_history(feedback_dir=feedback_dir, include_fixtures=True)
    return {
        row["bucket"]: {
            "hits": row.get("hits", 0),
            "attempts": row.get("attempts", 0),
            "bayesian_hit_rate": row.get("bayesian_hit_rate"),
        }
        for row in history.get("bucket_rows", [])
    }


def probability_bin_hit_rates(feedback_dir: str | Path | None = None) -> dict[str, dict]:
    history = build_learning_history(feedback_dir=feedback_dir, include_fixtures=True)
    return {
        row["probability_bin"]: {
            "attempts": row.get("attempts", 0),
            "hits": row.get("hits", 0),
            "avg_predicted_prob": row.get("avg_predicted_prob"),
            "observed_hit_rate": row.get("observed_hit_rate"),
            "calibration_gap": row.get("calibration_gap"),
            "message_zh": row.get("message_zh", ""),
        }
        for row in history.get("calibration_bins", [])
    }


def _safe_build_clv_history(errors: list[dict] | None = None) -> dict:
    try:
        payload = build_clv_history()
    except Exception as exc:
        if errors is not None:
            errors.append({"path": "data/learning_clv", "message_zh": f"CLV 历史读取失败：{str(exc).splitlines()[0]}"})
        return {
            "files_loaded": 0,
            "settled_count": 0,
            "average_clv_pct": None,
            "summary_zh": "CLV 历史暂不可用，学习历史仍保留命中率、ROI、Brier 和 Log Loss。",
            "rows": [],
        }
    if not isinstance(payload, dict):
        return {
            "files_loaded": 0,
            "settled_count": 0,
            "average_clv_pct": None,
            "summary_zh": "CLV 历史格式异常，暂不参与学习评分。",
            "rows": [],
        }
    return payload


def _safe_build_ai_review_history(errors: list[dict] | None = None) -> dict:
    try:
        payload = build_ai_hypothesis_review_history()
    except Exception as exc:
        if errors is not None:
            errors.append({"path": "data/learning_ai_hypotheses", "message_zh": f"AI 假设历史读取失败：{str(exc).splitlines()[0]}"})
        return {
            "files_loaded": 0,
            "reviewed_count": 0,
            "factor_rows": [],
            "summary_zh": "AI 假设历史暂不可用，学习历史仍保留赛果与 CLV。",
        }
    if not isinstance(payload, dict):
        return {
            "files_loaded": 0,
            "reviewed_count": 0,
            "factor_rows": [],
            "summary_zh": "AI 假设历史格式异常，暂不参与学习评分。",
        }
    return payload


def aggregate_play_type_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        play_type = str(row.get("play_type") or row.get("learning_track") or "unknown")
        label = row.get("play_type_zh") or _play_type_label(play_type)
        item = grouped.setdefault(
            play_type,
            {
                "play_type": play_type,
                "label_zh": label,
                "attempts": 0,
                "hits": 0,
                "brier_sum": 0.0,
                "brier_count": 0,
                "log_loss_sum": 0.0,
                "log_loss_count": 0,
                "paper_staked": 0.0,
                "paper_profit": 0.0,
            },
        )
        item["attempts"] += 1
        item["hits"] += 1 if row.get("hit") else 0
        brier = _float_or_none(row.get("brier_score"))
        if brier is not None:
            item["brier_sum"] += brier
            item["brier_count"] += 1
        log_loss = _float_or_none(row.get("log_loss"))
        if log_loss is not None:
            item["log_loss_sum"] += log_loss
            item["log_loss_count"] += 1
        stake = _float_or_none(row.get("paper_stake"))
        if stake is not None:
            item["paper_staked"] += stake
        profit = _float_or_none(row.get("settlement_profit"))
        if profit is not None:
            item["paper_profit"] += profit
    out = []
    for item in grouped.values():
        attempts = int(item["attempts"])
        hits = int(item["hits"])
        paper_staked = float(item["paper_staked"])
        paper_profit = float(item["paper_profit"])
        hit_rate = hits / attempts if attempts else None
        paper_roi = paper_profit / paper_staked if paper_staked > 0 else None
        avg_brier = item["brier_sum"] / item["brier_count"] if item["brier_count"] else None
        avg_log_loss = item["log_loss_sum"] / item["log_loss_count"] if item["log_loss_count"] else None
        out.append(
            {
                "play_type": item["play_type"],
                "label_zh": item["label_zh"],
                "attempts": attempts,
                "hits": hits,
                "hit_rate": round(hit_rate, 6) if hit_rate is not None else None,
                "paper_staked": round(paper_staked, 2),
                "paper_profit": round(paper_profit, 2),
                "paper_roi": round(paper_roi, 6) if paper_roi is not None else None,
                "brier_score": round(avg_brier, 6) if avg_brier is not None else None,
                "log_loss": round(avg_log_loss, 6) if avg_log_loss is not None else None,
                "sample_quality_zh": _play_type_sample_quality(attempts),
                "message_zh": _play_type_message(item["play_type"], attempts, hits, paper_roi),
                "model_action_zh": _play_type_model_action(item["play_type"], attempts, hit_rate, paper_roi),
            }
        )
    return sorted(out, key=lambda row: (row.get("attempts", 0), row.get("hit_rate") or 0), reverse=True)


def aggregate_competition_segment_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        segment = str(row.get("competition_segment") or "unknown")
        label = row.get("competition_segment_zh") or _competition_segment_label(segment)
        item = grouped.setdefault(
            segment,
            {
                "competition_segment": segment,
                "label_zh": label,
                "attempts": 0,
                "hits": 0,
                "brier_sum": 0.0,
                "brier_count": 0,
                "paper_staked": 0.0,
                "paper_profit": 0.0,
            },
        )
        item["attempts"] += 1
        item["hits"] += 1 if row.get("hit") else 0
        brier = _float_or_none(row.get("brier_score"))
        if brier is not None:
            item["brier_sum"] += brier
            item["brier_count"] += 1
        stake = _float_or_none(row.get("paper_stake"))
        if stake is not None:
            item["paper_staked"] += stake
        profit = _float_or_none(row.get("settlement_profit"))
        if profit is not None:
            item["paper_profit"] += profit
    out = []
    for item in grouped.values():
        attempts = int(item["attempts"])
        hits = int(item["hits"])
        staked = float(item["paper_staked"])
        profit = float(item["paper_profit"])
        roi = profit / staked if staked > 0 else None
        brier = item["brier_sum"] / item["brier_count"] if item["brier_count"] else None
        hit_rate = hits / attempts if attempts else None
        out.append({
            "competition_segment": item["competition_segment"],
            "label_zh": item["label_zh"],
            "attempts": attempts,
            "hits": hits,
            "hit_rate": round(hit_rate, 6) if hit_rate is not None else None,
            "paper_roi": round(roi, 6) if roi is not None else None,
            "brier_score": round(brier, 6) if brier is not None else None,
            "message_zh": _competition_segment_message(item["label_zh"], attempts, roi, brier),
        })
    return sorted(out, key=lambda row: (row.get("attempts", 0), row.get("hit_rate") or 0), reverse=True)


def _aggregate_buckets(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        bucket = row.get("odds_bucket") or (row.get("calibration") or {}).get("bucket", {}).get("bucket") or "unknown"
        grouped.setdefault(bucket, {"attempts": 0, "hits": 0})
        grouped[bucket]["attempts"] += 1
        grouped[bucket]["hits"] += 1 if row.get("hit") else 0
    out = []
    for bucket, stats in sorted(grouped.items()):
        attempts = int(stats["attempts"])
        hits = int(stats["hits"])
        bayes = bayesian_bucket_rate(bucket, hits, attempts)
        out.append({
            "bucket": bucket,
            "bucket_label_zh": bayes.get("bucket_label_zh", bucket),
            "attempts": attempts,
            "hits": hits,
            "raw_hit_rate": round(hits / attempts, 6) if attempts else None,
            "bayesian_hit_rate": bayes.get("posterior_hit_rate"),
            "message_zh": bayes.get("message_zh", ""),
        })
    return out


def _combo_discipline_history(rows: list[dict], reviews: list[dict] | None = None) -> dict:
    reviews = reviews or []
    if not rows and not reviews:
        return {
            "status": "empty",
            "review_count": 0,
            "message_zh": "还没有被拒组合进入赛后学习；组合纪律只能看当天规则，缺少长期验证。",
            "score_bonus": 0,
        }
    high_risk = len([row for row in rows if str(row.get("risk_level") or "").lower() in {"high", "very_high"}])
    reason_count = len([row for row in rows if row.get("reject_reason")])
    settled_reviews = [row for row in reviews if row.get("combo_hit") is not None]
    over_strict = [row for row in settled_reviews if row.get("combo_hit") is True]
    supported = [row for row in settled_reviews if row.get("combo_miss") is True]
    return {
        "status": "tracked",
        "review_count": max(len(rows), len(reviews)),
        "settled_review_count": len(settled_reviews),
        "over_strict_candidate_count": len(over_strict),
        "discipline_supported_count": len(supported),
        "rule_adjustment_summary": _rule_adjustment_summary(reviews),
        "high_risk_count": high_risk,
        "reason_count": reason_count,
        "message_zh": _combo_history_message(max(len(rows), len(reviews)), len(settled_reviews), len(over_strict), len(supported)),
        "score_bonus": 10 if len(settled_reviews) >= 10 and not over_strict else 8 if len(rows) >= 10 else 5,
    }


def _combo_history_message(total: int, settled: int, over_strict: int, supported: int) -> str:
    if settled <= 0:
        return f"累计 {total} 条被拒组合已进入赛后学习；还需要完整赛果来验证拒绝规则。"
    if over_strict > 0:
        return f"累计复盘 {settled} 条被拒组合，其中 {over_strict} 条赛后全中；建议复查这些组合当时被拒的具体规则。"
    return f"累计复盘 {settled} 条被拒组合，其中 {supported} 条未全中；当前组合纪律得到长期样本支持。"


def _rule_adjustment_summary(reviews: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for review in reviews or []:
        for item in review.get("rule_adjustment_suggestions") or []:
            rule = item.get("rule") or "unknown"
            grouped.setdefault(rule, {
                "rule": rule,
                "label_zh": item.get("label_zh") or rule,
                "suggestion_zh": item.get("suggestion_zh") or "",
                "count": 0,
            })
            grouped[rule]["count"] += 1
    return sorted(grouped.values(), key=lambda row: row.get("count", 0), reverse=True)


def _aggregate_categories(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        category = row.get("signal_category") or "unknown"
        label = row.get("signal_category_zh") or category
        grouped.setdefault(category, {"category": category, "label_zh": label, "attempts": 0, "hits": 0})
        grouped[category]["attempts"] += 1
        grouped[category]["hits"] += 1 if row.get("hit") else 0
    out = []
    for item in grouped.values():
        attempts = int(item["attempts"])
        hits = int(item["hits"])
        out.append({
            **item,
            "hit_rate": round(hits / attempts, 6) if attempts else None,
            "message_zh": _category_message(item["category"], hits, attempts),
        })
    return sorted(out, key=lambda x: (x.get("hit_rate") is not None, x.get("hit_rate") or 0), reverse=True)


def _aggregate_probability_quality(rows: list[dict]) -> dict:
    scored = [row for row in rows if row.get("brier_score") is not None and row.get("log_loss") is not None]
    if not scored:
        return {
            "status": "empty",
            "sample_count": 0,
            "brier_score": None,
            "log_loss": None,
            "grade_zh": "暂无",
            "message_zh": "暂无可评分概率样本。",
        }
    brier = sum(float(row.get("brier_score") or 0.0) for row in scored) / len(scored)
    log_loss = sum(float(row.get("log_loss") or 0.0) for row in scored) / len(scored)
    return {
        "status": "ok",
        "sample_count": len(scored),
        "brier_score": round(brier, 6),
        "log_loss": round(log_loss, 6),
        "grade_zh": _probability_grade(brier, log_loss, len(scored)),
        "message_zh": _probability_message(brier, log_loss, len(scored)),
    }


def _probability_grade(brier: float, log_loss: float, sample_count: int) -> str:
    if sample_count < 30:
        return "样本不足"
    if brier <= 0.18 and log_loss <= 0.55:
        return "较好"
    if brier <= 0.24 and log_loss <= 0.70:
        return "一般"
    return "需要降权"


def _probability_message(brier: float, log_loss: float, sample_count: int) -> str:
    if sample_count < 30:
        return f"当前只有 {sample_count} 条概率样本，Brier/Log Loss 只能提示方向，不能当稳定结论。"
    if brier <= 0.18 and log_loss <= 0.55:
        return "概率质量暂时较好，但仍需继续累计不同赔率段样本。"
    if brier <= 0.24 and log_loss <= 0.70:
        return "概率质量一般，建议继续用市场概率和赔率段先验约束模型自信。"
    return "概率质量偏弱，模型需要降低自信并复核特征和冷门降权。"


def _aggregate_calibration_bins(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        prob = _probability_or_none(row.get("calibrated_prob"))
        if prob is None:
            continue
        lower = int(prob * 10) * 10
        if lower >= 100:
            lower = 90
        upper = lower + 10
        label = f"{lower}-{upper}%"
        grouped.setdefault(label, {"label": label, "lower": lower, "upper": upper, "attempts": 0, "hits": 0, "prob_sum": 0.0})
        grouped[label]["attempts"] += 1
        grouped[label]["hits"] += 1 if row.get("hit") else 0
        grouped[label]["prob_sum"] += prob
    out = []
    for label, item in sorted(grouped.items(), key=lambda kv: kv[1]["lower"]):
        attempts = int(item["attempts"])
        hits = int(item["hits"])
        avg_prob = item["prob_sum"] / attempts if attempts else None
        observed = hits / attempts if attempts else None
        gap = observed - avg_prob if observed is not None and avg_prob is not None else None
        out.append(
            {
                "probability_bin": label,
                "attempts": attempts,
                "hits": hits,
                "avg_predicted_prob": round(avg_prob, 6) if avg_prob is not None else None,
                "observed_hit_rate": round(observed, 6) if observed is not None else None,
                "calibration_gap": round(gap, 6) if gap is not None else None,
                "message_zh": _calibration_bin_message(attempts, gap),
            }
        )
    return out


def _calibration_bin_message(attempts: int, gap: float | None) -> str:
    if attempts < 10:
        return "样本很少，只作提示，不调大权重。"
    if gap is None:
        return "暂无校准差。"
    if gap < -0.08:
        return "实际命中低于预测，后续应降权该概率段。"
    if gap > 0.08:
        return "实际命中高于预测，可继续观察是否稳定。"
    return "预测与实际较接近，继续累计样本。"


def _probability_or_none(value) -> float | None:
    try:
        p = float(value)
    except (TypeError, ValueError):
        return None
    if p < 0 or p > 1:
        return None
    return p


def _category_message(category: str, hits: int, attempts: int) -> str:
    if attempts <= 0:
        return "暂无样本。"
    if category == "longshot_watch" and hits == 0:
        return "冷门观察暂未兑现，继续保持纸面跟踪和串联禁入。"
    if hits == 0:
        return "当前样本未命中，排序需要保守。"
    return "已有命中样本，但仍需继续累计。"


def _play_type_label(play_type: str) -> str:
    labels = {
        "had": "胜平负",
        "hhad": "让球胜平负",
        "total_goals": "总进球",
        "correct_score": "比分",
        "single": "单关",
        "parlay_2x1": "2串1",
        "parlay_3x1": "3串1",
        "rejected_combo": "被拒组合",
        "unknown": "未知玩法",
    }
    return labels.get(str(play_type or "unknown"), str(play_type or "未知玩法"))


def _competition_segment_label(segment: str) -> str:
    return {
        "national_team": "国家队/国际赛",
        "friendly": "友谊赛",
        "cup": "杯赛/淘汰赛",
        "club_league": "俱乐部联赛",
        "unknown": "未知赛事类型",
    }.get(str(segment or "unknown"), str(segment or "未知赛事类型"))


def _competition_segment_message(label: str, attempts: int, roi: float | None, brier: float | None) -> str:
    if attempts < 10:
        return f"{label} 只有 {attempts} 条样本，只作语境提示，不大幅调权。"
    if roi is not None and roi < -0.03:
        return f"{label} 纸面 ROI 偏弱，下一轮同类赛事需要更严格的市场一致性和情报覆盖。"
    if brier is not None and brier > 0.30:
        return f"{label} Brier 偏高，说明该语境下概率质量需要降权。"
    return f"{label} 已开始累计语境样本，继续结合 CLV 和 Brier 验证。"


def _play_type_sample_quality(attempts: int) -> str:
    if attempts >= 80:
        return "样本较充分"
    if attempts >= 30:
        return "样本可参考"
    if attempts >= 10:
        return "样本偏少"
    return "样本很少"


def _play_type_message(play_type: str, attempts: int, hits: int, paper_roi: float | None) -> str:
    label = _play_type_label(play_type)
    if attempts <= 0:
        return f"{label} 暂无已结算样本。"
    if attempts < 10:
        return f"{label} 只有 {attempts} 条样本，只能提示方向，不能据此加大权重。"
    if paper_roi is not None and paper_roi < -0.05:
        return f"{label} 纸面 ROI 偏弱，后续排序应先降权或复核赔率段。"
    if hits <= 0:
        return f"{label} 当前未命中，不能继续凭当天 EV 放大权重。"
    return f"{label} 已有可复盘样本，下一步看命中率、ROI、Brier/Log Loss 是否同向支持。"


def _play_type_model_action(play_type: str, attempts: int, hit_rate: float | None, paper_roi: float | None) -> str:
    label = _play_type_label(play_type)
    if attempts < 10:
        return f"{label} 暂不调权，继续累计赛后样本。"
    if paper_roi is not None and paper_roi < 0:
        return f"{label} 先降权观察，避免玩法偏置继续放大。"
    if hit_rate is not None and hit_rate >= 0.55:
        return f"{label} 可保留观察，但还要用 CLV 和概率校准确认。"
    return f"{label} 保守保留，等待更多赛果和收盘赔率验证。"


def _play_type_lesson(play_type_rows: list[dict]) -> str:
    if not play_type_rows:
        return ""
    top = play_type_rows[0]
    label = top.get("label_zh") or top.get("play_type") or "某玩法"
    attempts = int(top.get("attempts") or 0)
    if attempts < 10:
        return f"当前最常出现的玩法是 {label}，但样本只有 {attempts} 条，不足以证明它优于其他玩法。"
    weak = [row for row in play_type_rows if (row.get("paper_roi") is not None and float(row.get("paper_roi")) < 0)]
    if weak:
        return f"{weak[0].get('label_zh') or '某玩法'} 的纸面 ROI 偏弱，后续需要降权或复核为什么模型仍频繁选择它。"
    return f"玩法维度已开始累计：{label} 样本最多。后续会用命中率、ROI 和 Brier/Log Loss 共同判断是否存在玩法偏置。"


def _float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _lessons(
    bucket_rows: list[dict],
    category_rows: list[dict],
    play_type_rows: list[dict],
    settled_count: int,
    probability_quality: dict | None = None,
) -> list[str]:
    if settled_count <= 0:
        return ["暂无可结算样本，模型不会假装已经学习。"]
    lessons = [f"累计已结算观察 {settled_count} 条，样本仍偏少，先做保守校准。"]
    longshot = next((row for row in category_rows if row.get("category") == "longshot_watch"), None)
    if longshot and not longshot.get("hits"):
        lessons.append("冷门观察未兑现，继续从 Top 最佳中降权，只保留纸面跟踪。")
    weak_buckets = [row for row in bucket_rows if row.get("attempts", 0) and not row.get("hits")]
    if weak_buckets:
        lessons.append("未命中赔率段会被贝叶斯先验拉回，避免单次高 EV 过度影响排序。")
    play_lesson = _play_type_lesson(play_type_rows)
    if play_lesson:
        lessons.append(play_lesson)
    if probability_quality and probability_quality.get("message_zh"):
        lessons.append(probability_quality["message_zh"])
    return lessons


def _daily_metrics(rows: list[dict], clv_rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        date_key = _date_key(row.get("date"))
        if not date_key:
            continue
        grouped.setdefault(date_key, []).append(row)
    clv_grouped: dict[str, list[dict]] = {}
    for row in clv_rows or []:
        date_key = _date_key(row.get("date"))
        if not date_key:
            continue
        clv_grouped.setdefault(date_key, []).append(row)
    metrics = []
    for date_key in sorted(grouped.keys(), reverse=True):
        metrics.append(_metrics_row(date_key, grouped[date_key], clv_grouped.get(date_key, []), label_zh="当日"))
    return metrics


def _window_metrics(rows: list[dict], clv_rows: list[dict], daily_metrics: list[dict]) -> list[dict]:
    dated_rows = [( _date_obj(row.get("date")), row) for row in rows]
    dated_rows = [(day, row) for day, row in dated_rows if day is not None]
    dated_clv = [(_date_obj(row.get("date")), row) for row in clv_rows or []]
    dated_clv = [(day, row) for day, row in dated_clv if day is not None]
    if dated_rows:
        latest_day = max(day for day, _ in dated_rows)
    elif daily_metrics:
        latest_day = _date_obj(daily_metrics[0].get("date"))
    else:
        latest_day = None
    windows = [
        ("all_time", "累计", None),
        ("last_7_days", "近7天", 7),
        ("last_30_days", "近30天", 30),
    ]
    out = []
    for key, label, days in windows:
        if days is None or latest_day is None:
            row_subset = [row for _, row in dated_rows] if dated_rows else rows
            clv_subset = [row for _, row in dated_clv]
            start = min((day for day, _ in dated_rows), default=None)
            end = max((day for day, _ in dated_rows), default=None)
        else:
            start_day = latest_day - timedelta(days=days - 1)
            row_subset = [row for day, row in dated_rows if start_day <= day <= latest_day]
            clv_subset = [row for day, row in dated_clv if start_day <= day <= latest_day]
            start = start_day
            end = latest_day
        out.append(_metrics_row(key, row_subset, clv_subset, label_zh=label, date_from=start, date_to=end))
    return out


def _metrics_row(
    key: str,
    rows: list[dict],
    clv_rows: list[dict],
    *,
    label_zh: str,
    date_from: date_cls | None = None,
    date_to: date_cls | None = None,
) -> dict:
    settled = [row for row in rows if row.get("hit") is not None]
    scored = [row for row in settled if row.get("brier_score") is not None and row.get("log_loss") is not None]
    hit_count = len([row for row in settled if row.get("hit")])
    paper_staked = sum(float(row.get("paper_stake") or 0.0) for row in settled if row.get("settlement_profit") is not None)
    paper_profit = sum(float(row.get("settlement_profit") or 0.0) for row in settled if row.get("settlement_profit") is not None)
    clv_settled = [row for row in clv_rows if row.get("clv_pct") is not None]
    avg_brier = sum(float(row.get("brier_score") or 0.0) for row in scored) / len(scored) if scored else None
    avg_log_loss = sum(float(row.get("log_loss") or 0.0) for row in scored) / len(scored) if scored else None
    avg_clv = sum(float(row.get("clv_pct") or 0.0) for row in clv_settled) / len(clv_settled) if clv_settled else None
    return {
        "window": key,
        "label_zh": label_zh,
        "date": key if label_zh == "当日" else None,
        "date_from": start_date(date_from),
        "date_to": start_date(date_to),
        "observation_count": len(rows),
        "settled_count": len(settled),
        "hit_count": hit_count,
        "hit_rate": round(hit_count / len(settled), 6) if settled else None,
        "paper_staked": round(paper_staked, 2),
        "paper_profit": round(paper_profit, 2),
        "paper_roi": round(paper_profit / paper_staked, 6) if paper_staked > 0 else None,
        "brier_score": round(avg_brier, 6) if avg_brier is not None else None,
        "log_loss": round(avg_log_loss, 6) if avg_log_loss is not None else None,
        "clv_settled_count": len(clv_settled),
        "average_clv_pct": round(avg_clv, 6) if avg_clv is not None else None,
        "play_type_rows": aggregate_play_type_rows(settled),
        "message_zh": _metrics_message(label_zh, len(settled), paper_staked, avg_clv),
    }


def _metrics_message(label_zh: str, settled_count: int, paper_staked: float, avg_clv: float | None) -> str:
    if settled_count <= 0:
        return f"{label_zh}暂无可结算样本，先继续记录赛果和收盘赔率。"
    if paper_staked <= 0:
        return f"{label_zh}已能计算概率质量，但还没有可用纸面投入口径，ROI 仅作单位收益参考。"
    if avg_clv is None:
        return f"{label_zh}已有收益和概率指标，但 CLV 仍缺收盘赔率样本。"
    return f"{label_zh}已同时覆盖命中率、ROI、Brier/Log Loss 和 CLV，可继续做阶段复盘。"


def _daily_summary_zh(row: dict) -> str:
    if not row:
        return "今日赛后学习摘要：还没有可用结算样本。"
    return (
        f"今日赛后学习：{row.get('date') or '未知日期'}，"
        f"结算 {row.get('settled_count', 0)} 条，"
        f"命中率 {_pct(row.get('hit_rate'))}，"
        f"纸面 ROI {_signed_pct(row.get('paper_roi'))}，"
        f"Brier {_metric(row.get('brier_score'))}，"
        f"Log Loss {_metric(row.get('log_loss'))}，"
        f"CLV {_signed_pct(row.get('average_clv_pct'))}。"
    )


def _daily_digest(row: dict) -> dict:
    if not row:
        return {
            "headline_zh": "今日赛后复盘",
            "status": "pending",
            "status_zh": "待累计",
            "verdict_zh": "今天还没有可结算样本，先不要把单日感觉当成长期结论。",
            "summary_zh": "今日赛后学习摘要：还没有可用结算样本。",
            "metrics_line_zh": "命中率 N/A · ROI N/A · Brier N/A · Log Loss N/A · CLV N/A",
            "next_step_zh": "先补赛果和收盘赔率，再看 Brier、Log Loss、ROI 和 CLV 是否同向改善。",
        }
    settled = int(row.get("settled_count") or 0)
    roi = row.get("paper_roi")
    clv = row.get("average_clv_pct")
    if settled < 3:
        verdict = "单日样本还很少，先看方向，不下长期定论。"
        status_zh = "样本偏少"
    elif roi is not None and float(roi) > 0:
        verdict = "单日纸面结果偏正，但仍要结合更多日期看稳定性。"
        status_zh = "当日偏正"
    else:
        verdict = "单日纸面结果偏弱，不代表模型失效，先复核赔率段和冷门降权。"
        status_zh = "当日偏弱"
    next_step = (
        "优先补收盘赔率，确认 CLV 是否支持今天的赛前价格判断。"
        if clv is None
        else "继续累计不同赔率段样本，判断今天的结果是偶然波动还是长期偏差。"
    )
    return {
        "headline_zh": f"今日赛后复盘 · {row.get('date') or '未知日期'}",
        "status": "active",
        "status_zh": status_zh,
        "verdict_zh": verdict,
        "summary_zh": _daily_summary_zh(row),
        "metrics_line_zh": _metrics_line_zh(row, include_clv=True),
        "next_step_zh": next_step,
    }


def _window_summary_zh(row: dict) -> str:
    if not row:
        return "区间学习摘要：暂无数据。"
    return (
        f"{row.get('label_zh') or row.get('window') or '区间'}："
        f"结算 {row.get('settled_count', 0)} 条，"
        f"命中率 {_pct(row.get('hit_rate'))}，"
        f"纸面 ROI {_signed_pct(row.get('paper_roi'))}，"
        f"Brier {_metric(row.get('brier_score'))}，"
        f"Log Loss {_metric(row.get('log_loss'))}。"
    )


def _window_digest(row: dict) -> dict:
    if not row:
        return {
            "window": "unknown",
            "headline_zh": "区间复盘",
            "status_zh": "暂无数据",
            "summary_zh": "区间学习摘要：暂无数据。",
            "metrics_line_zh": "命中率 N/A · ROI N/A · Brier N/A · Log Loss N/A",
            "next_step_zh": "继续累计赛果、CLV 和被拒组合复盘。",
        }
    settled = int(row.get("settled_count") or 0)
    clv_count = int(row.get("clv_settled_count") or 0)
    if settled < 10:
        status_zh = "样本偏少"
        next_step = "优先累计更多已结算样本，再决定是否调整排序或串联纪律。"
    elif clv_count <= 0:
        status_zh = "缺少 CLV"
        next_step = "补收盘赔率样本，避免只看赛果而忽略价格是否跑赢市场。"
    else:
        status_zh = "可继续复盘"
        next_step = "结合 CLV、Brier 和 ROI 看哪些赔率段值得继续观察，哪些该降权。"
    return {
        "window": row.get("window"),
        "headline_zh": f"{row.get('label_zh') or row.get('window') or '区间'}复盘",
        "status_zh": status_zh,
        "summary_zh": _window_summary_zh(row),
        "metrics_line_zh": _metrics_line_zh(row, include_clv=False),
        "next_step_zh": next_step,
    }


def _daily_report(row: dict) -> dict:
    digest = _daily_digest(row)
    settled = int(row.get("settled_count") or 0) if row else 0
    clv = row.get("average_clv_pct") if row else None
    roi = row.get("paper_roi") if row else None
    if not row:
        paragraphs = [
            "今天还没有形成可复盘的已结算样本，系统不会假装已经学到结论。",
            "先保存赛前观察快照，赛后补比分和收盘赔率，再看命中率、概率质量和 CLV 是否同向变化。",
        ]
    else:
        paragraphs = [
            digest.get("summary_zh", ""),
            _daily_report_interpretation(settled, roi, clv),
            digest.get("next_step_zh", ""),
        ]
    return {
        "headline_zh": digest.get("headline_zh", "今日赛后复盘"),
        "status_zh": digest.get("status_zh", "待累计"),
        "verdict_zh": digest.get("verdict_zh", "先累计样本。"),
        "metrics_line_zh": digest.get("metrics_line_zh", "命中率 N/A · ROI N/A · Brier N/A · Log Loss N/A · CLV N/A"),
        "paragraphs_zh": [line for line in paragraphs if line],
        "next_step_zh": digest.get("next_step_zh", "继续累计赛果与收盘赔率。"),
    }


def _window_report(row: dict) -> dict:
    digest = _window_digest(row)
    settled = int(row.get("settled_count") or 0) if row else 0
    clv_count = int(row.get("clv_settled_count") or 0) if row else 0
    roi = row.get("paper_roi") if row else None
    paragraphs = [
        digest.get("summary_zh", "区间学习摘要：暂无数据。"),
        _window_report_interpretation(settled, roi, clv_count),
        digest.get("next_step_zh", "继续累计赛果、CLV 和被拒组合复盘。"),
    ]
    return {
        "window": row.get("window") if row else "unknown",
        "headline_zh": digest.get("headline_zh", "区间复盘"),
        "status_zh": digest.get("status_zh", "暂无数据"),
        "metrics_line_zh": digest.get("metrics_line_zh", "命中率 N/A · ROI N/A · Brier N/A · Log Loss N/A"),
        "paragraphs_zh": [line for line in paragraphs if line],
        "next_step_zh": digest.get("next_step_zh", "继续累计赛果、CLV 和被拒组合复盘。"),
    }


def _daily_report_interpretation(settled: int, roi, clv) -> str:
    if settled < 3:
        return "单日样本仍很少，只能看方向，不能把今天的输赢直接当成模型长期水平。"
    if roi is not None and float(roi) > 0 and clv is not None and float(clv) > 0:
        return "今天纸面收益和价格优势方向一致，说明赛前判断暂时没有明显落后于市场。"
    if roi is not None and float(roi) > 0:
        return "今天纸面收益偏正，但还要看更多日期与 CLV，避免只被单日赛果鼓励。"
    if clv is not None and float(clv) > 0:
        return "今天赛果未必理想，但如果 CLV 偏正，说明赛前价格判断可能仍有价值。"
    return "今天纸面结果或价格优势偏弱，更适合回看赔率段、冷门降权和临场信息缺口。"


def _window_report_interpretation(settled: int, roi, clv_count: int) -> str:
    if settled < 10:
        return "区间样本仍偏少，当前更适合继续累计，而不是急着调整模型权重。"
    if clv_count <= 0:
        return "这个区间已经能看赛果和概率质量，但还缺 CLV，暂时不能确认赛前价格是否真的跑赢市场。"
    if roi is not None and float(roi) > 0:
        return "这个区间的纸面收益为正，下一步要看它是否也被 CLV 和概率校准共同支持。"
    return "这个区间收益偏弱时，更要看 CLV 和概率质量，避免只根据赛果做过度反应。"


def _metrics_line_zh(row: dict, *, include_clv: bool) -> str:
    parts = [
        f"命中率 {_pct(row.get('hit_rate'))}",
        f"ROI {_signed_pct(row.get('paper_roi'))}",
        f"Brier {_metric(row.get('brier_score'))}",
        f"Log Loss {_metric(row.get('log_loss'))}",
    ]
    if include_clv:
        parts.append(f"CLV {_signed_pct(row.get('average_clv_pct'))}")
    return " · ".join(parts)


def _metric(value) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "N/A"


def _pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _signed_pct(value) -> str:
    try:
        return f"{float(value) * 100:+.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _date_key(value) -> str | None:
    day = _date_obj(value)
    return day.isoformat() if day else None


def _date_obj(value) -> date_cls | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def start_date(value: date_cls | None) -> str | None:
    return value.isoformat() if value else None


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen = set()
    out = []
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out

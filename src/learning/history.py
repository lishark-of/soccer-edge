from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timedelta
from pathlib import Path

from src.learning.result_feedback import build_feedback_report, load_feedback
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
    probability_quality = _aggregate_probability_quality(settled)
    calibration_bins = _aggregate_calibration_bins(settled)
    clv_history = build_clv_history()
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
        "calibration_bins": calibration_bins,
        "bucket_rows": bucket_rows,
        "category_rows": category_rows,
        "daily_metrics": daily_metrics,
        "window_metrics": window_metrics,
        "latest_daily_summary_zh": _daily_summary_zh(latest_daily),
        "window_summaries_zh": [_window_summary_zh(row) for row in window_metrics],
        "daily_digest": daily_digest,
        "window_digests": window_digests,
        "daily_report": daily_report,
        "window_reports": window_reports,
        "lessons": _lessons(bucket_rows, category_rows, len(settled), probability_quality),
        "next_actions_zh": [
            "每天赛后把观察快照和赛果生成 feedback JSON，放入 data/learning_feedback/。",
            "累计样本不足时，模型更靠近市场概率；高赔率冷门保持降权。",
            "当某个赔率段长期命中率稳定后，再逐步调整排序权重。",
        ],
        "disclaimer": "累计学习只用于模型校准和纸面复盘，不构成投注建议。",
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


def _lessons(bucket_rows: list[dict], category_rows: list[dict], settled_count: int, probability_quality: dict | None = None) -> list[str]:
    if settled_count <= 0:
        return ["暂无可结算样本，模型不会假装已经学习。"]
    lessons = [f"累计已结算观察 {settled_count} 条，样本仍偏少，先做保守校准。"]
    longshot = next((row for row in category_rows if row.get("category") == "longshot_watch"), None)
    if longshot and not longshot.get("hits"):
        lessons.append("冷门观察未兑现，继续从 Top 最佳中降权，只保留纸面跟踪。")
    weak_buckets = [row for row in bucket_rows if row.get("attempts", 0) and not row.get("hits")]
    if weak_buckets:
        lessons.append("未命中赔率段会被贝叶斯先验拉回，避免单次高 EV 过度影响排序。")
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

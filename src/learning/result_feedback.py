from __future__ import annotations

import json
import math
from pathlib import Path

from src.learning.competition_segments import classify_competition_segment
from src.learning.odds_bucket_calibrator import bayesian_bucket_rate
from src.learning.signal_classifier import classify_signal


def load_feedback(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_observation_hit(observation: dict, match_result: dict) -> bool | None:
    play = str(observation.get("play_type") or "")
    direction = str(observation.get("direction") or observation.get("outcome_label") or "")
    actual = str(match_result.get("actual_outcome_zh") or match_result.get("actual_outcome") or "")
    if play in {"had", "胜平负"}:
        return direction in {actual, _outcome_zh(actual)}
    if play in {"hhad", "让球胜平负"}:
        handicap_result = str(match_result.get("actual_handicap_outcome_zh") or "").strip()
        if not handicap_result or handicap_result == "未知":
            return None
        return direction == handicap_result
    if play == "total_goals":
        return direction.endswith(str(match_result.get("total_goals")))
    if play == "correct_score":
        return direction.endswith(str(match_result.get("score")))
    return None


def build_feedback_report(feedback: dict) -> dict:
    matches = feedback.get("matches", []) or []
    rows = []
    bucket_stats: dict[str, dict] = {}
    for match in matches:
        result = match.get("result", {}) or {}
        for obs in match.get("observations", []) or []:
            segment = classify_competition_segment({**match, **obs})
            hit = evaluate_observation_hit(obs, result)
            classification = classify_signal(obs, match.get("intelligence_score"), use_history=False)
            probability_scores = _probability_scores(classification.get("calibrated_prob"), hit)
            settlement = _settlement_scores(obs, hit)
            bucket = classification.get("odds_bucket") or "unknown"
            bucket_stats.setdefault(bucket, {"attempts": 0, "hits": 0})
            if hit is not None:
                bucket_stats[bucket]["attempts"] += 1
                bucket_stats[bucket]["hits"] += 1 if hit else 0
            rows.append({
                "date": match.get("date") or feedback.get("date"),
                "league": obs.get("league") or match.get("league"),
                "match": match.get("match") or f"{match.get('home_team','')} vs {match.get('away_team','')}",
                **segment,
                "play_type": obs.get("play_type"),
                "direction": obs.get("direction") or obs.get("outcome_label"),
                "odds": obs.get("odds") or obs.get("official_odds"),
                "model_prob": obs.get("model_prob"),
                "market_prob": obs.get("market_prob"),
                "ev": obs.get("ev"),
                "learning_track": obs.get("learning_track") or "observation",
                "status": obs.get("status"),
                "reject_reason": obs.get("reject_reason"),
                "risk_level": obs.get("risk_level"),
                "hit": hit,
                **settlement,
                **probability_scores,
                **classification,
            })
    settled = [row for row in rows if row.get("hit") is not None]
    hits = len([row for row in settled if row.get("hit")])
    attempts = len(settled)
    settled_financial = [row for row in settled if row.get("settlement_profit") is not None]
    total_staked = sum(float(row.get("paper_stake") or 0.0) for row in settled_financial)
    total_profit = sum(float(row.get("settlement_profit") or 0.0) for row in settled_financial)
    longshots = [row for row in settled if row.get("signal_category") == "longshot_watch"]
    longshot_hits = len([row for row in longshots if row.get("hit")])
    rejected_combo_rows = [row for row in rows if row.get("learning_track") == "rejected_combo"]
    rejected_combo_reviews = feedback.get("rejected_combo_reviews", []) or []
    probability_quality = _probability_quality(settled)
    return {
        "feedback_version": "phase2t_small_sample_feedback_v0",
        "date": feedback.get("date"),
        "matches_count": len(matches),
        "observation_count": len(rows),
        "settled_count": attempts,
        "hit_count": hits,
        "hit_rate": round(hits / attempts, 6) if attempts else None,
        "paper_staked": round(total_staked, 2),
        "paper_profit": round(total_profit, 2),
        "paper_roi": round(total_profit / total_staked, 6) if total_staked > 0 else None,
        "longshot_count": len(longshots),
        "longshot_hit_count": longshot_hits,
        "longshot_hit_rate": round(longshot_hits / len(longshots), 6) if longshots else None,
        "rejected_combo_review_count": len(rejected_combo_rows),
        "rejected_combo_reviews": rejected_combo_reviews,
        "combo_discipline_learning": _combo_discipline_learning(rejected_combo_rows, rejected_combo_reviews),
        "probability_quality": probability_quality,
        "brier_score": probability_quality.get("brier_score"),
        "log_loss": probability_quality.get("log_loss"),
        "calibration_bins": _calibration_bins(settled),
        "bucket_stats": bucket_stats,
        "bucket_rows": _bucket_rows(bucket_stats),
        "rows": rows,
        "main_lesson_zh": _lesson(attempts, hits, longshots, longshot_hits),
        "next_model_action_zh": _next_action(probability_quality, longshots, longshot_hits),
        "disclaimer": "赛果反馈只用于模型校准和复盘，不构成任何真实投注建议。",
    }


def _bucket_rows(bucket_stats: dict[str, dict]) -> list[dict]:
    rows = []
    for bucket, stats in sorted(bucket_stats.items()):
        attempts = int(stats.get("attempts") or 0)
        hits = int(stats.get("hits") or 0)
        calibrated = bayesian_bucket_rate(bucket, hits, attempts)
        rows.append({
            "bucket": bucket,
            "bucket_label_zh": calibrated.get("bucket_label_zh", bucket),
            "attempts": attempts,
            "hits": hits,
            "raw_hit_rate": round(hits / attempts, 6) if attempts else None,
            "bayesian_hit_rate": calibrated.get("posterior_hit_rate"),
            "message_zh": calibrated.get("message_zh", ""),
        })
    return rows


def _combo_discipline_learning(rows: list[dict], reviews: list[dict] | None = None) -> dict:
    reviews = reviews or []
    if not rows and not reviews:
        return {
            "status": "empty",
            "review_count": 0,
            "message_zh": "暂无被拒组合复盘样本；组合纪律还不能从赛后结果中验证。",
        }
    high_risk = len([row for row in rows if str(row.get("risk_level") or "").lower() in {"high", "very_high"}])
    settled_reviews = [row for row in reviews if row.get("combo_hit") is not None]
    over_strict = [row for row in settled_reviews if row.get("combo_hit") is True]
    supported = [row for row in settled_reviews if row.get("combo_miss") is True]
    return {
        "status": "tracked",
        "review_count": max(len(rows), len(reviews)),
        "settled_review_count": len(settled_reviews),
        "over_strict_candidate_count": len(over_strict),
        "discipline_supported_count": len(supported),
        "high_risk_count": high_risk,
        "message_zh": _combo_discipline_message(len(rows), len(settled_reviews), len(over_strict), len(supported)),
        "next_action_zh": "继续把被拒 2串1/3串1 与赛后结果一起保存，观察哪些拒绝原因长期有效或过严。",
    }


def _combo_discipline_message(total: int, settled: int, over_strict: int, supported: int) -> str:
    if settled <= 0:
        return f"已纳入 {total} 条被拒组合复盘样本，但还没有完整赛果可判断拒绝规则是否过严。"
    if over_strict > 0:
        return f"已复盘 {settled} 条被拒组合，其中 {over_strict} 条赛后全中，需要复查对应拒绝规则是否过严。"
    return f"已复盘 {settled} 条被拒组合，其中 {supported} 条未全中，当前组合纪律得到样本支持。"


def _lesson(attempts: int, hits: int, longshots: list[dict], longshot_hits: int) -> str:
    if attempts <= 0:
        return "暂无可结算观察，不能更新模型。"
    if longshots and longshot_hits == 0:
        return "高赔率冷门未兑现，说明原始 EV 排序需要冷门降权和赔率段校准。"
    if hits == 0:
        return "本批观察未命中，需要降低模型自信并复核信号分类。"
    return "已有命中样本，但仍需按赔率段和信号类型继续累计。"


def _probability_scores(probability, hit) -> dict:
    if hit is None:
        return {"brier_score": None, "log_loss": None}
    p = _bounded_probability(probability)
    y = 1.0 if hit else 0.0
    brier = (p - y) ** 2
    log_loss = -(y * math.log(p) + (1.0 - y) * math.log(1.0 - p))
    return {"brier_score": round(brier, 6), "log_loss": round(log_loss, 6)}


def _settlement_scores(observation: dict, hit: bool | None) -> dict:
    if hit is None:
        return {
            "paper_stake": _stake_value(observation),
            "settlement_profit": None,
            "settlement_roi": None,
            "unit_profit": None,
        }
    odds = _positive_float(observation.get("odds") or observation.get("official_odds") or observation.get("combo_odds"))
    if odds is None:
        return {
            "paper_stake": _stake_value(observation),
            "settlement_profit": None,
            "settlement_roi": None,
            "unit_profit": None,
        }
    stake = _stake_value(observation)
    profit = stake * (odds - 1.0) if hit else -stake
    unit_profit = (odds - 1.0) if hit else -1.0
    return {
        "paper_stake": round(stake, 2),
        "settlement_profit": round(profit, 6),
        "settlement_roi": round(profit / stake, 6) if stake > 0 else None,
        "unit_profit": round(unit_profit, 6),
    }


def _stake_value(observation: dict) -> float:
    if str(observation.get("learning_track") or "") == "rejected_combo":
        return 0.0
    stake = _positive_float(observation.get("paper_stake"))
    if stake is not None:
        return stake
    return 1.0


def _positive_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _probability_quality(rows: list[dict]) -> dict:
    scored = [row for row in rows if row.get("brier_score") is not None and row.get("log_loss") is not None]
    if not scored:
        return {
            "status": "empty",
            "brier_score": None,
            "log_loss": None,
            "message_zh": "暂无可评分概率样本。",
        }
    brier = sum(float(row["brier_score"]) for row in scored) / len(scored)
    log_loss = sum(float(row["log_loss"]) for row in scored) / len(scored)
    return {
        "status": "ok",
        "sample_count": len(scored),
        "brier_score": round(brier, 6),
        "log_loss": round(log_loss, 6),
        "grade_zh": _quality_grade(brier, log_loss, len(scored)),
        "message_zh": _quality_message(brier, log_loss, len(scored)),
    }


def _quality_grade(brier: float, log_loss: float, sample_count: int) -> str:
    if sample_count < 30:
        return "样本不足"
    if brier <= 0.18 and log_loss <= 0.55:
        return "较好"
    if brier <= 0.24 and log_loss <= 0.70:
        return "一般"
    return "需要降权"


def _quality_message(brier: float, log_loss: float, sample_count: int) -> str:
    if sample_count < 30:
        return f"当前只有 {sample_count} 条概率样本，Brier/Log Loss 只能提示方向，不能当稳定结论。"
    if brier <= 0.18 and log_loss <= 0.55:
        return "概率质量暂时较好，但仍需继续累计不同赔率段样本。"
    if brier <= 0.24 and log_loss <= 0.70:
        return "概率质量一般，建议继续用市场概率和赔率段先验约束模型自信。"
    return "概率质量偏弱，模型需要降低自信并复核特征和冷门降权。"


def _next_action(probability_quality: dict, longshots: list[dict], longshot_hits: int) -> str:
    if longshots and longshot_hits == 0:
        return "高赔率冷门继续降权；同时用 Brier/Log Loss 监控模型是否过度自信。"
    if probability_quality.get("status") == "ok":
        return "继续累计 Brier/Log Loss、赔率段命中率和 CLV，用于调整概率校准权重。"
    return "继续导入赛后反馈，先积累可评分概率样本。"


def _calibration_bins(rows: list[dict]) -> list[dict]:
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


def _bounded_probability(value) -> float:
    try:
        p = float(value)
    except (TypeError, ValueError):
        p = 0.5
    return max(0.001, min(0.999, p))


def _probability_or_none(value) -> float | None:
    try:
        p = float(value)
    except (TypeError, ValueError):
        return None
    if p < 0 or p > 1:
        return None
    return p


def _outcome_zh(value: str) -> str:
    return {"home": "主胜", "draw": "平", "away": "客胜"}.get(value, value)

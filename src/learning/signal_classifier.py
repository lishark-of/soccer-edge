from __future__ import annotations

from src.learning.odds_bucket_calibrator import calibrate_probability, odds_bucket

_CLV_BUCKET_CACHE: dict | None = None


def classify_signal(candidate: dict, intelligence_score: float | None = None, use_history: bool = True) -> dict:
    odds = _float(candidate.get("odds") or candidate.get("official_odds") or candidate.get("combo_odds")) or 0.0
    model_prob = _float(candidate.get("model_prob") or candidate.get("combo_prob")) or 0.0
    market_prob = _float(candidate.get("market_prob")) or 0.0
    ev = _float(candidate.get("ev")) or 0.0
    edge = _float(candidate.get("edge")) or 0.0
    confidence = _float(candidate.get("observation_confidence") or candidate.get("confidence_score")) or 0.45
    calibration = calibrate_probability(model_prob, market_prob, odds, intelligence_score, use_history=use_history)
    calibrated_prob = calibration["calibrated_prob"]
    calibrated_ev = calibrated_prob * odds - 1.0 if odds > 1 else None
    break_even_prob = 1.0 / odds if odds > 1 else None
    safety_margin = calibrated_prob - break_even_prob if break_even_prob is not None else None
    bucket = odds_bucket(odds)
    if odds >= 6.0:
        category = "longshot_watch"
        label = "冷门观察"
        action = "只作纸面跟踪，不进入串联核心。"
    elif calibrated_ev is not None and calibrated_ev > 0.04 and edge >= 0.025 and confidence >= 0.55:
        category = "value_watch"
        label = "价值观察"
        action = "可继续跟踪，等待临场情报和终盘赔率复核。"
    elif odds <= 3.0 and calibrated_prob >= 0.42 and confidence >= 0.55:
        category = "steady_watch"
        label = "稳健观察"
        action = "可作为优先观察项，但仍需复核情报。"
    else:
        category = "weak_or_pass"
        label = "弱观察/放弃"
        action = "优势不足，优先等待更多信息。"
    decision = _decision(
        odds=odds,
        calibrated_prob=calibrated_prob,
        break_even_prob=break_even_prob,
        safety_margin=safety_margin,
        confidence=confidence,
        edge=edge,
        category=category,
    )
    learning_scores = _learning_scores(
        odds=odds,
        calibrated_prob=calibrated_prob,
        break_even_prob=break_even_prob,
        safety_margin=safety_margin,
        confidence=confidence,
        edge=edge,
        calibration=calibration,
        decision=decision,
        odds_bucket_key=bucket.get("bucket"),
        use_history=use_history,
    )
    return {
        "signal_category": category,
        "signal_category_zh": label,
        "recommended_use_zh": action,
        **decision,
        "odds_bucket": bucket.get("bucket"),
        "odds_bucket_zh": bucket.get("label_zh"),
        "calibrated_prob": round(calibrated_prob, 6),
        "calibrated_ev": round(calibrated_ev, 6) if calibrated_ev is not None else None,
        "break_even_prob": round(break_even_prob, 6) if break_even_prob is not None else None,
        "safety_margin": round(safety_margin, 6) if safety_margin is not None else None,
        "safety_margin_label_zh": _safety_margin_label(safety_margin, odds),
        "odds_reading_zh": _odds_reading(odds, break_even_prob, calibrated_prob, safety_margin),
        "probability_bin": calibration.get("probability_bin"),
        "probability_bin_weight": calibration.get("probability_bin_weight"),
        "probability_bin_message_zh": calibration.get("bin_adjustment_message_zh", ""),
        "odds_coach_verdict_zh": _coach_verdict(decision, odds, safety_margin, confidence),
        "ml_learning_note_zh": _learning_note(bucket, calibration),
        "next_review_zh": _next_review(decision, odds, confidence),
        "user_priority_zh": _user_priority(decision.get("decision_level"), odds, safety_margin),
        "learning_scores": learning_scores,
        "learning_score_summary_zh": _learning_score_summary(learning_scores),
        "matchday_review": _matchday_review(odds, calibrated_prob, safety_margin),
        "calibration": calibration,
    }


def _float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safety_margin_label(safety_margin: float | None, odds: float) -> str:
    if safety_margin is None:
        return "暂不能判断"
    if odds >= 6 and safety_margin < 0.08:
        return "冷门余量不足"
    if safety_margin >= 0.08:
        return "余量较厚"
    if safety_margin >= 0.03:
        return "余量一般"
    if safety_margin >= 0:
        return "余量偏薄"
    return "未覆盖赔率"


def _odds_reading(odds: float, break_even_prob: float | None, calibrated_prob: float, safety_margin: float | None) -> str:
    if not odds or break_even_prob is None or safety_margin is None:
        return "该玩法缺少有效赔率，暂不能做赔率覆盖判断。"
    if odds >= 6:
        prefix = "高赔率冷门"
    elif odds >= 3:
        prefix = "中高赔率"
    else:
        prefix = "常规赔率"
    if safety_margin > 0:
        return f"{prefix}：至少需要 {break_even_prob:.1%} 命中率，校准后约 {calibrated_prob:.1%}，安全边际 {safety_margin:.1%}。"
    return f"{prefix}：至少需要 {break_even_prob:.1%} 命中率，校准后约 {calibrated_prob:.1%}，暂未覆盖赔率。"


def _coach_verdict(decision: dict, odds: float, safety_margin: float | None, confidence: float) -> str:
    level = decision.get("decision_level")
    if level == "priority_watch":
        return "赔率教练：先列为重点观察，但必须等临场情报和终盘赔率确认。"
    if level == "normal_watch":
        return "赔率教练：有一点价值，但边际不厚，适合继续观察。"
    if level == "longshot_track" or odds >= 6:
        return "赔率教练：这是冷门波动，不是稳健方向；不能拿来当串联核心。"
    if level == "thin_edge":
        return "赔率教练：优势太薄，赔率稍微变化就可能失去价值。"
    if level == "wait_info" or confidence < 0.45:
        return "赔率教练：数字暂时不够，先等伤停、首发、天气或赔率变化。"
    if level == "no_value" or (safety_margin is not None and safety_margin < 0):
        return "赔率教练：校准概率没有覆盖赔率，当前无观察价值。"
    return "赔率教练：先看盈亏线和校准概率，再决定是否继续观察。"


def _learning_note(bucket: dict, calibration: dict) -> str:
    probability_bin = calibration.get("probability_bin") or "未知概率段"
    bin_weight = float(calibration.get("probability_bin_weight") or 0.0)
    bucket_label = bucket.get("label_zh") or bucket.get("bucket") or "未知赔率段"
    if bin_weight <= 0:
        return f"机器学习反馈：{bucket_label} + {probability_bin} 暂无稳定赛后样本，先按保守先验处理。"
    return f"机器学习反馈：{bucket_label} + {probability_bin} 已接入赛后样本，以 {bin_weight:.1%} 小权重约束排序。"


def _next_review(decision: dict, odds: float, confidence: float) -> str:
    level = decision.get("decision_level")
    if odds >= 6:
        return "下一步：只复核是否有强情报支撑冷门；没有就继续纸面跟踪。"
    if level in {"priority_watch", "normal_watch"}:
        return "下一步：临近开赛复核赔率是否继续支持，情报是否出现反向变化。"
    if confidence < 0.45:
        return "下一步：先补情报覆盖，再重新计算观察可信度。"
    return "下一步：等待赔率或模型边际变得更清晰。"


def _user_priority(level: str | None, odds: float, safety_margin: float | None) -> str:
    if level == "priority_watch":
        return "优先级：高，先放在观察区顶部。"
    if level == "normal_watch":
        return "优先级：中，继续等待确认。"
    if odds >= 6:
        return "优先级：低到中，冷门只单独观察。"
    if safety_margin is not None and safety_margin < 0:
        return "优先级：低，当前跳过。"
    return "优先级：低，等待更多信息。"


def _matchday_review(odds: float, calibrated_prob: float, safety_margin: float | None) -> dict:
    if odds <= 1.0 or calibrated_prob <= 0:
        return {
            "status_zh": "等待赔率",
            "keep_min_odds": None,
            "no_value_below_odds": None,
            "reverse_drift_watch_odds": None,
            "message_zh": "缺少有效赔率或校准概率，赛日无法做赔率复核。",
        }
    no_value_below = 1.0 / calibrated_prob
    desired_margin = 0.03 if odds < 6 else 0.08
    keep_min = 1.0 / (calibrated_prob - desired_margin) if calibrated_prob > desired_margin else no_value_below
    reverse_drift_watch = odds * (1.08 if odds < 6 else 1.15)
    if safety_margin is not None and safety_margin < 0:
        status = "当前未覆盖赔率"
    elif odds >= 6:
        status = "冷门临场严查"
    else:
        status = "赛日复核"
    return {
        "status_zh": status,
        "keep_min_odds": round(keep_min, 4),
        "no_value_below_odds": round(no_value_below, 4),
        "reverse_drift_watch_odds": round(reverse_drift_watch, 4),
        "message_zh": (
            f"赛日复核：若临场赔率低于 {keep_min:.2f}，安全边际会变薄；"
            f"低于 {no_value_below:.2f} 基本失去赔率覆盖；"
            f"若升至 {reverse_drift_watch:.2f} 以上且没有新情报支持，要警惕市场反向漂移。"
        ),
    }


def _learning_scores(
    odds: float,
    calibrated_prob: float,
    break_even_prob: float | None,
    safety_margin: float | None,
    confidence: float,
    edge: float,
    calibration: dict,
    decision: dict,
    odds_bucket_key: str | None = None,
    use_history: bool = True,
) -> dict:
    odds_value = _clamp_score(((safety_margin or -0.04) + 0.02) / 0.12 * 100)
    if odds >= 6:
        odds_value = min(odds_value, 62)
    stats = calibration.get("probability_bin_stats") or {}
    attempts = int(stats.get("attempts") or 0)
    hit_rate = stats.get("hit_rate")
    history_score = 28 if attempts == 0 else min(75, 35 + attempts * 3)
    if hit_rate is not None and calibrated_prob:
        history_score += max(-12, min(12, (float(hit_rate) - calibrated_prob) * 100))
    history_score = _clamp_score(history_score)
    clv_stats = _learned_clv_bucket_stats(odds_bucket_key) if use_history else {}
    clv_score = _clv_score(clv_stats)
    confidence_score = _clamp_score(confidence * 100)
    edge_score = _clamp_score((edge + 0.015) / 0.08 * 100)
    matchday_score = int(round(confidence_score * 0.65 + edge_score * 0.35))
    if decision.get("decision_level") in {"wait_info", "thin_edge", "no_value"}:
        matchday_score = min(matchday_score, 48)
    parlay_score = _parlay_fit_score(odds, safety_margin, confidence, decision)
    overall = int(round(odds_value * 0.28 + history_score * 0.16 + clv_score * 0.12 + matchday_score * 0.22 + parlay_score * 0.22))
    return {
        "overall_score": overall,
        "odds_value_score": int(round(odds_value)),
        "history_score": int(round(history_score)),
        "clv_score": int(round(clv_score)),
        "matchday_review_score": int(round(matchday_score)),
        "parlay_fit_score": int(round(parlay_score)),
        "probability_sample_count": attempts,
        "clv_sample_count": int(clv_stats.get("attempts") or 0),
        "verdict_zh": _learning_verdict(overall),
        "odds_value_zh": _score_label(odds_value),
        "history_zh": "样本不足" if attempts == 0 else f"已有 {attempts} 条同概率段反馈",
        "clv_zh": _clv_message(clv_stats),
        "matchday_zh": _score_label(matchday_score),
        "parlay_fit_zh": _score_label(parlay_score),
    }


def _learned_clv_bucket_stats(bucket_key: str | None) -> dict:
    global _CLV_BUCKET_CACHE
    if not bucket_key:
        return {}
    try:
        if _CLV_BUCKET_CACHE is None:
            from src.market.clv import build_clv_history

            _CLV_BUCKET_CACHE = (build_clv_history() or {}).get("bucket_stats", {})
        return _CLV_BUCKET_CACHE.get(bucket_key, {}) or {}
    except Exception:
        return {}


def _clv_score(stats: dict) -> float:
    attempts = int(stats.get("attempts") or 0)
    if attempts <= 0:
        return 30.0
    avg = float(stats.get("average_clv_pct") or 0.0)
    positive_rate = float(stats.get("positive_clv_rate") or 0.0)
    score = 38 + min(22, attempts * 2.0) + avg * 650 + (positive_rate - 0.5) * 24
    if attempts < 8:
        score = min(score, 48)
    return _clamp_score(score)


def _clv_message(stats: dict) -> str:
    attempts = int(stats.get("attempts") or 0)
    if attempts <= 0:
        return "CLV 样本不足"
    avg = float(stats.get("average_clv_pct") or 0.0)
    if attempts < 8:
        return f"CLV 样本 {attempts} 条，先作提示"
    if avg > 0.015:
        return f"CLV 为正 {avg:.2%}"
    if avg < -0.015:
        return f"CLV 为负 {avg:.2%}"
    return "CLV 接近中性"


def _parlay_fit_score(odds: float, safety_margin: float | None, confidence: float, decision: dict) -> float:
    level = decision.get("decision_level")
    if odds >= 6:
        return 12
    if safety_margin is None or safety_margin < 0:
        return 8
    base = confidence * 60 + min(30, safety_margin * 300)
    if level == "priority_watch":
        base += 10
    elif level in {"thin_edge", "wait_info"}:
        base -= 20
    return _clamp_score(base)


def _learning_verdict(score: int) -> str:
    if score >= 72:
        return "机器学习结论：可重点观察，仍需赛日前复核。"
    if score >= 58:
        return "机器学习结论：可以继续观察，但不宜跳过临场复核。"
    if score >= 42:
        return "机器学习结论：弱观察，优先等待赔率或情报改善。"
    return "机器学习结论：当前不够清晰，先跳过或仅纸面跟踪。"


def _learning_score_summary(scores: dict) -> str:
    return (
        f"{scores.get('verdict_zh', '机器学习结论：待评估')} "
        f"总分 {scores.get('overall_score', 0)}/100；"
        f"赔率价值 {scores.get('odds_value_score', 0)}，"
        f"历史学习 {scores.get('history_score', 0)}，"
        f"CLV价格 {scores.get('clv_score', 0)}，"
        f"临场复核 {scores.get('matchday_review_score', 0)}，"
        f"串联资格 {scores.get('parlay_fit_score', 0)}。"
    )


def _score_label(score: float) -> str:
    if score >= 72:
        return "较强"
    if score >= 58:
        return "中等"
    if score >= 42:
        return "偏弱"
    return "不足"


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _decision(
    odds: float,
    calibrated_prob: float,
    break_even_prob: float | None,
    safety_margin: float | None,
    confidence: float,
    edge: float,
    category: str,
) -> dict:
    if break_even_prob is None or safety_margin is None:
        level = "wait_odds"
        label = "等待赔率"
        action = "该玩法缺少有效赔率，先不做价值判断。"
        reason = "没有赔率就无法计算盈亏平衡概率，也无法判断模型概率是否覆盖赔率。"
        parlay = "不进入串联。"
    elif safety_margin < 0:
        level = "no_value"
        label = "无观察价值"
        action = "暂时放弃，除非赔率或情报发生明显变化。"
        reason = f"校准概率 {calibrated_prob:.1%} 低于盈亏线 {break_even_prob:.1%}，没有覆盖赔率。"
        parlay = "不进入串联。"
    elif odds >= 6:
        level = "longshot_track"
        label = "冷门跟踪"
        action = "只做纸面跟踪，不作为串联核心。"
        reason = "赔率很高说明波动极大；需要更厚安全边际和更完整情报。"
        parlay = "默认不进入串联，除非长期样本和赛前情报都支持。"
    elif confidence < 0.45:
        level = "wait_info"
        label = "等待情报"
        action = "先补伤停、首发、天气、新闻和终盘赔率。"
        reason = "赔率有一定余量，但情报可信度不足，容易被模型偏差误导。"
        parlay = "暂不串联。"
    elif safety_margin >= 0.08 and edge >= 0.025 and confidence >= 0.55:
        level = "priority_watch"
        label = "优先观察"
        action = "可列入优先观察清单，赛前再复核终盘赔率和情报。"
        reason = f"校准概率高于盈亏线 {safety_margin:.1%}，且 Edge 与可信度达到观察门槛。"
        parlay = "可作为低风险组合候选，但仍需通过组合相关性和可信度门控。"
    elif safety_margin >= 0.03:
        level = "normal_watch"
        label = "普通观察"
        action = "保留观察，等待临场信息确认。"
        reason = f"校准概率略高于盈亏线 {safety_margin:.1%}，但安全边际不算厚。"
        parlay = "一般不作为串联核心。"
    else:
        level = "thin_edge"
        label = "薄优势"
        action = "不急于进入观察清单，等待赔率变动或情报补强。"
        reason = f"虽然略高于盈亏线，但安全边际只有 {safety_margin:.1%}。"
        parlay = "不进入串联。"
    if category == "weak_or_pass" and level not in {"no_value", "wait_odds"}:
        label = "弱观察"
    return {
        "decision_level": level,
        "decision_label_zh": label,
        "decision_action_zh": action,
        "decision_reason_zh": reason,
        "parlay_policy_zh": parlay,
    }

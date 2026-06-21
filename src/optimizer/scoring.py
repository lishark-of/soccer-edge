from __future__ import annotations

from src.optimizer.constraints import stake_cap_for
from src.learning.signal_classifier import classify_signal
from src.learning.competition_segments import classify_competition_segment
from src.learning.ai_factor_taxonomy import classify_ai_factor


def score_candidate(candidate: dict, bankroll: float, config: dict | None = None) -> dict:
    cfg = config or {}
    kind = candidate.get("candidate_type", "single")
    odds = _odds(candidate)
    raw_probability = _probability(candidate)
    longshot = odds >= 6.0
    if longshot:
        candidate = {**candidate, "risk_level": "very_high"}
    confidence = float(candidate.get("observation_confidence") or candidate.get("confidence_score") or 0.45)
    market_prob = float(candidate.get("market_prob") or 0.0)
    segment = classify_competition_segment(candidate)
    ai_factor = classify_ai_factor(candidate, candidate.get("candidate_type"))
    shrinkage = _market_calibrated_probability(raw_probability, market_prob, cfg, confidence)
    probability = float(shrinkage["probability"])
    original_ev = float(candidate.get("ev") or 0.0)
    original_edge = float(candidate.get("edge") or 0.0)
    ev = probability * odds - 1.0 if odds > 0 and probability > 0 else original_ev
    edge = probability - market_prob if market_prob > 0 and probability > 0 else original_edge
    learning = classify_signal({**candidate, "odds": odds, "model_prob": probability, "market_prob": market_prob, "ev": ev, "edge": edge}, confidence * 100)
    calibrated_prob = float(learning.get("calibrated_prob") or probability)
    calibrated_ev = learning.get("calibrated_ev")
    effective_ev = float(calibrated_ev) if calibrated_ev is not None else ev
    correlation_discount = float(candidate.get("correlation_discount") or 1.0)
    risk_level = str(candidate.get("risk_level") or "medium")
    risk_penalty = {"low": 0.0, "medium": 0.08, "high": 0.18, "very_high": 0.32}.get(risk_level, 0.1)
    model_market_gap = abs(probability - market_prob) if probability and market_prob else None
    disagreement_penalty = _model_disagreement_penalty(model_market_gap)
    uncertainty = _probability_uncertainty_band(probability, market_prob, odds, cfg, confidence, model_market_gap, risk_level)
    robustness_penalty = float(uncertainty.get("robustness_penalty") or 0.0)
    market_model_agreement = max(0.0, 1.0 - min(1.0, model_market_gap * 4)) if model_market_gap is not None else 0.35
    odds_quality = min(1.0, odds / 5.0) if odds else 0.0
    normalized_ev = max(-1.0, min(1.0, effective_ev / 0.25)) if effective_ev else 0.0
    information_score = max(0.0, min(1.0, confidence))
    drawdown_safety = max(0.0, 1.0 - risk_penalty)
    leg_quality_score = max(
        0.0,
        min(
            1.0,
            0.30 * max(0.0, normalized_ev)
            + 0.25 * information_score
            + 0.20 * market_model_agreement
            + 0.15 * drawdown_safety
            + 0.10 * max(0.0, min(1.0, correlation_discount))
            - (0.18 if longshot else 0.0)
            - disagreement_penalty
            - robustness_penalty,
        ),
    )
    combo_score = (
        0.35 * normalized_ev
        + 0.20 * confidence
        + 0.15 * market_model_agreement
        + 0.10 * odds_quality
        + 0.10 * max(0.0, min(1.0, correlation_discount))
        + 0.10 * drawdown_safety
        - disagreement_penalty * 0.8
        - robustness_penalty
    )
    risk_adjusted_score = combo_score - risk_penalty - disagreement_penalty * 0.5 - robustness_penalty * 0.5
    kelly_fraction = _kelly_fraction(calibrated_prob, odds)
    score = effective_ev * 100 + edge * 20 + min(kelly_fraction, 0.25) * 10 - disagreement_penalty * 12 - robustness_penalty * 14
    short_cycle = _short_cycle_adjustment(
        cfg=cfg,
        odds=odds,
        effective_ev=effective_ev,
        edge=edge,
        confidence=confidence,
        risk_level=risk_level,
        longshot=longshot,
        market_model_gap=model_market_gap,
        robust_status=str(uncertainty.get("status") or ""),
    )
    if short_cycle["adjustment"]:
        adj = float(short_cycle["adjustment"])
        combo_score += adj
        risk_adjusted_score += adj
        leg_quality_score = min(1.0, leg_quality_score + adj * 0.55)
        score += adj * 10.0
    cap = stake_cap_for(kind, bankroll, cfg)
    kelly_stake = float(bankroll) * max(0.0, kelly_fraction) * float(cfg.get("kelly_multiplier", 0.25))
    suggested = round(min(cap, max(0.0, kelly_stake)), 2)
    if effective_ev > 0 and suggested <= 0:
        suggested = min(cap, max(10.0, cap * 0.25))
    longshot_parlay_min = float(cfg.get("longshot_parlay_confidence_min", 0.75))
    parlay_eligible = (not longshot) or confidence >= longshot_parlay_min
    return {
        **candidate,
        "model_prob": round(probability, 6),
        "score": round(score, 6),
        "raw_model_prob": round(raw_probability, 6),
        "probability_shrinkage": shrinkage,
        "probability_shrinkage_reason_zh": shrinkage.get("reason_zh", ""),
        "probability_shrinkage_weight": shrinkage.get("shrink_weight", 0.0),
        "raw_ev": round(original_ev, 6),
        "raw_edge": round(original_edge, 6),
        "ev": round(ev, 6),
        "edge": round(edge, 6),
        **segment,
        **ai_factor,
        "calibrated_prob": round(calibrated_prob, 6),
        "calibrated_ev": round(float(calibrated_ev), 6) if calibrated_ev is not None else None,
        "break_even_prob": learning.get("break_even_prob"),
        "safety_margin": learning.get("safety_margin"),
        "safety_margin_label_zh": learning.get("safety_margin_label_zh"),
        "odds_reading_zh": learning.get("odds_reading_zh"),
        "decision_level": learning.get("decision_level"),
        "decision_label_zh": learning.get("decision_label_zh"),
        "decision_action_zh": learning.get("decision_action_zh"),
        "decision_reason_zh": learning.get("decision_reason_zh"),
        "parlay_policy_zh": learning.get("parlay_policy_zh"),
        "learning_adjustment": learning,
        "signal_category": learning.get("signal_category"),
        "signal_category_zh": learning.get("signal_category_zh"),
        "recommended_use_zh": learning.get("recommended_use_zh"),
        "odds_bucket": learning.get("odds_bucket"),
        "odds_bucket_zh": learning.get("odds_bucket_zh"),
        "probability_bin": learning.get("probability_bin"),
        "probability_bin_weight": learning.get("probability_bin_weight"),
        "probability_bin_message_zh": learning.get("probability_bin_message_zh", ""),
        "odds_coach_verdict_zh": learning.get("odds_coach_verdict_zh", ""),
        "ml_learning_note_zh": learning.get("ml_learning_note_zh", ""),
        "next_review_zh": learning.get("next_review_zh", ""),
        "user_priority_zh": learning.get("user_priority_zh", ""),
        "learning_scores": learning.get("learning_scores", {}),
        "learning_score_summary_zh": learning.get("learning_score_summary_zh", ""),
        "combo_score": round(combo_score, 6),
        "risk_adjusted_score": round(risk_adjusted_score, 6),
        "leg_quality_score": round(leg_quality_score, 6),
        "short_cycle_adjustment": short_cycle,
        "short_cycle_score_adjustment": round(float(short_cycle["adjustment"]), 6),
        "short_cycle_reason_zh": short_cycle["reason_zh"],
        "information_score": round(information_score, 6),
        "risk_penalty": round(risk_penalty, 6),
        "market_model_agreement": round(market_model_agreement, 6),
        "model_market_gap": round(model_market_gap, 6) if model_market_gap is not None else None,
        "model_disagreement_penalty": round(disagreement_penalty, 6),
        "model_disagreement_reason_zh": _model_disagreement_reason(model_market_gap),
        "probability_uncertainty": uncertainty,
        "probability_lower": uncertainty.get("lower"),
        "probability_upper": uncertainty.get("upper"),
        "robust_edge": uncertainty.get("robust_edge"),
        "robust_ev": uncertainty.get("robust_ev"),
        "robust_value_status": uncertainty.get("status"),
        "robust_value_label_zh": uncertainty.get("label_zh"),
        "robust_value_reason_zh": uncertainty.get("reason_zh"),
        "robustness_penalty": round(robustness_penalty, 6),
        "odds_quality": round(odds_quality, 6),
        "drawdown_safety": round(drawdown_safety, 6),
        "kelly_fraction": round(kelly_fraction, 6),
        "suggested_paper_stake": round(suggested, 2),
        "stake_cap": round(cap, 2),
        "stake_reason": "按 1/4 Kelly 参考值估算，并受单项上限与每日总暴露约束。这是纸面投入，不是资金建议。",
        "selection_reason": _selection_reason(kind, effective_ev, edge, candidate.get("risk_level"), model_market_gap),
        "longshot_warning": "这是高赔率冷门观察，不是稳健信号；除非可信度充分补齐，否则不适合作为串联核心。" if longshot else "",
        "parlay_eligible": parlay_eligible,
        "longshot_parlay_blocked": bool(longshot and not parlay_eligible),
        "hit_rate_discipline_zh": _hit_rate_discipline(kind, probability, confidence, risk_level, longshot, parlay_eligible),
    }


def _odds(candidate: dict) -> float:
    return float(candidate.get("odds") or candidate.get("combo_odds") or 0.0)


def _probability(candidate: dict) -> float:
    return float(candidate.get("model_prob") or candidate.get("combo_prob") or 0.0)


def _kelly_fraction(probability: float, odds: float) -> float:
    if odds <= 1:
        return 0.0
    return (probability * odds - 1.0) / (odds - 1.0)


def _market_calibrated_probability(raw_probability: float, market_prob: float, cfg: dict, confidence: float) -> dict:
    raw_probability = max(0.0, min(1.0, float(raw_probability or 0.0)))
    market_prob = max(0.0, min(1.0, float(market_prob or 0.0)))
    if raw_probability <= 0 or market_prob <= 0:
        return {
            "probability": raw_probability or market_prob,
            "shrink_weight": 0.0,
            "status": "insufficient_input",
            "reason_zh": "缺少模型概率或市场概率，暂不做市场收缩。",
        }
    quality = cfg.get("learning_probability_quality") or {}
    clv = cfg.get("learning_clv_summary") or {}
    market_benchmark = cfg.get("learning_market_benchmark") or {}
    settled = _safe_float(cfg.get("learning_settled_count")) or _safe_float(quality.get("sample_count")) or 0.0
    brier = _safe_float(quality.get("brier_score"))
    log_loss = _safe_float(quality.get("log_loss"))
    avg_clv = _safe_float(clv.get("average_clv_pct"))
    clv_count = _safe_float(clv.get("settled_count")) or 0.0
    market_skill = _safe_float(market_benchmark.get("brier_skill_score"))
    market_skill_samples = _safe_float(market_benchmark.get("sample_count")) or 0.0
    market_discipline = _market_benchmark_discipline(market_skill, market_skill_samples)
    shrink = 0.18
    reasons = ["市场赔率作为强基准参与概率收缩"]
    if settled < 30:
        shrink += 0.18
        reasons.append("赛后样本不足 30 条")
    elif settled < 100:
        shrink += 0.08
        reasons.append("赛后样本仍处小样本阶段")
    if brier is None or log_loss is None:
        shrink += 0.08
        reasons.append("Brier/Log Loss 证据不足")
    else:
        if brier > 0.28 or log_loss > 0.85:
            shrink += 0.18
            reasons.append("概率校准偏弱")
        elif brier > 0.24 or log_loss > 0.72:
            shrink += 0.10
            reasons.append("概率校准一般")
        elif brier <= 0.20 and log_loss <= 0.62 and settled >= 100:
            shrink -= 0.08
            reasons.append("校准证据较好，保留更多模型权重")
    if clv_count >= 10 and avg_clv is not None:
        if avg_clv < 0:
            shrink += 0.12
            reasons.append("平均 CLV 偏负")
        elif avg_clv > 0.005:
            shrink -= 0.05
            reasons.append("平均 CLV 偏正")
    if market_skill is not None and market_skill_samples >= 10:
        if market_skill < 0:
            shrink += 0.14
            reasons.append("模型 Brier 暂未优于市场概率")
        elif market_skill >= 0.03 and market_skill_samples >= 50:
            shrink -= 0.06
            reasons.append("模型相对市场已有正 Brier Skill")
        elif market_skill > 0:
            reasons.append("模型相对市场略有正技能分，继续小样本观察")
    if confidence < 0.50:
        shrink += 0.10
        reasons.append("观察可信度偏低")
    gap = abs(raw_probability - market_prob)
    if gap > 0.14:
        shrink += 0.12
        reasons.append("模型与市场高分歧")
    elif gap > 0.08:
        shrink += 0.06
        reasons.append("模型与市场中度分歧")
    shrink = max(0.0, min(0.65, shrink))
    probability = raw_probability * (1.0 - shrink) + market_prob * shrink
    return {
        "probability": round(probability, 6),
        "raw_probability": round(raw_probability, 6),
        "market_probability": round(market_prob, 6),
        "shrink_weight": round(shrink, 6),
        "status": "market_calibrated",
        "market_benchmark_discipline": market_discipline,
        "reason_zh": f"纪律校准后概率 {probability:.1%}；向市场概率收缩 {shrink:.0%}，原因：{'、'.join(reasons)}。",
    }


def _market_benchmark_discipline(market_skill: float | None, sample_count: float) -> dict:
    if market_skill is None or sample_count < 10:
        return {
            "status": "insufficient",
            "label_zh": "市场基准证据不足",
            "message_zh": "模型相对市场概率的赛后样本不足，排序默认更尊重市场概率。",
        }
    if market_skill < 0:
        return {
            "status": "behind_market",
            "label_zh": "模型暂未跑赢市场",
            "message_zh": f"模型相对市场 Brier Skill {market_skill:+.1%}，本轮加强向市场概率收缩。",
        }
    if market_skill >= 0.03 and sample_count >= 50:
        return {
            "status": "beating_market",
            "label_zh": "模型阶段性优于市场",
            "message_zh": f"模型相对市场 Brier Skill {market_skill:+.1%}，允许保留更多模型权重。",
        }
    return {
        "status": "watch",
        "label_zh": "模型略优待观察",
        "message_zh": f"模型相对市场 Brier Skill {market_skill:+.1%}，样本仍需扩大。",
    }


def _short_cycle_adjustment(
    *,
    cfg: dict,
    odds: float,
    effective_ev: float,
    edge: float,
    confidence: float,
    risk_level: str,
    longshot: bool,
    market_model_gap: float | None,
    robust_status: str,
) -> dict:
    if not cfg.get("short_cycle_mode", True):
        return {"status": "off", "adjustment": 0.0, "reason_zh": "短周期赛会模式未启用。"}
    settled = _safe_float(cfg.get("learning_settled_count")) or 0.0
    if settled >= 60:
        return {"status": "enough_history", "adjustment": 0.0, "reason_zh": "赛后样本已较多，短周期调节自动降级。"}
    reasons = []
    adjustment = 0.0
    gap = float(market_model_gap or 0.0)
    if effective_ev > 0 and edge > 0 and gap <= 0.06:
        bonus = float(cfg.get("short_cycle_market_agreement_bonus", 0.05))
        adjustment += bonus
        reasons.append("模型与市场接近且仍有正价值，短周期加分")
    if robust_status == "robust":
        bonus = float(cfg.get("short_cycle_robust_value_bonus", 0.04))
        adjustment += bonus
        reasons.append("概率区间下沿仍覆盖赔率")
    if risk_level in {"high", "very_high"}:
        adjustment -= 0.04 if risk_level == "high" else 0.08
        reasons.append("风险偏高，短周期降权")
    if longshot:
        adjustment -= 0.08
        reasons.append("长赔冷门不适合作为短周期核心")
    if odds >= 4.5:
        adjustment -= 0.03
        reasons.append("赔率偏高，波动惩罚")
    if confidence < 0.50:
        adjustment -= 0.04
        reasons.append("可信度不足")
    adjustment = max(-0.12, min(0.12, adjustment))
    status = "boost" if adjustment > 0 else "penalty" if adjustment < 0 else "neutral"
    if not reasons:
        reasons.append("短周期模式保持中性，等待更多赛后样本")
    return {
        "status": status,
        "adjustment": round(adjustment, 6),
        "reason_zh": "赛会短周期模式：" + "；".join(reasons[:4]) + "。",
    }


def _probability_uncertainty_band(
    probability: float,
    market_prob: float,
    odds: float,
    cfg: dict,
    confidence: float,
    model_market_gap: float | None,
    risk_level: str,
) -> dict:
    probability = max(0.0, min(1.0, float(probability or 0.0)))
    market_prob = max(0.0, min(1.0, float(market_prob or 0.0)))
    quality = cfg.get("learning_probability_quality") or {}
    clv = cfg.get("learning_clv_summary") or {}
    settled = _safe_float(cfg.get("learning_settled_count")) or _safe_float(quality.get("sample_count")) or 0.0
    brier = _safe_float(quality.get("brier_score"))
    log_loss = _safe_float(quality.get("log_loss"))
    clv_count = _safe_float(clv.get("settled_count")) or 0.0
    avg_clv = _safe_float(clv.get("average_clv_pct"))
    gap = float(model_market_gap or 0.0)
    width = 0.035 + max(0.0, 0.55 - confidence) * 0.16 + min(0.11, gap * 0.38)
    reasons = ["按可信度、市场分歧、赛后校准和 CLV 估计概率区间"]
    if settled < 30:
        width += 0.045
        reasons.append("小样本")
    elif settled < 100:
        width += 0.020
        reasons.append("样本仍未充分")
    if brier is None or log_loss is None:
        width += 0.025
        reasons.append("缺少 Brier/Log Loss")
    elif brier > 0.28 or log_loss > 0.85:
        width += 0.045
        reasons.append("校准偏弱")
    elif brier <= 0.20 and log_loss <= 0.62 and settled >= 100:
        width -= 0.020
        reasons.append("校准较好")
    if clv_count >= 10 and avg_clv is not None:
        if avg_clv < 0:
            width += 0.030
            reasons.append("CLV 偏负")
        elif avg_clv > 0.005:
            width -= 0.015
            reasons.append("CLV 偏正")
    if risk_level in {"high", "very_high"}:
        width += 0.020
        reasons.append("风险等级偏高")
    width = max(0.025, min(0.22, width))
    lower = max(0.0, probability - width)
    upper = min(1.0, probability + width)
    robust_edge = lower - market_prob if market_prob > 0 else None
    robust_ev = lower * odds - 1.0 if odds > 0 else None
    penalty = 0.0
    if robust_ev is not None and robust_ev <= 0:
        penalty += min(0.14, abs(robust_ev) * 0.22 + 0.04)
    if robust_edge is not None and robust_edge <= 0:
        penalty += 0.04
    penalty = round(min(0.18, penalty), 6)
    if robust_ev is not None and robust_ev > 0 and robust_edge is not None and robust_edge > 0:
        status = "robust"
        label = "稳健价值通过"
    elif robust_ev is not None and robust_ev > 0:
        status = "thin"
        label = "价值边际偏薄"
    else:
        status = "fragile"
        label = "稳健价值不足"
    return {
        "lower": round(lower, 6),
        "upper": round(upper, 6),
        "width": round(width, 6),
        "robust_edge": round(robust_edge, 6) if robust_edge is not None else None,
        "robust_ev": round(robust_ev, 6) if robust_ev is not None else None,
        "robustness_penalty": penalty,
        "status": status,
        "label_zh": label,
        "reason_zh": f"{label}：校准概率区间 {lower:.1%}-{upper:.1%}；保守下沿 EV {robust_ev:+.1%}，稳健 Edge {robust_edge:+.1%}。依据：{'、'.join(reasons)}。",
    }


def _selection_reason(kind: str, ev: float, edge: float, risk: str | None, model_market_gap: float | None = None) -> str:
    label = {"single": "单关观察", "parlay_2x1": "2串1 组合观察", "parlay_3x1": "3串1 组合观察"}.get(kind, kind)
    tail = ""
    if model_market_gap is not None and model_market_gap > 0.08:
        tail = f" 但模型与市场概率相差 {model_market_gap:.1%}，需要额外复核，不把高 EV 直接当强信号。"
    return f"{label}满足 EV {ev:.2%}、Edge {edge:.2%} 与风险等级 {risk or 'medium'} 的约束。{tail}"


def _model_disagreement_penalty(gap: float | None) -> float:
    if gap is None:
        return 0.03
    if gap <= 0.04:
        return 0.0
    if gap <= 0.08:
        return 0.04
    if gap <= 0.14:
        return 0.08
    return 0.12


def _model_disagreement_reason(gap: float | None) -> str:
    if gap is None:
        return "缺少模型概率或市场概率，按轻度不确定性处理。"
    if gap <= 0.04:
        return "模型与市场概率接近，分歧较小。"
    if gap <= 0.08:
        return f"模型与市场概率相差 {gap:.1%}，轻度分歧，排序轻微降权。"
    if gap <= 0.14:
        return f"模型与市场概率相差 {gap:.1%}，中度分歧；高 EV 需要额外复核。"
    return f"模型与市场概率相差 {gap:.1%}，高分歧；不能把高 EV 直接升级为强观察。"


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _hit_rate_discipline(
    kind: str,
    probability: float,
    confidence: float,
    risk_level: str,
    longshot: bool,
    parlay_eligible: bool,
) -> str:
    if kind == "single":
        if longshot:
            return "高赔率冷门观察：只适合单独观察，不适合作为串联核心。"
        return "单关观察优先看概率、赔率价值和情报完整度，不因单项 EV 为正就放大组合。"
    if longshot and not parlay_eligible:
        return "含高赔率冷门腿，且可信度未达到高门槛，串联纪律不通过。"
    if probability < 0.20:
        return "组合命中概率偏低，串联会明显放大波动。"
    if confidence < 0.50:
        return "组合腿可信度不足，需要补齐伤停、首发、天气或新闻面后再评估。"
    if risk_level in {"high", "very_high"}:
        return "组合风险偏高，即使赔率有吸引力也需要降权观察。"
    return "组合命中率、单腿可信度和风险等级初步通过纪律检查。"

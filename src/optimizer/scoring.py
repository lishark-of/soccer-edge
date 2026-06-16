from __future__ import annotations

from src.optimizer.constraints import stake_cap_for
from src.learning.signal_classifier import classify_signal


def score_candidate(candidate: dict, bankroll: float, config: dict | None = None) -> dict:
    cfg = config or {}
    kind = candidate.get("candidate_type", "single")
    odds = _odds(candidate)
    probability = _probability(candidate)
    ev = float(candidate.get("ev") or 0.0)
    edge = float(candidate.get("edge") or 0.0)
    longshot = odds >= 6.0
    if longshot:
        candidate = {**candidate, "risk_level": "very_high"}
    confidence = float(candidate.get("observation_confidence") or candidate.get("confidence_score") or 0.45)
    market_prob = float(candidate.get("market_prob") or 0.0)
    learning = classify_signal({**candidate, "odds": odds, "model_prob": probability, "market_prob": market_prob, "ev": ev, "edge": edge}, confidence * 100)
    calibrated_prob = float(learning.get("calibrated_prob") or probability)
    calibrated_ev = learning.get("calibrated_ev")
    effective_ev = float(calibrated_ev) if calibrated_ev is not None else ev
    correlation_discount = float(candidate.get("correlation_discount") or 1.0)
    risk_level = str(candidate.get("risk_level") or "medium")
    risk_penalty = {"low": 0.0, "medium": 0.08, "high": 0.18, "very_high": 0.32}.get(risk_level, 0.1)
    market_model_agreement = max(0.0, 1.0 - min(1.0, abs(probability - market_prob) * 4)) if probability and market_prob else 0.35
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
            - (0.18 if longshot else 0.0),
        ),
    )
    combo_score = (
        0.35 * normalized_ev
        + 0.20 * confidence
        + 0.15 * market_model_agreement
        + 0.10 * odds_quality
        + 0.10 * max(0.0, min(1.0, correlation_discount))
        + 0.10 * drawdown_safety
    )
    risk_adjusted_score = combo_score - risk_penalty
    kelly_fraction = _kelly_fraction(calibrated_prob, odds)
    cap = stake_cap_for(kind, bankroll, cfg)
    kelly_stake = float(bankroll) * max(0.0, kelly_fraction) * float(cfg.get("kelly_multiplier", 0.25))
    suggested = round(min(cap, max(0.0, kelly_stake)), 2)
    if effective_ev > 0 and suggested <= 0:
        suggested = min(cap, max(10.0, cap * 0.25))
    score = effective_ev * 100 + edge * 20 + min(kelly_fraction, 0.25) * 10
    longshot_parlay_min = float(cfg.get("longshot_parlay_confidence_min", 0.75))
    parlay_eligible = (not longshot) or confidence >= longshot_parlay_min
    return {
        **candidate,
        "score": round(score, 6),
        "raw_model_prob": round(probability, 6),
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
        "information_score": round(information_score, 6),
        "risk_penalty": round(risk_penalty, 6),
        "market_model_agreement": round(market_model_agreement, 6),
        "odds_quality": round(odds_quality, 6),
        "drawdown_safety": round(drawdown_safety, 6),
        "kelly_fraction": round(kelly_fraction, 6),
        "suggested_paper_stake": round(suggested, 2),
        "stake_cap": round(cap, 2),
        "stake_reason": "按 1/4 Kelly 参考值估算，并受单项上限与每日总暴露约束。这是纸面投入，不是资金建议。",
        "selection_reason": _selection_reason(kind, effective_ev, edge, candidate.get("risk_level")),
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


def _selection_reason(kind: str, ev: float, edge: float, risk: str | None) -> str:
    label = {"single": "单关观察", "parlay_2x1": "2串1 组合观察", "parlay_3x1": "3串1 组合观察"}.get(kind, kind)
    return f"{label}满足 EV {ev:.2%}、Edge {edge:.2%} 与风险等级 {risk or 'medium'} 的约束。"


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

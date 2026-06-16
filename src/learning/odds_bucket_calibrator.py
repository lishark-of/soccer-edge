from __future__ import annotations

BUCKETS = [
    (1.0, 1.5, "1.01-1.50"),
    (1.5, 2.0, "1.50-2.00"),
    (2.0, 3.0, "2.00-3.00"),
    (3.0, 5.0, "3.00-5.00"),
    (5.0, 8.0, "5.00-8.00"),
    (8.0, 999.0, "8.00+"),
]

DEFAULT_BUCKET_PRIORS = {
    "1.01-1.50": {"alpha": 18.0, "beta": 8.0, "label_zh": "低赔率热门"},
    "1.50-2.00": {"alpha": 14.0, "beta": 10.0, "label_zh": "中低赔率"},
    "2.00-3.00": {"alpha": 9.0, "beta": 12.0, "label_zh": "均衡赔率"},
    "3.00-5.00": {"alpha": 5.0, "beta": 13.0, "label_zh": "中高赔率"},
    "5.00-8.00": {"alpha": 3.0, "beta": 15.0, "label_zh": "高赔率观察"},
    "8.00+": {"alpha": 2.0, "beta": 18.0, "label_zh": "高赔率冷门"},
}

_LEARNED_BUCKET_CACHE: dict[str, dict] | None = None
_LEARNED_PROBABILITY_BIN_CACHE: dict[str, dict] | None = None


def odds_bucket(decimal_odds: float | int | str | None) -> dict:
    odds = _float(decimal_odds)
    if odds is None or odds <= 1.0:
        return {"bucket": "unknown", "label_zh": "赔率未知", "lower": None, "upper": None}
    for lower, upper, label in BUCKETS:
        if lower < odds <= upper:
            prior = DEFAULT_BUCKET_PRIORS[label]
            return {"bucket": label, "label_zh": prior["label_zh"], "lower": lower, "upper": upper}
    prior = DEFAULT_BUCKET_PRIORS["8.00+"]
    return {"bucket": "8.00+", "label_zh": prior["label_zh"], "lower": 8.0, "upper": 999.0}


def bucket_prior(bucket: str) -> dict:
    return DEFAULT_BUCKET_PRIORS.get(bucket, {"alpha": 4.0, "beta": 12.0, "label_zh": "未知赔率段"})


def bayesian_bucket_rate(bucket: str, hits: int = 0, attempts: int = 0) -> dict:
    prior = bucket_prior(bucket)
    misses = max(0, int(attempts) - int(hits))
    alpha = float(prior["alpha"]) + max(0, int(hits))
    beta = float(prior["beta"]) + misses
    rate = alpha / (alpha + beta) if alpha + beta > 0 else 0.0
    return {
        "bucket": bucket,
        "bucket_label_zh": prior.get("label_zh", bucket),
        "posterior_hit_rate": round(rate, 6),
        "alpha": round(alpha, 3),
        "beta": round(beta, 3),
        "attempts": int(attempts),
        "hits": int(hits),
        "message_zh": _message(bucket, rate, attempts),
    }


def calibrate_probability(
    raw_model_prob: float | int | str | None,
    market_prob: float | int | str | None,
    odds: float | int | str | None,
    intelligence_score: float | int | str | None = None,
    bucket_hits: int = 0,
    bucket_attempts: int = 0,
    use_history: bool = True,
) -> dict:
    model = _bounded(raw_model_prob, 0.0, 1.0)
    market = _bounded(market_prob, 0.0, 1.0)
    if market <= 0:
        market = _implied_prob(odds) or model
    bucket = odds_bucket(odds)
    if use_history and bucket_attempts <= 0 and bucket_hits <= 0:
        learned = _learned_bucket_stats(bucket["bucket"])
        bucket_hits = int(learned.get("hits", 0) or 0)
        bucket_attempts = int(learned.get("attempts", 0) or 0)
    bucket_stats = bayesian_bucket_rate(bucket["bucket"], bucket_hits, bucket_attempts)
    bucket_rate = float(bucket_stats["posterior_hit_rate"])
    info = _bounded(intelligence_score, 0.0, 100.0) / 100.0 if intelligence_score is not None else 0.45
    sample_weight = min(0.30, max(0.0, bucket_attempts / 200.0))
    market_weight = 0.52 if bucket_attempts < 50 else 0.45
    model_weight = 0.28 if bucket_attempts < 50 else 0.30
    bucket_weight = 0.15 + sample_weight
    info_weight = 0.05
    total = market_weight + model_weight + bucket_weight + info_weight
    calibrated = (
        market * market_weight
        + model * model_weight
        + bucket_rate * bucket_weight
        + model * (0.80 + 0.40 * info) * info_weight
    ) / total
    penalty = longshot_penalty(odds, info)
    adjusted = max(0.0, min(1.0, calibrated * (1.0 - penalty)))
    probability_bin = _probability_bin(adjusted)
    probability_bin_stats = _learned_probability_bin_stats(probability_bin) if use_history else {}
    bin_adjustment = _probability_bin_adjustment(adjusted, probability_bin_stats)
    adjusted_with_bin = max(0.0, min(1.0, bin_adjustment["adjusted_prob"]))
    return {
        "raw_model_prob": round(model, 6),
        "market_prob": round(market, 6),
        "calibrated_prob": round(adjusted_with_bin, 6),
        "pre_probability_bin_prob": round(adjusted, 6),
        "bucket": bucket,
        "bucket_stats": bucket_stats,
        "probability_bin": probability_bin,
        "probability_bin_stats": probability_bin_stats,
        "probability_bin_weight": round(float(bin_adjustment["weight"]), 6),
        "intelligence_score": round(info * 100, 2),
        "longshot_penalty": round(penalty, 6),
        "message_zh": _calibration_message(model, adjusted_with_bin, bucket, penalty),
        "bin_adjustment_message_zh": _probability_bin_message(probability_bin, probability_bin_stats, bin_adjustment),
    }


def _learned_bucket_stats(bucket: str) -> dict:
    global _LEARNED_BUCKET_CACHE
    try:
        if _LEARNED_BUCKET_CACHE is not None:
            return _LEARNED_BUCKET_CACHE.get(bucket, {})
        from src.learning.history import bucket_prior_hit_rates

        _LEARNED_BUCKET_CACHE = bucket_prior_hit_rates()
        return _LEARNED_BUCKET_CACHE.get(bucket, {})
    except Exception:
        return {}


def _learned_probability_bin_stats(probability_bin: str) -> dict:
    global _LEARNED_PROBABILITY_BIN_CACHE
    try:
        if _LEARNED_PROBABILITY_BIN_CACHE is not None:
            return _LEARNED_PROBABILITY_BIN_CACHE.get(probability_bin, {})
        from src.learning.history import probability_bin_hit_rates

        _LEARNED_PROBABILITY_BIN_CACHE = probability_bin_hit_rates()
        return _LEARNED_PROBABILITY_BIN_CACHE.get(probability_bin, {})
    except Exception:
        return {}


def longshot_penalty(odds: float | int | str | None, intelligence_ratio: float = 0.45) -> float:
    value = _float(odds) or 0.0
    if value >= 10:
        return 0.30 + max(0.0, 0.60 - intelligence_ratio) * 0.15
    if value >= 8:
        return 0.24 + max(0.0, 0.60 - intelligence_ratio) * 0.12
    if value >= 6:
        return 0.18 + max(0.0, 0.60 - intelligence_ratio) * 0.10
    if value >= 4:
        return 0.08
    return 0.0


def _calibration_message(model: float, adjusted: float, bucket: dict, penalty: float) -> str:
    if penalty > 0:
        return f"{bucket.get('label_zh')}自动降权：原模型概率 {model:.1%}，校准后 {adjusted:.1%}。"
    return f"赔率段校准后概率 {adjusted:.1%}，用于排序而非保证命中。"


def _message(bucket: str, rate: float, attempts: int) -> str:
    if attempts <= 0:
        return f"{bucket} 暂无本地赛果样本，使用保守先验。"
    return f"{bucket} 本地样本 {attempts} 次，贝叶斯命中率 {rate:.1%}。"


def _probability_bin(probability: float) -> str:
    lower = int(max(0.0, min(0.999999, probability)) * 10) * 10
    upper = lower + 10
    return f"{lower}-{upper}%"


def _probability_bin_adjustment(probability: float, stats: dict) -> dict:
    attempts = int(stats.get("attempts", 0) or 0)
    observed = _float(stats.get("observed_hit_rate"))
    if attempts <= 0 or observed is None:
        return {"adjusted_prob": probability, "weight": 0.0}
    weight = min(0.12, max(0.0, attempts / 500.0))
    adjusted = probability * (1.0 - weight) + observed * weight
    return {"adjusted_prob": adjusted, "weight": weight}


def _probability_bin_message(probability_bin: str, stats: dict, adjustment: dict) -> str:
    attempts = int(stats.get("attempts", 0) or 0)
    weight = float(adjustment.get("weight") or 0.0)
    observed = _float(stats.get("observed_hit_rate"))
    avg_predicted = _float(stats.get("avg_predicted_prob"))
    if attempts <= 0 or observed is None:
        return f"{probability_bin} 概率段暂无本地赛后样本，暂不额外调整。"
    if attempts < 30:
        return (
            f"{probability_bin} 概率段仅 {attempts} 条样本，实际命中 {observed:.1%}，"
            f"只用 {weight:.1%} 极小权重约束排序。"
        )
    if avg_predicted is not None and observed + 0.08 < avg_predicted:
        return f"{probability_bin} 概率段历史命中低于预测，已保守降权。"
    if avg_predicted is not None and observed > avg_predicted + 0.08:
        return f"{probability_bin} 概率段历史命中高于预测，但仍需继续累计样本。"
    return f"{probability_bin} 概率段历史反馈接近预测，维持轻微校准。"


def _implied_prob(odds) -> float | None:
    value = _float(odds)
    if value and value > 1.0:
        return 1.0 / value
    return None


def _bounded(value, lower: float, upper: float) -> float:
    number = _float(value)
    if number is None:
        return lower
    return max(lower, min(upper, number))


def _float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

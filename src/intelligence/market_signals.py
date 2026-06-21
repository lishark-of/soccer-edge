from __future__ import annotations


def no_vig_probs(odds: dict[str, float | None] | None) -> dict[str, float]:
    report = market_probability_report(odds)
    return report.get("consensus_no_vig") or proportional_no_vig_probs(odds)


def proportional_no_vig_probs(odds: dict[str, float | None] | None) -> dict[str, float]:
    odds = odds or {}
    implied = {}
    for key, value in odds.items():
        if key == "handicap":
            continue
        try:
            odd = float(value)
        except (TypeError, ValueError):
            continue
        if odd > 1.01:
            normalized_key = {"win": "home", "lose": "away"}.get(key, key)
            implied[normalized_key] = 1.0 / odd
    total = sum(implied.values()) or 1.0
    return {key: round(value / total, 6) for key, value in implied.items()}


def power_no_vig_probs(odds: dict[str, float | None] | None) -> dict[str, float]:
    """Power method market-probability conversion.

    It keeps the rank order of implied probabilities but uses one exponent so
    probabilities sum to 1. This is a lightweight alternative to plain
    proportional no-vig and is useful for checking favourite/longshot bias.
    """
    implied = _implied_probs(odds)
    if not implied:
        return {}
    values = list(implied.values())
    if len(values) == 1:
        key = next(iter(implied))
        return {key: 1.0}
    if abs(sum(values) - 1.0) <= 1e-9:
        return {key: round(value, 6) for key, value in implied.items()}
    low, high = 0.01, 8.0
    for _ in range(80):
        mid = (low + high) / 2.0
        total = sum(value**mid for value in values)
        if total > 1.0:
            low = mid
        else:
            high = mid
    exponent = (low + high) / 2.0
    converted = {key: value**exponent for key, value in implied.items()}
    total = sum(converted.values()) or 1.0
    return {key: round(value / total, 6) for key, value in converted.items()}


def consensus_no_vig_probs(odds: dict[str, float | None] | None) -> dict[str, float]:
    """Blend proportional and power conversion as a conservative market prior."""
    proportional = proportional_no_vig_probs(odds)
    power = power_no_vig_probs(odds)
    shin = shin_no_vig_probs(odds)
    methods = [method for method in (proportional, power, shin) if method]
    keys = sorted(set().union(*(method.keys() for method in methods))) if methods else []
    if not keys:
        return {}
    blended = {
        key: sum(method.get(key, 0.0) for method in methods) / max(1, len([method for method in methods if key in method]))
        for key in keys
    }
    total = sum(blended.values()) or 1.0
    return {key: round(value / total, 6) for key, value in blended.items()}


def shin_no_vig_probs(odds: dict[str, float | None] | None) -> dict[str, float]:
    """Shin-style implied probability conversion.

    This is used as a cross-check for possible insider/favourite-longshot
    distortion. If the numerical solve is unstable, callers can safely fall
    back to proportional/power conversions.
    """
    implied = _implied_probs(odds)
    if not implied:
        return {}
    values = list(implied.values())
    book = sum(values)
    if book <= 1.0 + 1e-9:
        total = book or 1.0
        return {key: round(value / total, 6) for key, value in implied.items()}
    if len(values) == 1:
        key = next(iter(implied))
        return {key: 1.0}
    low, high = 0.0, min(0.99, 1.0 - 1e-9)
    for _ in range(80):
        mid = (low + high) / 2.0
        total = _shin_probability_sum(values, book, mid)
        if total > 1.0:
            low = mid
        else:
            high = mid
    z = (low + high) / 2.0
    converted = {key: _shin_probability(value, book, z) for key, value in implied.items()}
    total = sum(converted.values())
    if not total or any(value < 0 for value in converted.values()):
        return {}
    return {key: round(value / total, 6) for key, value in converted.items()}


def favorite_longshot_bias_report(odds: dict[str, float | None] | None) -> dict:
    proportional = proportional_no_vig_probs(odds)
    power = power_no_vig_probs(odds)
    shin = shin_no_vig_probs(odds)
    consensus = consensus_no_vig_probs(odds)
    rows = []
    for key in sorted(consensus):
        prop = proportional.get(key)
        pwr = power.get(key)
        shn = shin.get(key)
        cons = consensus.get(key)
        if prop is None or pwr is None or cons is None:
            continue
        method_values = [value for value in (prop, pwr, shn) if value is not None]
        method_shift = max(method_values) - min(method_values) if method_values else abs(prop - pwr)
        rows.append(
            {
                "outcome": key,
                "proportional_prob": prop,
                "power_prob": pwr,
                "shin_prob": shn,
                "consensus_prob": cons,
                "method_shift": round(method_shift, 6),
                "bias_bucket": _bias_bucket(cons),
                "message_zh": _bias_message(key, cons, method_shift),
            }
        )
    max_shift = max((row["method_shift"] for row in rows), default=0.0)
    longshot_rows = [row for row in rows if row["bias_bucket"] == "longshot"]
    favorite_rows = [row for row in rows if row["bias_bucket"] == "favorite"]
    if max_shift >= 0.05:
        status, label, confidence_penalty = "unstable", "方法分歧较大", 12
        message = "不同去水方法对概率判断差异较大，应降低 Edge/EV 自信，尤其谨慎高赔率冷门。"
    elif longshot_rows:
        status, label, confidence_penalty = "longshot_watch", "存在冷门偏差风险", 7
        message = "候选中存在低概率方向，需防止表面高 EV 来自冷门偏差。"
    else:
        status, label, confidence_penalty = "stable", "冷门偏差可控", 2
        message = "去水方法分歧较小，暂未发现明显冷门偏差风险。"
    return {
        "status": status,
        "label_zh": label,
        "confidence_penalty": confidence_penalty,
        "max_method_shift": round(max_shift, 6),
        "favorite_count": len(favorite_rows),
        "longshot_count": len(longshot_rows),
        "rows": rows,
        "message_zh": message,
    }


def market_probability_report(odds: dict[str, float | None] | None) -> dict:
    implied = _implied_probs(odds)
    proportional = proportional_no_vig_probs(odds)
    power = power_no_vig_probs(odds)
    shin = shin_no_vig_probs(odds)
    consensus = consensus_no_vig_probs(odds)
    bias = favorite_longshot_bias_report(odds) if implied else {}
    overround = sum(implied.values()) - 1.0 if implied else None
    max_shift = 0.0
    for key, value in proportional.items():
        max_shift = max(max_shift, abs(value - power.get(key, value)))
    if overround is None:
        status, label, score = "missing", "赔率缺失", 0
        message = "缺少有效赔率，无法进行市场概率转换。"
    elif overround < -0.02:
        status, label, score = "underround", "赔率异常", 42
        message = "隐含概率低于 100%，赔率可能缺失或来源异常。"
    elif overround <= 0.12 and max_shift <= 0.025:
        status, label, score = "strong", "市场转换稳定", 86
        message = "比例去水与 Power 转换差异较小，市场概率基准较稳定。"
    elif overround <= 0.18:
        status, label, score = "usable", "市场转换可用", 74
        message = "已进行比例去水与 Power 交叉检查，仍需结合冷门偏差与海外赔率。"
    else:
        status, label, score = "wide_margin", "水位较厚", 58
        message = "赔率水位较厚，简单去水可能偏差较大，应降低 Edge 自信。"
    return {
        "method_primary": "consensus_no_vig",
        "method_cross_check": "proportional_no_vig + power_no_vig + shin_style",
        "implied_sum": round(sum(implied.values()), 6) if implied else None,
        "overround": round(overround, 6) if overround is not None else None,
        "proportional_no_vig": proportional,
        "power_no_vig": power,
        "shin_no_vig": shin,
        "consensus_no_vig": consensus,
        "favorite_longshot_bias": bias,
        "max_method_shift": round(max_shift, 6),
        "status": status,
        "label_zh": label,
        "score": max(0, score - int((bias or {}).get("confidence_penalty", 0) * 0.35)),
        "message_zh": message,
    }


def odds_for_outcome(odds: dict[str, float | None] | None, outcome: str) -> float | None:
    odds = odds or {}
    key = {"home": "win", "away": "lose", "draw": "draw"}.get(outcome, outcome)
    value = odds.get(key)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _implied_probs(odds: dict[str, float | None] | None) -> dict[str, float]:
    odds = odds or {}
    implied = {}
    for key, value in odds.items():
        if key == "handicap":
            continue
        try:
            odd = float(value)
        except (TypeError, ValueError):
            continue
        if odd > 1.01:
            normalized_key = {"win": "home", "lose": "away"}.get(key, key)
            implied[normalized_key] = 1.0 / odd
    return implied


def _shin_probability(value: float, book: float, z: float) -> float:
    if z >= 1.0:
        return 0.0
    inside = z * z + 4.0 * (1.0 - z) * value * value / max(book, 1e-12)
    return (inside**0.5 - z) / (2.0 * (1.0 - z))


def _shin_probability_sum(values: list[float], book: float, z: float) -> float:
    return sum(_shin_probability(value, book, z) for value in values)


def _bias_bucket(prob: float) -> str:
    if prob >= 0.55:
        return "favorite"
    if prob <= 0.18:
        return "longshot"
    return "middle"


def _bias_message(outcome: str, prob: float, shift: float) -> str:
    label = {"home": "主胜", "draw": "平", "away": "客胜"}.get(outcome, outcome)
    if prob <= 0.18:
        return f"{label} 属于低概率方向，容易出现冷门偏差；若 EV 很高也要用赛后样本验证。"
    if shift >= 0.04:
        return f"{label} 在不同去水方法下差异较大，说明市场概率不稳定。"
    if prob >= 0.55:
        return f"{label} 属于热门方向，重点检查赔率是否太低、回报是否覆盖风险。"
    return f"{label} 处于中间概率区间，仍需结合模型与情报。"

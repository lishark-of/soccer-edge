from __future__ import annotations

import math


def build_market_benchmark_from_learning(learning_history: dict | None) -> dict:
    learning_history = learning_history or {}
    rows = _learning_outcome_rows(learning_history)
    usable = []
    for row in rows:
        model_prob = _safe_float(row.get("calibrated_prob") if row.get("calibrated_prob") is not None else row.get("model_prob"))
        market_prob = _safe_float(row.get("market_prob"))
        actual = _actual_binary(row)
        if model_prob is None or market_prob is None or actual is None:
            continue
        usable.append((max(0.0001, min(0.9999, model_prob)), max(0.0001, min(0.9999, market_prob)), actual))
    if not usable:
        return {
            "status": "missing",
            "sample_count": 0,
            "summary_zh": "暂无可比较的模型概率/市场概率/赛果样本，不能证明模型优于市场基准。",
        }
    model_brier = sum((model - actual) ** 2 for model, _market, actual in usable) / len(usable)
    market_brier = sum((market - actual) ** 2 for _model, market, actual in usable) / len(usable)
    model_log_loss = -sum(actual * math.log(model) + (1 - actual) * math.log(1 - model) for model, _market, actual in usable) / len(usable)
    market_log_loss = -sum(actual * math.log(market) + (1 - actual) * math.log(1 - market) for _model, market, actual in usable) / len(usable)
    skill = (market_brier - model_brier) / market_brier if market_brier > 0 else None
    status = "beating_market" if skill is not None and skill > 0 else "behind_market"
    return {
        "status": status,
        "sample_count": len(usable),
        "model_brier": round(model_brier, 6),
        "market_brier": round(market_brier, 6),
        "brier_skill_score": round(skill, 6) if skill is not None else None,
        "model_log_loss": round(model_log_loss, 6),
        "market_log_loss": round(market_log_loss, 6),
        "summary_zh": (
            f"模型相对市场 Brier Skill {skill:+.1%}，样本 {len(usable)} 条；模型 Brier {model_brier:.3f}，市场 Brier {market_brier:.3f}。"
            if skill is not None
            else f"样本 {len(usable)} 条，但市场 Brier 无法作为分母计算技能分。"
        ),
    }


def _learning_outcome_rows(learning_history: dict) -> list[dict]:
    rows = []
    for key in ("rows", "feedback_rows", "observations", "settled_rows"):
        value = learning_history.get(key)
        if isinstance(value, list):
            rows.extend([item for item in value if isinstance(item, dict)])
    for key in ("report", "feedback_report", "settlement_report"):
        value = learning_history.get(key)
        if isinstance(value, dict) and isinstance(value.get("rows"), list):
            rows.extend([item for item in value.get("rows") if isinstance(item, dict)])
    return rows


def _actual_binary(row: dict) -> int | None:
    if isinstance(row.get("hit"), bool):
        return 1 if row.get("hit") else 0
    value = str(row.get("result") or row.get("status") or row.get("settlement_status") or row.get("outcome") or "").lower()
    if value in {"hit", "win", "won", "success", "命中", "盈利"}:
        return 1
    if value in {"miss", "loss", "lost", "fail", "failed", "未命中", "亏损"}:
        return 0
    return None


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

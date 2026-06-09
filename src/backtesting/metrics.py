from __future__ import annotations

import math


def calculate_hit_rate(bets: list) -> float:
    if not bets:
        return 0.0
    return round(sum(1 for bet in bets if bet.get("hit")) / len(bets), 6)


def calculate_roi(bets: list) -> float:
    total_staked = sum(float(bet.get("stake", 0.0)) for bet in bets)
    if total_staked <= 0:
        return 0.0
    return round(calculate_pnl(bets) / total_staked, 6)


def calculate_pnl(bets: list) -> float:
    return round(sum(float(bet.get("profit", 0.0)) for bet in bets), 6)


def calculate_yield(bets: list) -> float:
    return calculate_roi(bets)


def calculate_average_odds(bets: list) -> float:
    if not bets:
        return 0.0
    return round(sum(float(bet.get("odds", 0.0)) for bet in bets) / len(bets), 6)


def calculate_max_drawdown(equity_curve: list[float]) -> float:
    peak = 0.0
    max_drawdown = 0.0
    for value in equity_curve:
        peak = max(peak, float(value))
        max_drawdown = max(max_drawdown, peak - float(value))
    return round(max_drawdown, 6)


def brier_score(predictions, outcome: int | None = None) -> float:
    if isinstance(predictions, (int, float)):
        return (float(predictions) - float(outcome or 0)) ** 2
    if not predictions:
        return 0.0
    total = 0.0
    for prediction in predictions:
        actual = prediction.get("actual")
        probs = prediction.get("probabilities", {})
        total += sum((float(probs.get(outcome_name, 0.0)) - (1.0 if outcome_name == actual else 0.0)) ** 2 for outcome_name in ("win", "draw", "lose"))
    return round(total / len(predictions), 6)


def log_loss(predictions, outcome: int | None = None, eps: float = 1e-12) -> float:
    if isinstance(predictions, (int, float)):
        probability = min(1 - eps, max(eps, float(predictions)))
        return -math.log(probability if outcome else 1 - probability)
    if not predictions:
        return 0.0
    total = 0.0
    for prediction in predictions:
        actual = prediction.get("actual")
        probs = prediction.get("probabilities", {})
        probability = min(1 - eps, max(eps, float(probs.get(actual, 0.0))))
        total += -math.log(probability)
    return round(total / len(predictions), 6)


def summarize_backtest(bets: list, predictions: list[dict]) -> dict:
    equity_curve = []
    running = 0.0
    for bet in bets:
        running += float(bet.get("profit", 0.0))
        equity_curve.append(running)
    warnings = []
    if not bets:
        warnings.append("no bets selected by baseline strategy")
    return {
        "sample_size": len(predictions),
        "bets": len(bets),
        "hit_rate": calculate_hit_rate(bets),
        "pnl": calculate_pnl(bets),
        "roi": calculate_roi(bets),
        "yield": calculate_yield(bets),
        "average_odds": calculate_average_odds(bets),
        "max_drawdown": calculate_max_drawdown(equity_curve),
        "brier_score": brier_score(predictions),
        "log_loss": log_loss(predictions),
        "warnings": warnings,
    }

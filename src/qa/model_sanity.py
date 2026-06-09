from __future__ import annotations

import math

from src.qa.checks import QaCheckResult


def check_probability_dict(
    probs: dict,
    name: str = "probabilities",
    tolerance: float = 1e-6,
) -> list[QaCheckResult]:
    results = []
    if not isinstance(probs, dict):
        return [QaCheckResult(name, False, message=f"{name} must be a dict")]
    keys = ("win", "draw", "lose") if {"win", "draw", "lose"}.issubset(probs) else ("home", "draw", "away")
    values = [probs.get(key) for key in keys]
    finite = all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in values)
    in_range = finite and all(0 <= float(value) <= 1 for value in values)
    total = sum(float(value) for value in values) if finite else 0.0
    results.append(QaCheckResult(f"{name}.finite", finite, message=f"{name} probabilities are finite"))
    results.append(QaCheckResult(f"{name}.range", in_range, message=f"{name} probabilities are in [0, 1]"))
    results.append(
        QaCheckResult(
            f"{name}.sum",
            finite and abs(total - 1.0) <= tolerance,
            message=f"{name} probabilities sum to 1",
            details={"sum": round(total, 8)},
        )
    )
    return results


def check_analysis_output(analysis: dict) -> list[QaCheckResult]:
    results = [
        QaCheckResult("analysis.warnings", "warnings" in analysis, severity="warning", message="analysis includes warnings"),
        QaCheckResult("analysis.provider", bool(analysis.get("provider_used")), message="analysis includes provider_used"),
    ]
    for section in ("single_candidates",):
        for index, item in enumerate(analysis.get(section, [])):
            odds = item.get("odds")
            ev = item.get("ev")
            results.append(QaCheckResult(f"analysis.{section}.{index}.odds", isinstance(odds, (int, float)) and odds > 1, message="odds > 1"))
            results.append(QaCheckResult(f"analysis.{section}.{index}.ev", isinstance(ev, (int, float)) and math.isfinite(ev), message="EV is finite"))
    return results


def check_backtest_output(report: dict) -> list[QaCheckResult]:
    results = [
        QaCheckResult("backtest.sample_size", "sample_size" in report.get("metrics", {}), message="metrics include sample size"),
        QaCheckResult("backtest.metrics", isinstance(report.get("metrics"), dict), message="backtest includes metrics"),
    ]
    if not report.get("bets"):
        results.append(QaCheckResult("backtest.empty_bets", True, severity="warning", message="empty bets are allowed"))
    for key in ("roi", "pnl", "max_drawdown", "brier_score", "log_loss"):
        value = report.get("metrics", {}).get(key)
        results.append(QaCheckResult(f"backtest.metric.{key}", value is None or (isinstance(value, (int, float)) and math.isfinite(value)), message=f"{key} is finite or None"))
    return results


def check_calibration_artifact(artifact: dict) -> list[QaCheckResult]:
    results = [
        QaCheckResult("calibration.version", artifact.get("artifact_version") == "calibration_v1", message="artifact version is calibration_v1"),
        QaCheckResult("calibration.model_version", bool(artifact.get("model_version")), message="artifact has model_version"),
    ]
    for outcome, bins in artifact.get("calibration", {}).items():
        for index, item in enumerate(bins):
            for key in ("avg_predicted_prob", "observed_frequency"):
                value = item.get(key)
                results.append(QaCheckResult(f"calibration.{outcome}.{index}.{key}", isinstance(value, (int, float)) and 0 <= value <= 1, message=f"{key} in [0, 1]"))
    return results

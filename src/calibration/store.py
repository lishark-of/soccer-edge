from __future__ import annotations

from datetime import datetime, timezone


def build_calibration_artifact(
    backtest_report: dict,
    model_version: str,
) -> dict:
    calibration = backtest_report.get("calibration", {}).get("bins", {})
    metrics = backtest_report.get("metrics", {})
    return {
        "artifact_version": "calibration_v1",
        "model_version": model_version,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": {
            "backtest_matches": backtest_report.get("matches_evaluated", 0),
            "bets_total": backtest_report.get("bets_total", 0),
        },
        "calibration": {
            "win": calibration.get("win", []),
            "draw": calibration.get("draw", []),
            "lose": calibration.get("lose", []),
        },
        "metrics": {
            "brier_score": metrics.get("brier_score"),
            "log_loss": metrics.get("log_loss"),
        },
        "warnings": list(backtest_report.get("warnings", [])),
    }


def validate_calibration_artifact(artifact: dict) -> list[str]:
    issues: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact must be a JSON object"]
    if artifact.get("artifact_version") != "calibration_v1":
        issues.append("artifact_version must be calibration_v1")
    if not artifact.get("model_version"):
        issues.append("model_version is required")
    calibration = artifact.get("calibration")
    if not isinstance(calibration, dict):
        issues.append("calibration must be an object")
    else:
        for outcome in ("win", "draw", "lose"):
            if outcome not in calibration or not isinstance(calibration.get(outcome), list):
                issues.append(f"calibration.{outcome} must be a list")
    return issues

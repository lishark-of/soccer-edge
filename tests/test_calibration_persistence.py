from src.calibration.persistence import load_calibration_artifact, save_calibration_artifact
from src.calibration.store import build_calibration_artifact, validate_calibration_artifact


def test_build_and_validate_calibration_artifact():
    report = {
        "matches_evaluated": 12,
        "bets_total": 3,
        "calibration": {"bins": {"win": [], "draw": [], "lose": []}},
        "metrics": {"brier_score": 0.4, "log_loss": 1.2},
        "warnings": [],
    }
    artifact = build_calibration_artifact(report, "model")
    assert validate_calibration_artifact(artifact) == []


def test_save_and_load_calibration_artifact(tmp_path):
    artifact = {
        "artifact_version": "calibration_v1",
        "model_version": "model",
        "calibration": {"win": [], "draw": [], "lose": []},
    }
    path = tmp_path / "calibration.json"
    save_calibration_artifact(artifact, str(path))
    assert load_calibration_artifact(str(path))["artifact_version"] == "calibration_v1"


def test_invalid_calibration_artifact_returns_warnings():
    assert validate_calibration_artifact({"artifact_version": "bad"})

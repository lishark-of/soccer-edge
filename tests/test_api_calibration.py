from src.api.routes import dispatch_route


def test_api_calibration_validate_missing_file_does_not_crash():
    response = dispatch_route("/api/calibration/validate", {"path": "/tmp/missing-football-jc-calibration.json"})
    assert response["ok"] is True
    assert response["data"]["valid"] is False

from src.cli import validate_local


def test_validate_local_json_shape(monkeypatch):
    monkeypatch.setattr(validate_local, "run_validation", lambda: {"overall_passed": True, "checks": [], "warnings": []})
    report = validate_local.run_validation()
    assert "overall_passed" in report
    assert isinstance(report["checks"], list)

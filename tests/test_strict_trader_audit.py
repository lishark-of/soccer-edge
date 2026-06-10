from src.cli.strict_trader_audit import run_strict_trader_audit


def test_strict_trader_audit_json_shape():
    report = run_strict_trader_audit(".")
    assert report["audit_version"] == "phase2o_strict_trader_audit_v0"
    assert "summary" in report
    assert "endpoint_summary" in report


def test_strict_trader_audit_static_checks_pass():
    report = run_strict_trader_audit(".")
    failed_static = [c for c in report["checks"] if c["name"].startswith("audit.home") and not c["passed"]]
    assert failed_static == []

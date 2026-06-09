from src.paper_trading.diagnostics import diagnose_operation


def test_diagnostics_flags_large_drawdown():
    report = {"max_drawdown": 0.2, "observation_count": 30, "combo_summary": {}, "fixture_warning": False}
    diagnostics = diagnose_operation(report)
    assert any("回撤" in item["title"] for item in diagnostics["issues"])

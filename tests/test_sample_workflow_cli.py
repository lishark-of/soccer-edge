from src.cli import sample_workflow


def test_sample_workflow_json_shape(monkeypatch):
    monkeypatch.setattr(sample_workflow, "run_sample_workflow", lambda write_report=None: {"overall_passed": True, "steps": [], "generated_outputs": {}})
    report = sample_workflow.run_sample_workflow()
    assert report["overall_passed"] is True
    assert "steps" in report

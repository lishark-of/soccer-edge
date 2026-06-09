from src.qa.runner import run_qa


def test_qa_runner_json_shape():
    payload = run_qa(".", rehearsal=False)
    assert payload["qa_version"] == "phase2f_qa_harness_v0"
    assert "summary" in payload
    assert "checks" in payload

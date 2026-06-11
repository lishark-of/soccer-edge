from src.audit.user_journey import run_user_acceptance_audit


def test_user_acceptance_audit_json_shape():
    result = run_user_acceptance_audit(".")
    assert "overall_passed" in result
    assert isinstance(result["pages_checked"], list)
    assert "credibility_score" in result

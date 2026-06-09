from src.explain.deepseek_explainer import explain_with_optional_deepseek
from src.qa.network_safety import check_no_default_external_calls


def test_no_default_external_calls_in_validation(monkeypatch):
    monkeypatch.delenv("FOOTBALL_JC_LLM_ENABLED", raising=False)
    calls = {"count": 0}

    def fake_transport(*args):
        calls["count"] += 1
        return {"choices": [{"message": {"content": "unused"}}]}

    explain_with_optional_deepseek("candidate", {"edge": 0.01}, {"provider": "deepseek", "transport": fake_transport})
    assert calls["count"] == 0
    assert all(item.passed for item in check_no_default_external_calls())

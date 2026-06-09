from src.explain.deepseek_explainer import explain_with_optional_deepseek


def test_deepseek_explainer_falls_back_when_disabled(monkeypatch):
    monkeypatch.delenv("FOOTBALL_JC_LLM_ENABLED", raising=False)
    result = explain_with_optional_deepseek("candidate", {"model_prob": 0.52, "fair_prob": 0.45, "edge": 0.07, "ev": 0.05})
    assert result["provider"] == "local"
    assert result["status"] == "disabled"


def test_deepseek_explainer_falls_back_on_unsafe_output(monkeypatch):
    monkeypatch.setenv("FOOTBALL_JC_LLM_ENABLED", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    def fake_transport(url, headers, body, timeout):
        return {"choices": [{"message": {"content": "必中。"}}]}

    result = explain_with_optional_deepseek(
        "candidate",
        {"model_prob": 0.52, "fair_prob": 0.45, "edge": 0.07, "ev": 0.05},
        {"provider": "deepseek", "transport": fake_transport},
    )
    assert result["provider"] == "local"
    assert result["status"] == "fallback_local"

import pytest

from src.explain.llm_explainer import LlmExplainerUnavailable, explain_with_llm, is_llm_explainer_enabled


def test_llm_explainer_disabled_by_default(monkeypatch):
    monkeypatch.delenv("LLM_EXPLAINER_ENABLED", raising=False)
    assert is_llm_explainer_enabled() is False


def test_llm_explainer_stub_makes_no_external_call(monkeypatch):
    monkeypatch.delenv("LLM_EXPLAINER_ENABLED", raising=False)
    with pytest.raises(LlmExplainerUnavailable):
        explain_with_llm("explain", {})

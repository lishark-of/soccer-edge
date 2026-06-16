from src.explain.deepseek_client import DeepSeekClientError
from src.explain.deepseek_explainer import explain_with_optional_deepseek


class _SuccessClient:
    def complete(self, messages, temperature=0.2):
        return {"text": "DS 研究摘要", "token_in": 120, "token_out": 34, "token_total": 154}


class _FailClient:
    def complete(self, messages, temperature=0.2):
        raise DeepSeekClientError("rate limited", code="rate_limited", user_message_zh="DeepSeek 请求过于频繁，已改用本地摘要。")


class _TimeoutClient:
    def complete(self, messages, temperature=0.2):
        raise DeepSeekClientError("timed out", code="request_timeout", user_message_zh="DeepSeek 请求超时，已改用本地摘要。")


def test_explainer_returns_ds_telemetry(monkeypatch):
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_API_KEY", "demo-key")
    result = explain_with_optional_deepseek("combo_research", {"sample": True}, {"provider": "auto", "client": _SuccessClient()})
    assert result["provider"] == "deepseek"
    assert result["ds_status"] == "loaded"
    assert result["ds_attempted"] is True
    assert result["ds_completed"] is True
    assert result["ds_status_zh"] == "DS Pro 已参与"
    assert result["token_in"] == 120
    assert result["token_out"] == 34
    assert result["token_total"] == 154
    assert result["fallback_reason"] == ""
    assert result["display_status_zh"] == "DS Pro 已参与本次研究。"


def test_explainer_returns_fallback_reason_when_ds_fails(monkeypatch):
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_API_KEY", "demo-key")
    result = explain_with_optional_deepseek("combo_research", {"sample": True}, {"provider": "auto", "client": _FailClient()})
    assert result["provider"] == "local"
    assert result["ds_status"] == "error"
    assert result["ds_attempted"] is True
    assert result["ds_completed"] is False
    assert result["ds_error_code"] == "rate_limited"
    assert "改用本地摘要" in result["fallback_reason"]
    assert result["display_status_zh"] == result["fallback_reason"]


def test_explainer_returns_timeout_status(monkeypatch):
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_API_KEY", "demo-key")
    result = explain_with_optional_deepseek("combo_research", {"sample": True}, {"provider": "auto", "client": _TimeoutClient()})
    assert result["provider"] == "local"
    assert result["ds_error_code"] == "request_timeout"
    assert "请求超时" in result["fallback_reason"]

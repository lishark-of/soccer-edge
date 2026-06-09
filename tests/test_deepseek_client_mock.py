import pytest

from src.explain.deepseek_client import DeepSeekClient, DeepSeekClientError
from src.explain.deepseek_config import DeepSeekConfig


def _config(enabled=True, key=True):
    return DeepSeekConfig(enabled=enabled, provider="deepseek", api_key_present=key, base_url="https://api.deepseek.com", model="deepseek-v4-flash", timeout_seconds=1, max_tokens=100)


def test_deepseek_client_uses_injected_transport(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    calls = []

    def fake_transport(url, headers, body, timeout):
        calls.append((url, headers, body, timeout))
        return {"choices": [{"message": {"content": "概率模型不保证结果，回测不代表未来，串关会放大风险。"}}]}

    client = DeepSeekClient(config=_config(), transport=fake_transport)
    text = client.explain([{"role": "user", "content": "hello"}])
    assert "概率模型不保证结果" in text
    assert calls and calls[0][0].endswith("/chat/completions")


def test_deepseek_client_missing_key_errors_cleanly(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = DeepSeekClient(config=_config(enabled=True, key=False), transport=lambda *args: {})
    with pytest.raises(DeepSeekClientError) as exc:
        client.explain([])
    assert "missing" in str(exc.value).lower()

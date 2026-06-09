from src.api.routes import dispatch_route


def test_api_llm_status_hides_api_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-value")
    payload = dispatch_route("/api/llm/status", {})
    assert payload["ok"] is True
    assert payload["data"]["api_key_present"] is True
    assert "secret-value" not in str(payload)

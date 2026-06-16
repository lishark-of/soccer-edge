from src.api.routes import dispatch_route
from src.explain.deepseek_runtime import reset_runtime_status, update_runtime_status


def test_api_llm_status_exposes_token_aliases_for_frontend():
    reset_runtime_status()
    update_runtime_status(
        provider_requested="auto",
        provider_target="deepseek",
        provider_resolved="deepseek",
        ds_status="loaded",
        ds_status_zh="DS Pro 已参与",
        ds_attempted=True,
        ds_completed=True,
        ds_error_code="",
        fallback_reason="",
        token_in=321,
        token_out=123,
        token_total=444,
    )
    payload = dispatch_route("/api/llm/status", {})
    assert payload["ok"] is True
    data = payload["data"]
    assert data["token_in"] == 321
    assert data["token_out"] == 123
    assert data["token_total"] == 444
    assert data["last_token_in"] == 321
    assert data["last_token_out"] == 123
    assert data["last_token_total"] == 444

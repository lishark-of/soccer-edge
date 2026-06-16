from src.explain.deepseek_client import DeepSeekClientError
from src.explain.deepseek_config import llm_status_payload
from src.explain.deepseek_explainer import explain_with_optional_deepseek
from src.explain.deepseek_runtime import reset_runtime_status, update_runtime_status


class _SuccessClient:
    def complete(self, messages, temperature=0.2):
        return {"text": "DS 研究摘要", "token_in": 200, "token_out": 80, "token_total": 280}


class _FailClient:
    def complete(self, messages, temperature=0.2):
        raise DeepSeekClientError("invalid key", code="invalid_api_key", user_message_zh="DeepSeek Key 无效，已改用本地摘要。")


def test_llm_status_shows_runtime_success(monkeypatch):
    reset_runtime_status()
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_API_KEY", "demo-key")
    explain_with_optional_deepseek("combo_research", {"sample": True}, {"provider": "auto", "client": _SuccessClient()})
    payload = llm_status_payload()
    assert payload["status"] == "ready"
    assert payload["runtime_status"] == "loaded"
    assert payload["ds_attempted"] is True
    assert payload["ds_completed"] is True
    assert payload["ds_error_code"] == ""
    assert payload["last_provider_resolved"] == "deepseek"
    assert payload["last_token_in"] == 200
    assert payload["last_token_out"] == 80
    assert payload["last_token_total"] == 280


def test_llm_status_shows_runtime_failure(monkeypatch):
    reset_runtime_status()
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_API_KEY", "demo-key")
    explain_with_optional_deepseek("combo_research", {"sample": True}, {"provider": "auto", "client": _FailClient()})
    payload = llm_status_payload()
    assert payload["status"] == "ready"
    assert payload["runtime_status"] == "error"
    assert payload["ds_attempted"] is True
    assert payload["ds_completed"] is False
    assert payload["ds_error_code"] == "invalid_api_key"
    assert payload["last_error_code"] == "invalid_api_key"
    assert payload["last_error_label_zh"] == "Key 无效"
    assert "Key 无效" in payload["status_detail_zh"]


def test_llm_status_reads_persisted_runtime_across_processes(monkeypatch, tmp_path):
    status_path = tmp_path / "ds_runtime_status.json"
    monkeypatch.setenv("JC_EDGE_RUNTIME_STATUS_PATH", str(status_path))
    reset_runtime_status()
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_API_KEY", "demo-key")
    explain_with_optional_deepseek("combo_research", {"sample": True}, {"provider": "auto", "client": _SuccessClient()})
    reset_runtime_status(delete_persisted=False)
    payload = llm_status_payload()
    assert payload["runtime_status"] == "loaded"
    assert payload["ds_attempted"] is True
    assert payload["ds_completed"] is True
    assert payload["last_token_total"] == 280


def test_llm_status_distinguishes_clean_cache_hit_from_failed_fallback(monkeypatch):
    reset_runtime_status()
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_API_KEY", "demo-key")
    update_runtime_status(
        provider_requested="auto",
        provider_target="deepseek",
        provider_resolved="deepseek",
        ds_status="cached",
        ds_status_zh="已复用最近一次 DS 研究",
        ds_attempted=True,
        ds_completed=True,
        ds_error_code="",
        fallback_reason="",
        token_in=100,
        token_out=40,
        token_total=140,
    )
    payload = llm_status_payload()
    assert payload["runtime_status"] == "cached"
    assert payload["ai_research_status"]["status"] == "cached"
    assert payload["ai_research_status"]["summary_zh"] == "已复用最近一次成功的 DS 研究结果，本轮未重复调用 DS Pro。"
    assert payload["next_step_zh"] == "当前可直接查看缓存研究；如需获取最新解释，可手动刷新今日观察或赛前优化。"

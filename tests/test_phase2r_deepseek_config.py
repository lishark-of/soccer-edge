from src.explain.deepseek_config import load_deepseek_config, llm_status_payload


def test_deepseek_is_disabled_by_default(monkeypatch):
    for name in [
        "JC_EDGE_DEEPSEEK_ENABLED",
        "FOOTBALL_JC_LLM_ENABLED",
        "JC_EDGE_DEEPSEEK_API_KEY",
        "DEEPSEEK_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)
    config = load_deepseek_config()
    status = llm_status_payload()
    assert config.enabled is False
    assert status["status"] == "disabled"
    assert status["external_calls_default"] is False
    assert "config_status_zh" in status
    assert "runtime_notice_zh" in status
    assert "next_step_zh" in status


def test_deepseek_pro_env_aliases_are_supported(monkeypatch):
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_MAX_INPUT_TOKENS", "7000")
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_MAX_OUTPUT_TOKENS", "900")
    config = load_deepseek_config()
    status = llm_status_payload()
    assert config.enabled is True
    assert config.api_key_present is True
    assert config.model == "deepseek-chat"
    assert config.max_input_tokens == 7000
    assert config.max_tokens == 900
    assert status["safe_usage"] == "optional_explainer_only"
    assert "DeepSeek 已就绪" in status["config_status_zh"]

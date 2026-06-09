from src.explain.deepseek_config import load_deepseek_config


def test_deepseek_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FOOTBALL_JC_LLM_ENABLED", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    config = load_deepseek_config()
    assert config.enabled is False
    assert config.model == "deepseek-v4-flash"


def test_deepseek_config_does_not_expose_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-value")
    config = load_deepseek_config()
    assert config.api_key_present is True
    assert "secret" not in repr(config)

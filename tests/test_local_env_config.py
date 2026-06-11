from src.config.local_env import build_secret_config_status, save_local_env_values
from src.api.routes import dispatch_post_route
import src.config.local_env as local_env


def test_save_local_env_masks_keys(tmp_path, monkeypatch):
    env_path = tmp_path / ".env.local"
    monkeypatch.delenv("JC_EDGE_API_FOOTBALL_KEY", raising=False)
    status = save_local_env_values({"JC_EDGE_API_FOOTBALL_KEY": "abc123456789"}, env_path)
    key_status = {item["key"]: item for item in status["keys"]}
    assert key_status["JC_EDGE_API_FOOTBALL_KEY"]["configured"] is True
    assert key_status["JC_EDGE_API_FOOTBALL_KEY"]["masked"] == "abc...6789"
    assert "abc123456789" not in str(status)
    assert env_path.exists()


def test_secret_config_status_does_not_require_existing_env(tmp_path, monkeypatch):
    monkeypatch.delenv("JC_EDGE_THE_ODDS_API_KEY", raising=False)
    status = build_secret_config_status(tmp_path / ".env.local")
    key_status = {item["key"]: item for item in status["keys"]}
    assert key_status["JC_EDGE_THE_ODDS_API_KEY"]["configured"] is False
    assert key_status["JC_EDGE_THE_ODDS_API_KEY"]["masked"] == "未配置"


def test_post_local_env_route_returns_masked_status(monkeypatch, tmp_path):
    monkeypatch.setattr(local_env, "DEFAULT_ENV_PATH", tmp_path / ".env.local")
    monkeypatch.delenv("JC_EDGE_THE_ODDS_API_KEY", raising=False)
    response = dispatch_post_route("/api/config/local-env", {"JC_EDGE_THE_ODDS_API_KEY": "odds_test_123456"})
    assert response["ok"] is True
    assert "odds_test_123456" not in str(response)
    keys = {item["key"]: item for item in response["data"]["keys"]}
    assert keys["JC_EDGE_THE_ODDS_API_KEY"]["configured"] is True

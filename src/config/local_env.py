from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env.local"
ALLOWED_SECRET_KEYS = {
    "JC_EDGE_API_FOOTBALL_KEY": "API-Football / API-Sports",
    "JC_EDGE_THE_ODDS_API_KEY": "The Odds API",
    "JC_EDGE_DEEPSEEK_API_KEY": "DeepSeek Pro 解释层",
    "JC_EDGE_OPENROUTER_API_KEY": "OpenRouter 解释层",
}
ALLOWED_CONFIG_KEYS = {
    "JC_EDGE_DEEPSEEK_ENABLED": "DeepSeek optional explainer enabled",
    "JC_EDGE_LLM_PROVIDER": "LLM provider",
    "JC_EDGE_DEEPSEEK_MODEL": "DeepSeek model",
    "JC_EDGE_DEEPSEEK_MAX_INPUT_TOKENS": "DeepSeek max input tokens",
    "JC_EDGE_DEEPSEEK_MAX_OUTPUT_TOKENS": "DeepSeek max output tokens",
}
ALLOWED_LOCAL_KEYS = {**ALLOWED_SECRET_KEYS, **ALLOWED_CONFIG_KEYS}


def load_local_env(path: str | Path | None = None, override: bool = False) -> dict[str, str]:
    env_path = Path(path) if path else DEFAULT_ENV_PATH
    values = _read_env_file(env_path)
    for key, value in values.items():
        if key in ALLOWED_LOCAL_KEYS and (override or not os.getenv(key)):
            os.environ[key] = value
    return values


def build_secret_config_status(path: str | Path | None = None) -> dict:
    env_path = Path(path) if path else DEFAULT_ENV_PATH
    values = load_local_env(env_path)
    keys = []
    for key, label in ALLOWED_SECRET_KEYS.items():
        value = os.getenv(key) or values.get(key) or ""
        keys.append(
            {
                "key": key,
                "label": label,
                "configured": bool(value),
                "masked": mask_secret(value),
                "source": str(env_path) if value else "not_configured",
            }
        )
    return {
        "config_version": "local_env_config_v0",
        "env_path": str(env_path),
        "env_file_exists": env_path.exists(),
        "keys": keys,
        "notes_zh": [
            ".env.local 已在 .gitignore 中，不会被正常提交。",
            "页面保存时不会返回完整 key，只显示是否配置和尾号掩码。",
            "DeepSeek/OpenRouter/GPT 等解释层只做解释研究，不参与概率、EV 或候选筛选。",
        ],
    }


def save_local_env_values(updates: dict[str, object], path: str | Path | None = None) -> dict:
    env_path = Path(path) if path else DEFAULT_ENV_PATH
    env_path.parent.mkdir(parents=True, exist_ok=True)
    current = _read_env_file(env_path)
    changed: list[str] = []
    for key in ALLOWED_LOCAL_KEYS:
        raw = updates.get(key)
        if raw is None:
            continue
        value = str(raw).strip()
        if not value:
            continue
        current[key] = value
        os.environ[key] = value
        changed.append(key)
    if updates.get("JC_EDGE_DEEPSEEK_API_KEY") and str(updates.get("JC_EDGE_DEEPSEEK_API_KEY")).strip():
        defaults = {
            "JC_EDGE_DEEPSEEK_ENABLED": "true",
            "JC_EDGE_LLM_PROVIDER": "deepseek",
            "JC_EDGE_DEEPSEEK_MODEL": "deepseek-v4-pro",
            "JC_EDGE_DEEPSEEK_MAX_INPUT_TOKENS": "24000",
            "JC_EDGE_DEEPSEEK_MAX_OUTPUT_TOKENS": "4000",
            "JC_EDGE_DEEPSEEK_TIMEOUT_SECONDS": "120",
        }
        for key, value in defaults.items():
            if not current.get(key):
                current[key] = value
                os.environ[key] = value
                changed.append(key)
    _write_env_file(env_path, current)
    try:
        env_path.chmod(0o600)
    except OSError:
        pass
    status = build_secret_config_status(env_path)
    status["changed_keys"] = changed
    status["message_zh"] = "本地 key 配置已保存；完整密钥不会显示在页面或响应中。" if changed else "没有收到新的 key，现有配置保持不变。"
    return status


def get_secret(key: str) -> str | None:
    load_local_env()
    value = os.getenv(key)
    return value.strip() if value else None


def mask_secret(value: str | None) -> str:
    if not value:
        return "未配置"
    text = str(value)
    if len(text) <= 8:
        return "已配置（长度较短，已隐藏）"
    return f"{text[:3]}...{text[-4:]}"


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in ALLOWED_LOCAL_KEYS:
            values[key] = value
    return values


def _write_env_file(path: Path, values: dict[str, str]) -> None:
    preserved_lines: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("# JC Edge local-only secrets") or stripped.startswith("# Full keys are read locally"):
                continue
            if stripped.startswith("# API-Football") or stripped.startswith("# The Odds API") or stripped.startswith("# OpenRouter") or stripped.startswith("# DeepSeek") or stripped.startswith("# LLM"):
                continue
            key = stripped.split("=", 1)[0].strip() if "=" in stripped else ""
            if key not in ALLOWED_LOCAL_KEYS:
                preserved_lines.append(line)

    lines = list(preserved_lines)
    if lines:
        lines.append("")
    lines.extend([
        "# JC Edge local-only secrets. Do not commit this file.",
        "# Full keys are read locally and never rendered back by the App.",
    ])
    for key, label in ALLOWED_SECRET_KEYS.items():
        value = values.get(key, "")
        lines.append(f"# {label}")
        lines.append(f"{key}={value}")
    config_keys = [
        "JC_EDGE_DEEPSEEK_ENABLED",
        "JC_EDGE_LLM_PROVIDER",
        "JC_EDGE_DEEPSEEK_MODEL",
        "JC_EDGE_DEEPSEEK_TIMEOUT_SECONDS",
        "JC_EDGE_DEEPSEEK_MAX_INPUT_TOKENS",
        "JC_EDGE_DEEPSEEK_MAX_OUTPUT_TOKENS",
    ]
    if any(values.get(key) for key in config_keys):
        lines.append("# DeepSeek optional explainer config")
        for key in config_keys:
            value = values.get(key, "")
            if value:
                lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

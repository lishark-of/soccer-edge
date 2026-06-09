from pathlib import Path


def test_dashboard_deepseek_ui_mentions_optional_disabled():
    text = "\n".join((Path("src/dashboard/static") / name).read_text(encoding="utf-8") for name in ["index.html", "app.js", "glossary.js"])
    assert "DeepSeek" in text
    assert "解释模式" in text
    assert "默认" in text or "disabled" in text
    assert "API Key" not in (Path("src/dashboard/static/index.html").read_text(encoding="utf-8"))

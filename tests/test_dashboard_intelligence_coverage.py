from pathlib import Path


def test_dashboard_uses_intelligence_coverage_copy():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    js = Path("src/dashboard/static/app.js").read_text(encoding="utf-8")
    assert "情报覆盖状态" in html
    assert "情报已补齐" not in html
    assert "用户已提供字段" in js

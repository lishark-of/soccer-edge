from pathlib import Path


def test_dashboard_contains_quick_start():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    assert "Quick Start" in html
    assert "快速启动" in html


def test_dashboard_contains_version_and_read_only_mode():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    assert "Version 0.1.0-local" in html
    assert "Read-only local analysis mode" in html

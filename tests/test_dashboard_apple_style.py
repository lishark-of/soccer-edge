from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
CSS = (ROOT / "src/dashboard/static/style.css").read_text(encoding="utf-8")


def test_app_title_is_jc_edge():
    assert "<title>JC Edge</title>" in HTML
    assert "<h1>JC Edge</h1>" in HTML
    assert "竞猜足球概率分析台" not in HTML


def test_dashboard_has_apple_style_tokens():
    assert "--bg: #f5f5f7" in CSS
    assert "--blue: #0071e3" in CSS
    assert "backdrop-filter" in CSS
    assert "border-radius: var(--radius-xl)" in CSS
    assert "-apple-system" in CSS


def test_dashboard_respects_reduced_motion():
    assert "prefers-reduced-motion" in CSS


def test_dashboard_no_external_assets():
    assert "https://" not in HTML
    assert "cdn" not in HTML.lower()

from pathlib import Path


HTML = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")


def test_dashboard_static_contains_read_only_disclaimer():
    assert "Read-only local analysis mode" in HTML
    assert "No betting, payment, order placement, or proxy purchase features are implemented." in HTML


def test_dashboard_static_has_no_external_cdn():
    assert "https://" not in HTML
    assert "cdn" not in HTML.lower()

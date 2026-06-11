from pathlib import Path


def test_dashboard_has_best_parlay_page():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    assert "优秀串联" in html
    assert "风险调整最佳" in html

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_has_research_archive_status_panel():
    html = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
    app = (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")
    assert "researchArchivePanel" in html
    assert "researchArchiveDetailPanel" in html
    assert "autoArchiveResearch" in app
    assert "/api/learning/auto-archive-research" in app
    assert "Brier、Log Loss、ROI 和 CLV" in app
    assert "CLV待填" in app
    assert "查看优先回填收盘赔率" in app


def test_dashboard_research_archive_has_no_positive_order_controls():
    html = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
    app = (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")
    combined = html + app
    forbidden_controls = ["立即购买", "一键投注", "自动投注", "下单按钮", "支付按钮", "代购入口"]
    assert not any(text in combined for text in forbidden_controls)

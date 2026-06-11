from pathlib import Path


def test_dashboard_has_credibility_page():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    assert "可信度审计" in html
    assert "严厉交易者复盘" in html


def test_dashboard_has_no_betting_controls():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    for word in ["购买", "下单", "支付", "代购"]:
        assert f">{word}<" not in html

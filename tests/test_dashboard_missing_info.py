from pathlib import Path


def test_dashboard_has_missing_info_intake():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    assert "情报补齐" in html
    assert "externalSignalsPath" in html


def test_dashboard_no_payment_order_controls():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    for word in ["购买", "下单", "支付", "代购"]:
        assert f">{word}<" not in html

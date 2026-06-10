from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "src/dashboard/static/index.html").read_text(encoding="utf-8")


def test_dashboard_has_intelligence_pages():
    for text in ["赛前情报", "赛前观察总览", "比分 / 总进球", "缺失情报"]:
        assert text in HTML


def test_dashboard_intelligence_has_no_transaction_controls():
    button_text = " ".join(part.split("</button>")[0] for part in HTML.split("<button")[1:])
    for forbidden in ["下注", "投注", "购买", "下单", "支付", "代购"]:
        assert forbidden not in button_text

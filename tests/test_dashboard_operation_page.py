from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")


def test_dashboard_has_operation_page():
    for text in ["模拟走盘", "初始模拟本金", "最终模拟本金", "总盈亏", "走盘明细", "问题诊断"]:
        assert text in HTML


def test_dashboard_operation_page_has_no_betting_controls():
    button_text = " ".join(part.split("</button>")[0] for part in HTML.split("<button")[1:])
    for forbidden in ["下注", "投注", "购买", "下单", "支付", "代购"]:
        assert forbidden not in button_text


def test_dashboard_operation_page_mentions_profit_explanation():
    assert "为什么赚/亏" in HTML

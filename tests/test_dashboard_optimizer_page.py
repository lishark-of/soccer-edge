from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")


def test_dashboard_has_optimizer_page():
    for text in ["赛前优化", "今日赛前组合优化", "生成观察组合", "放弃的候选", "风险解释"]:
        assert text in HTML


def test_dashboard_optimizer_page_has_no_betting_controls():
    button_text = " ".join(part.split("</button>")[0] for part in HTML.split("<button")[1:])
    for forbidden in ["下注", "投注", "购买", "下单", "支付", "代购"]:
        assert forbidden not in button_text

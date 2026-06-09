import re
from pathlib import Path

STATIC = Path("src/dashboard/static")


def _combined():
    return "\n".join((STATIC / name).read_text(encoding="utf-8") for name in ["index.html", "app.js", "style.css", "components.js", "glossary.js"])


def test_dashboard_contains_chinese_user_facing_labels():
    text = _combined()
    assert "竞彩足球概率分析台" in text
    assert "指定日期分析" in text
    assert "数据导入预检" in text


def test_dashboard_has_probability_backtest_section():
    assert "概率回测" in _combined()


def test_dashboard_no_external_cdn():
    text = _combined().lower()
    assert "https://" not in text
    assert "fonts.googleapis" not in text
    assert "cdn" not in text


def test_dashboard_no_betting_controls():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    labels = [re.sub(r"<.*?>", "", item).strip() for item in re.findall(r"<button[^>]*>.*?</button>", html, flags=re.S)]
    forbidden = {"投注", "立即购买", "下单", "支付", "代购", "跟单", "自动投注", "追号", "倍投", "回血"}
    for label in labels:
        assert label not in forbidden

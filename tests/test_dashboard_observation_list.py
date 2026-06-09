from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
JS = (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")


def test_dashboard_has_observation_language_not_betting_language():
    assert "观察清单" in HTML
    assert "加入观察" in JS
    assert "移出观察" in JS
    button_text = "\n".join(part.split("</button>")[0] for part in HTML.split("<button")[1:])
    for forbidden in ["下注", "立即购买", "下单", "支付", "代购", "跟单", "自动投注", "追号", "倍投", "回血", "必中", "稳赢", "稳赚", "杀庄", "保本"]:
        assert forbidden not in button_text

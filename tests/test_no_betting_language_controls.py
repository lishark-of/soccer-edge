from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")


def test_no_betting_payment_order_controls():
    labels = re.findall(r"<button[^>]*>(.*?)</button>", HTML, flags=re.S)
    joined = " ".join(re.sub(r"<.*?>", "", label) for label in labels)
    for forbidden in ["下注", "投注", "立即购买", "下单", "支付", "代购", "跟单", "自动投注", "追号", "倍投", "回血", "必中", "稳赢", "稳赚", "杀庄", "保本"]:
        assert forbidden not in joined

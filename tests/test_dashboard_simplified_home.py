from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")


def test_home_has_today_observation_and_top_blocks():
    for text in ["今日观察", "Top 单关观察", "Top 2串1观察", "Top 总进球观察", "Top 比分观察"]:
        assert text in HTML


def test_advanced_settings_closed_by_default():
    assert '<details id="advancedSettings"' in HTML
    assert '<details id="advancedSettings" open' not in HTML


def test_no_default_technical_panel():
    assert "操作面板" not in HTML
    assert "API Base" not in HTML
    assert "sidebar" not in HTML


def test_no_positive_transaction_buttons():
    for label in ["下注", "投注", "购买", "下单", "支付", "代购"]:
        assert f">{label}<" not in HTML

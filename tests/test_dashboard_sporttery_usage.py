from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")


def test_dashboard_has_six_step_usage_path():
    for text in ["先用 mock 数据体验", "查看竞彩足球比赛", "导入自己的历史 CSV", "运行概率回测", "生成校准文件", "查看候选信号与组合风险"]:
        assert text in HTML


def test_dashboard_has_sporttery_section():
    assert "中国体育彩票竞彩足球" in HTML
    assert "Sporttery" in HTML
    assert "provider_used" in HTML


def test_dashboard_has_read_only_safety_copy():
    assert "本地只读" in HTML
    assert "不提供投注、下单、支付、代购或自动化购彩能力" in HTML

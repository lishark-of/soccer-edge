from pathlib import Path


def test_dashboard_home_has_six_step_onboarding():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    for text in ["使用 mock 数据体验", "导入历史 CSV", "查看字段识别结果", "运行概率回测", "生成 calibration artifact", "查看明日分析与候选风险解释"]:
        assert text in html


def test_dashboard_import_page_mentions_field_report():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    assert "字段识别结果" in html
    assert "缺字段与修复建议" in html


def test_dashboard_backtest_page_mentions_probability_backtest():
    html = Path("src/dashboard/static/index.html").read_text(encoding="utf-8")
    assert "概率回测" in html
    assert "指标解释" in html

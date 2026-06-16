from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_has_clv_and_backtest_credibility_sections():
    html = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
    assert "CLV / 收盘赔率复盘" in html
    assert "CSV 回测可信度" in html
    assert "DeepSeek Pro 解释层默认关闭" in html
    assert "DeepSeek Pro key" in (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")


def test_dashboard_home_is_top_observation_first():
    html = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
    today = html.split('id="view-today"', 1)[1].split('id="view-credibility"', 1)[0]
    assert today.index("Top 单关观察") < today.index("情报覆盖状态")
    assert "API Base" not in today


def test_deepseek_status_copy_is_explainer_only():
    html = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")
    combined = html + app_js
    assert "不参与概率、EV、候选筛选或组合决策" in combined
    assert "/api/llm/status" in app_js


def test_dashboard_today_copy_mentions_no_combo_and_ds_state():
    app_js = (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")
    assert "暂不组合：" in app_js
    assert "DS 已参与" in app_js
    assert "配置：" in app_js
    assert "区间复盘：" in app_js
    assert "学习结论：" in app_js
    assert "今日结论" in app_js
    assert "当前暂不强行串联" in app_js
    assert "DAILY REPORT" in app_js
    assert "WINDOW REPORTS" in app_js

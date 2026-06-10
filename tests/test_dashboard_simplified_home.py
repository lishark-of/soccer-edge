from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
JS = (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")


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


def test_score_goals_page_mentions_handicap_probability():
    assert "让球胜平负概率" in HTML
    assert "概率矩阵完整性" in HTML


def test_parlay_page_shows_rejected_candidate_sections():
    assert "2串1 被拒候选" in HTML
    assert "3串1 被拒候选" in HTML
    assert "被拒组合原因" in HTML or "被拒组合" in HTML or "被拒候选" in HTML
    assert "Top 2串1被拒原因" in HTML
    assert "Top 3串1被拒原因" in HTML


def test_import_page_shows_user_csv_replay_path():
    assert "用户 CSV 复盘路径" in HTML
    assert "下一步" in HTML


def test_import_page_shows_backtest_calibration_quality_notes():
    for text in ["CSV 复盘就绪度", "预检质量检查", "完整 workflow 交接", "回测怎么读", "校准文件说明", "数据质量提示"]:
        assert text in HTML


def test_observation_tables_show_support_opposition_and_missing_signals():
    for text in ["支持因素", "反对因素", "缺失情报"]:
        assert text in JS


def test_home_shows_external_signal_load_status():
    assert "情报读取状态" in JS

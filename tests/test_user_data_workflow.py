from src.cli.user_data_workflow import preview_user_data_workflow, run_user_data_workflow


def test_user_data_workflow_json_shape(tmp_path):
    result = run_user_data_workflow(
        "data/fixtures/user_onboarding_sample.csv",
        mapping_path="data/fixtures/user_onboarding_mapping_example.json",
        output_dir=str(tmp_path / "normalized"),
    )
    assert result["workflow_version"] == "phase2j_user_data_workflow_v0"
    assert "field_report" in result
    assert "user_view" in result


def test_user_data_workflow_generates_paths_under_ignored_dirs():
    result = preview_user_data_workflow("data/fixtures/user_onboarding_sample.csv", "data/fixtures/user_onboarding_mapping_example.json")
    assert result["normalized_output_path"] is None
    assert result["user_view"]["steps"]


def test_user_workflow_preview_explains_backtest_calibration_next_steps():
    result = preview_user_data_workflow("data/fixtures/user_onboarding_sample.csv", "data/fixtures/user_onboarding_mapping_example.json")
    view = result["user_view"]
    titles = [step["title"] for step in view["steps"]]
    assert "运行概率回测" in titles
    assert "生成校准文件" in titles
    assert view["next_steps"]


def test_user_data_workflow_includes_readable_diagnostics(tmp_path):
    result = run_user_data_workflow(
        "data/fixtures/user_onboarding_sample.csv",
        mapping_path="data/fixtures/user_onboarding_mapping_example.json",
        output_dir=str(tmp_path / "normalized"),
    )
    assert "workflow_summary" in result
    assert result["backtest_explanation"]
    assert result["calibration_explanation"]
    assert result["data_quality_notes"]
    assert "不代表未来表现" in "；".join(result["backtest_explanation"])


def test_user_workflow_preview_has_readable_placeholder_explanations():
    result = preview_user_data_workflow("data/fixtures/user_onboarding_sample.csv", "data/fixtures/user_onboarding_mapping_example.json")
    view = result["user_view"]
    assert view["workflow_summary"]
    assert view["readiness_cards"]
    assert view["readiness_table"]
    assert view["preflight_quality"]
    assert view["preflight_checks"]
    assert view["cli_handoff"]
    assert view["backtest_explanation"]
    assert view["calibration_explanation"]
    assert view["data_quality_notes"]


def test_user_workflow_readiness_explains_preview_boundary():
    result = preview_user_data_workflow("data/fixtures/user_onboarding_sample.csv", "data/fixtures/user_onboarding_mapping_example.json")
    rows = {row["item"]: row for row in result["user_view"]["readiness_table"]}
    assert rows["字段预检"]["status"] == "ready"
    assert rows["赔率覆盖"]["status"] == "ready"
    assert rows["标准化 CSV"]["status"] == "pending"
    assert "App 预览不写文件" in rows["标准化 CSV"]["meaning_zh"]


def test_user_workflow_preflight_quality_estimates_backtest_readiness():
    result = preview_user_data_workflow("data/fixtures/user_onboarding_sample.csv", "data/fixtures/user_onboarding_mapping_example.json")
    quality = result["user_view"]["preflight_quality"]
    checks = {row["item"]: row for row in result["user_view"]["preflight_checks"]}
    assert quality["rows_normalized"] >= 30
    assert quality["had_odds_coverage"] == 1.0
    assert quality["backtest_preflight_status"] == "ready"
    assert checks["回测准备度"]["status"] == "ready"


def test_user_workflow_replay_readiness_summary_is_actionable():
    result = preview_user_data_workflow("data/fixtures/user_onboarding_sample.csv", "data/fixtures/user_onboarding_mapping_example.json")
    summary = result["user_view"]["replay_readiness_summary"]
    assert summary["label"] == "可进入完整复盘"
    assert summary["score"] >= 80
    assert "CLI 完整执行" in summary["next_action_zh"]
    assert "不保证未来表现" in summary["calibration_note_zh"]
    assert any("赔率覆盖" in item for item in summary["proof_points"])


def test_user_workflow_cli_handoff_is_cli_only_and_ignored_outputs():
    result = preview_user_data_workflow("data/fixtures/user_onboarding_sample.csv", "data/fixtures/user_onboarding_mapping_example.json")
    handoff = result["user_view"]["cli_handoff"]
    assert handoff["mode"] == "cli_only_write_step"
    assert "python3 -m src.cli.user_data_workflow" in handoff["command"]
    assert "--mapping data/fixtures/user_onboarding_mapping_example.json" in handoff["command"]
    assert len(handoff["expected_outputs"]) == 2
    assert all(item["git_policy"] == "ignored" for item in handoff["expected_outputs"])

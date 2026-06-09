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

from src.cli.user_data_workflow import run_user_data_workflow


def test_errors_are_chinese_and_no_traceback():
    result = run_user_data_workflow("missing-file.csv")
    text = "\n".join(result.get("warnings", []))
    assert "文件不存在" in text
    assert "Traceback" not in text
    assert "KeyError" not in text

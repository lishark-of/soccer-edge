from src.qa.git_hygiene import check_generated_paths_not_tracked


def test_git_hygiene_generated_paths_not_tracked():
    results = check_generated_paths_not_tracked(".")
    assert all(result.passed for result in results)

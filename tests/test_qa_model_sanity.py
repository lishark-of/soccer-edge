from src.qa.model_sanity import check_probability_dict


def test_check_probability_dict_accepts_valid_probs():
    results = check_probability_dict({"win": 0.4, "draw": 0.3, "lose": 0.3})
    assert all(result.passed for result in results)


def test_check_probability_dict_rejects_bad_sum():
    results = check_probability_dict({"win": 0.4, "draw": 0.3, "lose": 0.2})
    assert any(result.name.endswith(".sum") and not result.passed for result in results)

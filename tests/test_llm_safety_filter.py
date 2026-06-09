from src.explain.safety import enforce_safe_explanation, validate_explanation_safety


def test_safety_filter_rejects_banned_terms():
    issues = validate_explanation_safety("这是必中方案")
    assert issues


def test_safety_filter_falls_back_on_violation():
    fallback = "本地解释：概率模型不保证结果，回测结果不保证未来表现。"
    assert enforce_safe_explanation("必中", fallback) == fallback

from src.qa.disclaimers import check_text_disclaimers


SAFE_TEXT = "仅供数据研究与娱乐参考。不提供投注、下单、支付、代购或任何自动化购彩能力。概率模型不保证结果。回测结果不保证未来表现。串关会显著放大风险。"


def test_disclaimer_scan_requires_safety_language():
    results = check_text_disclaimers("missing", "test")
    assert any(result.name.startswith("disclaimer.required") and not result.passed for result in results)


def test_disclaimer_scan_rejects_promotional_terms():
    results = check_text_disclaimers(SAFE_TEXT + " 必中", "test")
    assert any(result.name == "disclaimer.banned.必中" and not result.passed for result in results)

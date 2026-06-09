from pathlib import Path


def test_onboarding_docs_include_safety_boundaries():
    text = Path("docs/onboarding_guide.md").read_text(encoding="utf-8")
    assert "本地只读" in text
    assert "不提供投注、下单、支付、代购或任何自动化购彩能力" in text
    assert "不要把 API Key 写进 Git" in text

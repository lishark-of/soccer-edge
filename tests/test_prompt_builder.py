from src.explain.prompt_builder import build_backtest_explanation_prompt, build_candidate_explanation_prompt


def _joined(messages):
    return "\n".join(item["content"] for item in messages)


def test_prompt_builder_contains_no_betting_instruction():
    text = _joined(build_candidate_explanation_prompt({"home_team": "A", "away_team": "B"}))
    assert "不要给出投注指令" in text
    assert "不要承诺命中" in text


def test_prompt_builder_requires_uncertainty_language():
    text = _joined(build_backtest_explanation_prompt({"metrics": {"roi": 0.01}}))
    assert "概率模型不保证结果" in text
    assert "回测不代表未来" in text

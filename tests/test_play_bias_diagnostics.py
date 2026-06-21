from src.optimizer.play_bias import diagnose_play_bias


def test_play_bias_flags_hhad_concentration():
    diagnostics = diagnose_play_bias(
        {
            "singles": [
                {"play_type": "hhad", "direction": "让胜"},
                {"play_type": "hhad", "direction": "让胜"},
                {"play_type": "hhad", "direction": "让胜"},
                {"play_type": "had", "direction": "主胜"},
            ],
            "parlay_2x1": [
                {
                    "legs": [
                        {"play_type": "hhad", "direction": "让胜"},
                        {"play_type": "hhad", "direction": "让胜"},
                    ]
                },
                {
                    "legs": [
                        {"play_type": "hhad", "direction": "让胜"},
                        {"play_type": "hhad", "direction": "让胜"},
                    ]
                },
            ],
        }
    )
    assert diagnostics["status"] == "biased"
    assert "玩法偏置" in diagnostics["label_zh"]
    assert any(section["status"] in {"concentrated", "very_concentrated"} for section in diagnostics["sections"])


def test_play_bias_balanced_when_play_types_are_mixed():
    diagnostics = diagnose_play_bias(
        {
            "singles": [
                {"play_type": "had", "direction": "主胜"},
                {"play_type": "hhad", "direction": "让胜"},
                {"play_type": "total_goals", "direction": "总进球 2"},
            ],
            "parlay_2x1": [],
        }
    )
    assert diagnostics["sections"][0]["status"] == "balanced"
    assert diagnostics["status"] == "balanced"

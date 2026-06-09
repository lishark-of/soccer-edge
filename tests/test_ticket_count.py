import pytest

from src.domain.selection import Selection
from src.rules.parlay_builder import build_parlay_combinations
from src.rules.ticket_count import calculate_ticket_count


def _selection(match_id: str, match_no: str) -> Selection:
    return Selection(
        match_id=match_id,
        match_no=match_no,
        league="测试联赛",
        home_team="A",
        away_team="B",
        play_type="had",
        outcome_key="home",
        outcome_label="胜",
        odds=1.8,
        fair_prob=0.5,
        model_prob=0.56,
        edge=0.06,
        ev=0.008,
        confidence=0.56,
        risk_level="medium",
        risk_score=0.3,
    )


def test_2x1_ticket_count():
    selections = [_selection("m1", "001"), _selection("m2", "002")]

    assert calculate_ticket_count(selections, "2x1") == 1


def test_3x1_ticket_count():
    selections = [_selection("m1", "001"), _selection("m2", "002"), _selection("m3", "003")]

    assert calculate_ticket_count(selections, "3x1") == 1


def test_mixed_parlay_combinations():
    selections = [_selection("m1", "001"), _selection("m2", "002"), _selection("m3", "003")]
    parlays = build_parlay_combinations(selections, "2x1")

    assert len(parlays) == 3


def test_invalid_pass_type_rejected():
    selections = [_selection("m1", "001"), _selection("m2", "002")]

    with pytest.raises(ValueError):
        calculate_ticket_count(selections, "4x1")

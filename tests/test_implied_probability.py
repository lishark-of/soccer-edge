from src.probability.implied_probability import calculate_implied_probabilities
from src.probability.no_vig import remove_vig


def test_implied_probability_sum_greater_than_one_before_no_vig():
    odds = {"home": 1.82, "draw": 3.45, "away": 4.20}
    implied = calculate_implied_probabilities(odds)

    assert sum(implied.values()) > 1.0


def test_no_vig_probability_sums_to_one():
    odds = {"home": 1.82, "draw": 3.45, "away": 4.20}
    implied = calculate_implied_probabilities(odds)
    fair = remove_vig(implied)

    assert round(sum(fair.values()), 6) == 1.0

from src.probability.poisson_model import (
    derive_1x2_probs,
    derive_handicap_probs,
    poisson_pmf,
    scoreline_distribution,
)


def test_poisson_distribution_sums_close_to_one():
    dist = scoreline_distribution(1.8, 1.1)

    assert abs(sum(dist.values()) - 1.0) < 1e-6


def test_derive_1x2_probs_sums_to_one():
    dist = scoreline_distribution(1.5, 1.2)
    probs = derive_1x2_probs(dist)

    assert abs(sum(probs.values()) - 1.0) < 1e-6


def test_poisson_rejects_non_positive_xg():
    try:
        scoreline_distribution(0.0, 1.0)
        assert False, "expected ValueError"
    except ValueError:
        assert True


def test_handicap_probs_sum_to_one():
    dist = scoreline_distribution(1.9, 1.0)
    probs = derive_handicap_probs(dist, -1.0)

    assert abs(sum(probs.values()) - 1.0) < 1e-6
    assert poisson_pmf(2, 1.5) > 0

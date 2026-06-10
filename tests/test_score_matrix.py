from src.models.score_matrix import build_score_matrix, outcome_probabilities, top_scores, total_goals_distribution


def test_score_matrix_outputs_probabilities():
    matrix = build_score_matrix(1.6, 0.9)
    assert abs(sum(matrix.values()) - 1.0) < 1e-6
    outcomes = outcome_probabilities(matrix)
    assert abs(sum(outcomes.values()) - 1.0) < 1e-6
    assert len(top_scores(matrix, 5)) == 5


def test_total_goals_distribution_normalized():
    dist = total_goals_distribution(build_score_matrix(1.2, 1.2))
    assert abs(sum(dist.values()) - 1.0) < 1e-6
    assert "7+" in dist

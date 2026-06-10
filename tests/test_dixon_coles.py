from src.models.dixon_coles import apply_dixon_coles_adjustment
from src.models.score_matrix import build_score_matrix


def test_dixon_coles_preserves_normalization():
    matrix = build_score_matrix(1.4, 1.1)
    adjusted = apply_dixon_coles_adjustment(matrix)
    assert abs(sum(adjusted.values()) - 1.0) < 1e-6
    assert adjusted[(0, 0)] > matrix[(0, 0)]

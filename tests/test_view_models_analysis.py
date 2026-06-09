from src.view_models.analysis_view import build_analysis_view
from src.view_models.import_view import build_import_preview_view
from src.view_models.calibration_view import build_calibration_view


def test_analysis_view_has_summary_cards():
    view = build_analysis_view(
        {
            "matches_analyzed": 2,
            "provider_used": "mock",
            "single_candidates": [
                {
                    "home_team": "Alpha FC",
                    "away_team": "Beta United",
                    "play_type": "had",
                    "outcome_label": "主胜",
                    "odds": 2.1,
                    "fair_prob": 0.45,
                    "model_prob": 0.52,
                    "edge": 0.07,
                    "ev": 0.092,
                    "risk_level": "medium",
                    "model_components": {"market": {}, "weights": {}},
                }
            ],
            "parlay_2x1_candidates": [],
            "parlay_3x1_candidates": [],
        }
    )
    assert view["summary_cards"]
    assert view["candidate_tables"]["single"]


def test_import_view_handles_missing_fields():
    view = build_import_preview_view({})
    assert view["summary_cards"]
    assert view["warnings"] == []


def test_calibration_view_handles_invalid_artifact():
    view = build_calibration_view({"path": "missing.json", "valid": False, "issues": ["missing"]})
    assert view["warnings"] == ["missing"]

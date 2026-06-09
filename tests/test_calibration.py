from src.backtesting.calibration import calibration_bins, reliability_summary


def test_calibration_bins_shape():
    bins = calibration_bins([{"actual": True, "prob": 0.72}, {"actual": False, "prob": 0.22}], n_bins=5)
    assert bins
    assert {"bin_start", "bin_end", "count", "avg_predicted_prob", "observed_frequency", "gap"}.issubset(bins[0])


def test_reliability_summary_multiclass():
    summary = reliability_summary([{"actual": "win", "probabilities": {"win": 0.7, "draw": 0.2, "lose": 0.1}}])
    assert summary["sample_size"] == 1
    assert "win" in summary["bins"]

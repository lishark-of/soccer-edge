from __future__ import annotations


def calibration_bins(
    predictions: list[dict],
    outcome_key: str = "actual",
    prob_key: str = "prob",
    n_bins: int = 10,
) -> list[dict]:
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")
    buckets: dict[int, list[dict]] = {}
    for prediction in predictions:
        probability = float(prediction.get(prob_key, 0.0))
        probability = max(0.0, min(1.0, probability))
        index = min(n_bins - 1, int(probability * n_bins))
        buckets.setdefault(index, []).append(prediction)
    result = []
    for index in sorted(buckets):
        items = buckets[index]
        avg_prob = sum(float(item.get(prob_key, 0.0)) for item in items) / len(items)
        observed = sum(1.0 for item in items if bool(item.get(outcome_key))) / len(items)
        result.append(
            {
                "bin_start": round(index / n_bins, 6),
                "bin_end": round((index + 1) / n_bins, 6),
                "count": len(items),
                "avg_predicted_prob": round(avg_prob, 6),
                "observed_frequency": round(observed, 6),
                "gap": round(avg_prob - observed, 6),
            }
        )
    return result


def multiclass_calibration_bins(predictions: list[dict], n_bins: int = 10) -> dict:
    output: dict[str, list[dict]] = {}
    for outcome in ("win", "draw", "lose"):
        binary_predictions = [
            {
                "actual": prediction.get("actual") == outcome,
                "prob": prediction.get("probabilities", {}).get(outcome, 0.0),
            }
            for prediction in predictions
        ]
        output[outcome] = calibration_bins(binary_predictions, n_bins=n_bins)
    return output


def reliability_summary(predictions: list[dict], n_bins: int = 10) -> dict:
    bins = multiclass_calibration_bins(predictions, n_bins=n_bins)
    gaps = [abs(item["gap"]) for outcome_bins in bins.values() for item in outcome_bins]
    return {
        "n_bins": n_bins,
        "sample_size": len(predictions),
        "bins": bins,
        "mean_absolute_gap": round(sum(gaps) / len(gaps), 6) if gaps else 0.0,
        "note": "Calibration is diagnostic and does not guarantee future outcomes.",
    }

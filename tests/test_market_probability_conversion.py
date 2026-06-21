from src.intelligence.market_signals import (
    consensus_no_vig_probs,
    favorite_longshot_bias_report,
    market_probability_report,
    no_vig_probs,
    power_no_vig_probs,
    shin_no_vig_probs,
)


def test_power_no_vig_probs_normalize_to_one():
    probs = power_no_vig_probs({"win": 2.0, "draw": 3.4, "lose": 3.8})
    assert round(sum(probs.values()), 6) == 1.0
    assert set(probs) == {"home", "draw", "away"}


def test_market_probability_report_has_conversion_quality():
    report = market_probability_report({"win": 2.0, "draw": 3.4, "lose": 3.8})
    assert report["method_primary"] == "consensus_no_vig"
    assert report["method_cross_check"] == "proportional_no_vig + power_no_vig + shin_style"
    assert report["overround"] is not None
    assert report["consensus_no_vig"]
    assert report["shin_no_vig"]
    assert report["favorite_longshot_bias"]["status"] in {"stable", "longshot_watch", "unstable"}
    assert report["score"] > 0
    assert "市场" in report["label_zh"] or "赔率" in report["label_zh"]


def test_consensus_no_vig_probs_is_default_market_prior():
    odds = {"win": 1.35, "draw": 4.8, "lose": 8.8}
    consensus = consensus_no_vig_probs(odds)
    assert round(sum(consensus.values()), 6) == 1.0
    assert no_vig_probs(odds) == consensus


def test_favorite_longshot_bias_report_flags_longshots():
    report = favorite_longshot_bias_report({"win": 1.35, "draw": 4.8, "lose": 8.8})
    assert report["longshot_count"] >= 1
    assert report["confidence_penalty"] >= 2
    assert any(row["bias_bucket"] == "longshot" for row in report["rows"])


def test_shin_no_vig_probs_normalize_to_one():
    probs = shin_no_vig_probs({"win": 1.85, "draw": 3.45, "lose": 4.35})
    assert round(sum(probs.values()), 6) == 1.0
    assert set(probs) == {"home", "draw", "away"}

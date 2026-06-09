from __future__ import annotations

from src.domain.match import Match
from src.domain.odds import MarketOdds, OddsHistory
from src.modeling.team_strength import estimate_xg_for_match
from src.probability.elo_model import DEFAULT_INITIAL_RATING, elo_to_1x2_probs
from src.probability.poisson_model import derive_1x2_probs, derive_handicap_probs, scoreline_distribution


DEFAULT_WEIGHTS = {
    "market": 0.65,
    "poisson": 0.20,
    "elo": 0.15,
}


def combine_probabilities(
    market_no_vig: dict,
    poisson_probs: dict | None = None,
    elo_probs: dict | None = None,
    weights: dict | None = None,
) -> dict:
    chosen_weights = dict(DEFAULT_WEIGHTS)
    if weights:
        chosen_weights.update(weights)

    market_component = _canonicalize_probs(market_no_vig)
    poisson_component = _canonicalize_probs(poisson_probs) if poisson_probs else None
    elo_component = _canonicalize_probs(elo_probs) if elo_probs else None

    active_components = {
        "market": market_component,
        "poisson": poisson_component,
        "elo": elo_component,
    }
    active_weights = {
        name: chosen_weights[name]
        for name, component in active_components.items()
        if component is not None
    }
    total_weight = sum(active_weights.values()) or 1.0
    normalized_weights = {name: 0.0 for name in DEFAULT_WEIGHTS}
    for name, value in active_weights.items():
        normalized_weights[name] = value / total_weight

    probabilities = {"win": 0.0, "draw": 0.0, "lose": 0.0}
    for name, component in active_components.items():
        if component is None:
            continue
        for outcome in probabilities:
            probabilities[outcome] += normalized_weights[name] * component[outcome]

    return {
        "probabilities": _normalize(probabilities),
        "components": {
            "market": market_component,
            "poisson": poisson_component,
            "elo": elo_component,
            "weights": {key: round(value, 6) for key, value in normalized_weights.items()},
        },
    }


def build_model_probabilities(
    match: Match,
    market: MarketOdds,
    fair_probabilities: dict[str, float],
    odds_history: OddsHistory | None = None,
    *,
    team_strengths: dict | None = None,
    elo_ratings: dict[str, float] | None = None,
) -> tuple[dict[str, float], float, list[str], dict[str, object]]:
    del odds_history  # reserved for future versions
    market_component = {
        "win": fair_probabilities["home"],
        "draw": fair_probabilities["draw"],
        "lose": fair_probabilities["away"],
    }

    poisson_component = None
    home_xg = None
    away_xg = None
    if team_strengths and int(team_strengths.get("sample_size", 0)) > 0:
        home_xg, away_xg = estimate_xg_for_match(match, team_strengths)
        distribution = scoreline_distribution(home_xg, away_xg)
        if market.play_type == "had":
            poisson_component = derive_1x2_probs(distribution)
        elif market.play_type == "hhad" and market.handicap is not None:
            poisson_component = derive_handicap_probs(distribution, market.handicap)

    elo_component = None
    if elo_ratings and market.play_type == "had":
        home_rating = float(elo_ratings.get(match.home_team, DEFAULT_INITIAL_RATING))
        away_rating = float(elo_ratings.get(match.away_team, DEFAULT_INITIAL_RATING))
        elo_component = elo_to_1x2_probs(home_rating, away_rating)
    else:
        home_rating = away_rating = DEFAULT_INITIAL_RATING

    combined = combine_probabilities(
        market_component,
        poisson_probs=poisson_component,
        elo_probs=elo_component,
    )
    probabilities = combined["probabilities"]
    mapped = {
        "home": probabilities["win"],
        "draw": probabilities["draw"],
        "away": probabilities["lose"],
    }
    confidence = round(max(mapped.values()), 6)

    reasons = [
        f"market no-vig baseline active，玩法={market.play_type}",
        f"ensemble weights market={combined['components']['weights']['market']:.2f} poisson={combined['components']['weights']['poisson']:.2f} elo={combined['components']['weights']['elo']:.2f}",
    ]
    if poisson_component is not None and home_xg is not None and away_xg is not None:
        reasons.append(f"poisson baseline xg home={home_xg:.2f} away={away_xg:.2f}")
    if elo_component is not None:
        reasons.append(f"elo baseline ratings home={home_rating:.1f} away={away_rating:.1f}")
    if poisson_component is None and elo_component is None:
        reasons.append("historical model unavailable; market-only fallback")

    return mapped, confidence, reasons, combined["components"]


def _canonicalize_probs(probabilities: dict | None) -> dict[str, float] | None:
    if probabilities is None:
        return None
    if {"home", "draw", "away"}.issubset(probabilities.keys()):
        return _normalize(
            {
                "win": float(probabilities["home"]),
                "draw": float(probabilities["draw"]),
                "lose": float(probabilities["away"]),
            }
        )
    if {"win", "draw", "lose"}.issubset(probabilities.keys()):
        return _normalize(
            {
                "win": float(probabilities["win"]),
                "draw": float(probabilities["draw"]),
                "lose": float(probabilities["lose"]),
            }
        )
    return None


def _normalize(probabilities: dict[str, float]) -> dict[str, float]:
    total = sum(max(value, 0.0) for value in probabilities.values())
    if total <= 0:
        return {key: round(1.0 / len(probabilities), 6) for key in probabilities}
    return {key: round(max(value, 0.0) / total, 6) for key, value in probabilities.items()}

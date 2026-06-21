from __future__ import annotations

from src.intelligence.confidence import confidence_score
from src.intelligence.lineup_signals import injury_signal, lineup_signal
from src.intelligence.market_signals import market_probability_report, no_vig_probs
from src.intelligence.motivation_signals import motivation_signal
from src.intelligence.news_signals import signal_or_unknown
from src.intelligence.schedule_signals import schedule_signal, travel_signal
from src.intelligence.weather_signals import weather_signal
from src.models.dixon_coles import apply_dixon_coles_adjustment
from src.models.score_matrix import build_score_matrix, handicap_probabilities, outcome_probabilities, top_scores, total_goals_distribution


def build_match_context(match, historical_data=None, external_signals: dict | None = None) -> dict:
    external = external_signals or {}
    had_odds = _value(match, "had_odds", None) or _raw_pool(match, "HAD")
    hhad_odds = _value(match, "hhad_odds", None) or _raw_pool(match, "HHAD")
    match_id = str(_value(match, "match_id", ""))
    market_had = no_vig_probs(had_odds)
    market_hhad = no_vig_probs(hhad_odds)
    market_had_report = market_probability_report(had_odds)
    market_hhad_report = market_probability_report(hhad_odds)
    home_xg, away_xg = _xg_baseline(match, market_had)
    poisson_matrix = build_score_matrix(home_xg, away_xg)
    dc_matrix = apply_dixon_coles_adjustment(poisson_matrix)
    poisson_probs = outcome_probabilities(poisson_matrix)
    dc_probs = outcome_probabilities(dc_matrix)
    handicap = _safe_float((hhad_odds or {}).get("handicap"))
    signals = {
        "news": signal_or_unknown(external, "news"),
        "injuries": injury_signal(external),
        "lineup": lineup_signal(external),
        "weather": weather_signal(external),
        "motivation": motivation_signal(external),
        "schedule": schedule_signal(match),
        "travel": travel_signal(match),
    }
    confidence = confidence_score(signals)
    return {
        "match": _match_info(match),
        "sporttery_odds": {"had": had_odds or {}, "hhad": hhad_odds or {}},
        "market_no_vig": {"had": market_had, "hhad": market_hhad},
        "market_probability_report": {"had": market_had_report, "hhad": market_hhad_report},
        "elo_strength": _elo_strength(match),
        "poisson_xg": {"home_xg": round(home_xg, 4), "away_xg": round(away_xg, 4), "outcome_probs": poisson_probs},
        "dixon_coles": {"outcome_probs": dc_probs, "rho": 0.08},
        "hhad_probs": handicap_probabilities(dc_matrix, handicap) if hhad_odds else {},
        "total_goals": total_goals_distribution(dc_matrix),
        "top_scores": top_scores(dc_matrix, 5),
        "signals": signals,
        "confidence_score": confidence["confidence_score"],
        "missing_signals": confidence["missing_signals"],
    }


def _match_info(match) -> dict:
    return {
        "match_id": _value(match, "match_id", ""),
        "match_no": _value(match, "match_no", ""),
        "date": _value(match, "date", ""),
        "league": _value(match, "league", ""),
        "kickoff_at": _value(match, "kickoff_at", ""),
        "home_team": _value(match, "home_team", ""),
        "away_team": _value(match, "away_team", ""),
        "source": _value(match, "source", ""),
    }


def _xg_baseline(match, market_had: dict[str, float]) -> tuple[float, float]:
    metadata = _value(match, "metadata", {}) or {}
    home_rating = float(metadata.get("home_rating", 56) or 56)
    away_rating = float(metadata.get("away_rating", 56) or 56)
    rating_gap = max(-18.0, min(18.0, home_rating - away_rating))
    market_home = float(market_had.get("home", 0.36) or 0.36)
    market_away = float(market_had.get("away", 0.33) or 0.33)
    home_xg = 1.18 + rating_gap / 34.0 + (market_home - market_away) * 0.9
    away_xg = 1.05 - rating_gap / 40.0 + (market_away - market_home) * 0.7
    return max(0.25, min(3.2, home_xg)), max(0.2, min(3.0, away_xg))


def _elo_strength(match) -> dict:
    metadata = _value(match, "metadata", {}) or {}
    home = float(metadata.get("home_rating", 56) or 56)
    away = float(metadata.get("away_rating", 56) or 56)
    diff = home - away
    home_prob = 1.0 / (1.0 + 10 ** (-diff / 16.0))
    draw = 0.25
    remaining = max(0.0, 1.0 - draw)
    return {"home": round(home_prob * remaining, 6), "draw": draw, "away": round((1.0 - home_prob) * remaining, 6), "home_rating": home, "away_rating": away}


def _raw_pool(match, pool_code: str) -> dict:
    raw = _value(match, "raw", {}) or {}
    for item in raw.get("oddsList", []) or []:
        if isinstance(item, dict) and str(item.get("poolCode")) == pool_code:
            payload = {"win": _safe_float(item.get("h")), "draw": _safe_float(item.get("d")), "lose": _safe_float(item.get("a"))}
            if pool_code == "HHAD":
                payload["handicap"] = _safe_float(item.get("goalLine"))
            return payload
    return {}


def _value(obj, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

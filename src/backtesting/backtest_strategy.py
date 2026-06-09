from __future__ import annotations


DEFAULT_STRATEGY_CONFIG = {
    "min_ev": 0.04,
    "min_edge": 0.025,
    "min_odds": 1.35,
    "max_odds": 5.50,
}


def select_value_bet(
    match,
    model_probs: dict,
    market_probs: dict,
    odds: dict,
    config: dict | None = None,
) -> dict | None:
    settings = dict(DEFAULT_STRATEGY_CONFIG)
    if config:
        settings.update(config)
    candidates = []
    for selection in ("win", "draw", "lose"):
        odd = odds.get(selection)
        if not isinstance(odd, (int, float)):
            continue
        model_prob = float(model_probs.get(selection, 0.0))
        market_prob = float(market_probs.get(selection, 0.0))
        edge = model_prob - market_prob
        ev = model_prob * float(odd) - 1.0
        if (
            ev >= settings["min_ev"]
            and edge >= settings["min_edge"]
            and settings["min_odds"] <= float(odd) <= settings["max_odds"]
        ):
            candidates.append((ev, edge, selection, odd, model_prob, market_prob))
    if not candidates:
        return None
    ev, edge, selection, odd, model_prob, market_prob = max(candidates, key=lambda item: (item[0], item[1]))
    return {
        "date": match.date,
        "match_id": f"{match.date}:{match.home_team}:{match.away_team}",
        "league": match.league,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "selection": selection,
        "odds": round(float(odd), 6),
        "model_prob": round(model_prob, 6),
        "market_prob": round(market_prob, 6),
        "edge": round(edge, 6),
        "ev": round(ev, 6),
        "stake": 1.0,
    }

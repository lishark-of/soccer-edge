from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.backtesting.backtest_strategy import select_value_bet
from src.backtesting.calibration import reliability_summary
from src.backtesting.metrics import summarize_backtest
from src.domain.match import Match
from src.domain.odds import MarketOdds
from src.modeling.team_strength import build_team_strengths
from src.probability.elo_model import build_elo_ratings, elo_to_1x2_probs
from src.probability.ensemble import combine_probabilities
from src.probability.implied_probability import calculate_implied_probabilities
from src.probability.no_vig import remove_vig
from src.probability.poisson_model import derive_1x2_probs, scoreline_distribution


MODEL_VERSION = "phase2c_backtest_market_poisson_elo_v0"


@dataclass(slots=True)
class ChronologicalSplit:
    train: list[dict[str, Any]]
    test: list[dict[str, Any]]


def run_backtest(
    historical_matches: list,
    start_date: str | None = None,
    end_date: str | None = None,
    min_train_matches: int = 20,
    strategy_config: dict | None = None,
) -> dict:
    ordered = sorted(historical_matches, key=lambda match: match.date)
    predictions: list[dict] = []
    bets: list[dict] = []
    skipped = 0
    warnings: list[str] = []
    for match in ordered:
        if start_date and match.date < start_date:
            continue
        if end_date and match.date > end_date:
            continue
        prior_matches = [item for item in ordered if item.date < match.date]
        if len(prior_matches) < min_train_matches:
            skipped += 1
            continue
        odds = _extract_had_odds(match)
        if not odds:
            skipped += 1
            warnings.append(f"skip {match.date} {match.home_team} vs {match.away_team}: missing usable odds")
            continue
        market_probs = _market_probs(odds)
        model_probs = _model_probs(match, prior_matches, market_probs)
        actual = _actual_result(match)
        predictions.append(
            {
                "date": match.date,
                "match_id": f"{match.date}:{match.home_team}:{match.away_team}",
                "actual": actual,
                "probabilities": model_probs,
                "market_probabilities": market_probs,
            }
        )
        bet = select_value_bet(match, model_probs, market_probs, odds, strategy_config)
        if bet:
            hit = bet["selection"] == actual
            profit = bet["stake"] * (bet["odds"] - 1.0) if hit else -bet["stake"]
            bet["actual"] = actual
            bet["hit"] = hit
            bet["profit"] = round(profit, 6)
            bets.append(bet)
    metrics = summarize_backtest(bets, predictions)
    calibration = reliability_summary(predictions)
    return {
        "model_version": MODEL_VERSION,
        "matches_total": len(historical_matches),
        "matches_evaluated": len(predictions),
        "matches_skipped": skipped,
        "bets_total": len(bets),
        "metrics": metrics,
        "calibration": calibration,
        "bets": bets,
        "predictions": predictions,
        "warnings": warnings + metrics.get("warnings", []),
    }


def chronological_split(rows: list[dict[str, Any]], train_ratio: float = 0.8) -> ChronologicalSplit:
    ordered = sorted(rows, key=lambda item: item["date"])
    cutoff = max(1, int(len(ordered) * train_ratio)) if ordered else 0
    return ChronologicalSplit(train=ordered[:cutoff], test=ordered[cutoff:])


def rolling_feature_shift(values: list[float | None]) -> list[float | None]:
    shifted: list[float | None] = [None]
    shifted.extend(values[:-1])
    return shifted


def features_use_only_past_matches(matches: list[dict[str, Any]]) -> bool:
    ordered = sorted(matches, key=lambda item: item["date"])
    return ordered == matches


def _extract_had_odds(match) -> dict[str, float] | None:
    odds = getattr(match, "odds_had", None)
    if not odds:
        return None
    mapped = {
        "win": odds.get("win"),
        "draw": odds.get("draw"),
        "lose": odds.get("lose"),
    }
    if not all(isinstance(value, (int, float)) and value > 1 for value in mapped.values()):
        return None
    return {key: float(value) for key, value in mapped.items()}


def _market_probs(odds: dict[str, float]) -> dict[str, float]:
    market = MarketOdds(play_type="had", outcomes={"home": odds["win"], "draw": odds["draw"], "away": odds["lose"]})
    fair = remove_vig(calculate_implied_probabilities(market.outcomes))
    return {"win": fair["home"], "draw": fair["draw"], "lose": fair["away"]}


def _model_probs(match, prior_matches: list, market_probs: dict[str, float]) -> dict[str, float]:
    team_strengths = build_team_strengths(prior_matches, before_date=match.date)
    lightweight_match = Match(
        match_id=f"{match.date}:{match.home_team}:{match.away_team}",
        match_no="historical",
        date=match.date,
        league=match.league,
        kickoff_at=match.date,
        home_team=match.home_team,
        away_team=match.away_team,
    )
    from src.modeling.team_strength import estimate_xg_for_match

    home_xg, away_xg = estimate_xg_for_match(lightweight_match, team_strengths)
    poisson_probs = derive_1x2_probs(scoreline_distribution(home_xg, away_xg))
    ratings = build_elo_ratings(prior_matches, before_date=match.date)
    elo_probs = elo_to_1x2_probs(ratings.get(match.home_team, 1500.0), ratings.get(match.away_team, 1500.0))
    return combine_probabilities(market_probs, poisson_probs=poisson_probs, elo_probs=elo_probs)["probabilities"]


def _actual_result(match) -> str:
    return {"H": "win", "D": "draw", "A": "lose"}[match.result_1x2]

from __future__ import annotations

from itertools import combinations

from src.domain.analysis_result import DailyAnalysisReport, MatchAnalysis
from src.domain.match import Match
from src.domain.odds import MatchOdds, OddsHistory, MarketOdds
from src.domain.parlay import ParlayCandidate
from src.providers.base import BaseProvider
from src.probability.ensemble import build_model_probabilities
from src.probability.implied_probability import calculate_implied_probabilities
from src.probability.no_vig import remove_vig
from src.rules.parlay_builder import build_parlay_combinations
from src.rules.payout_estimator import estimate_payout
from src.strategy.bankroll import exposure_warning
from src.strategy.risk_ranker import score_parlay_risk, score_selection_risk
from src.strategy.value_detector import analyze_market_outcomes


DISCLAIMERS = [
    "仅供数据研究与娱乐参考",
    "概率模型不保证结果",
    "串关会显著放大风险",
    "请勿投入无法承受损失的资金",
]


def build_daily_analysis(provider: BaseProvider, target_date: str) -> DailyAnalysisReport:
    matches = provider.get_matches(target_date)
    report = DailyAnalysisReport(
        date=target_date,
        matches_analyzed=len(matches),
        disclaimers=list(DISCLAIMERS),
    )
    parlay_pool: list[MatchAnalysis] = []

    for match in matches:
        try:
            odds = provider.get_match_odds(match.match_id)
        except Exception as exc:
            report.excluded_matches.append(
                {
                    "match_id": match.match_id,
                    "match_no": match.match_no,
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "reason": f"赔率加载失败：{exc}",
                }
            )
            continue
        filtered_odds, market_reasons = _filter_usable_markets(odds)
        if not filtered_odds.markets:
            report.excluded_matches.append(
                {
                    "match_id": match.match_id,
                    "match_no": match.match_no,
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "reason": "；".join(market_reasons) or "未提供可用赔率。",
                }
            )
            continue
        try:
            history = provider.get_odds_history(match.match_id)
        except Exception:
            history = OddsHistory(match_id=match.match_id, history={})
        match_analyses = _analyze_match(match, filtered_odds, history)
        positive = [item for item in match_analyses if item.selection.ev > 0]
        if positive:
            best = max(positive, key=lambda item: (item.selection.ev, item.selection.edge))
            if best.recommended_use == "单关候选":
                report.single_candidates.append(best)
            parlay_best = _choose_parlay_friendly_candidate(positive)
            if parlay_best is not None:
                parlay_pool.append(parlay_best)
        else:
            report.excluded_matches.append(
                {
                    "match_id": match.match_id,
                    "match_no": match.match_no,
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "reason": "模型概率未形成正期望方向。",
                }
            )

    parlay_eligible = [item.selection for item in parlay_pool if item.selection.ev > 0]
    report.parlay_2x1_candidates = _build_parlay_candidates(parlay_eligible, "2x1")
    report.parlay_3x1_candidates = _build_parlay_candidates(parlay_eligible, "3x1")
    if not report.single_candidates:
        report.warnings.append("当前日期没有满足单关阈值的候选。")
    if not report.parlay_2x1_candidates:
        report.warnings.append("当前日期没有满足 2串1 阈值的候选组合。")
    return report


def _analyze_match(match: Match, odds: MatchOdds, history: OddsHistory) -> list[MatchAnalysis]:
    analyses: list[MatchAnalysis] = []
    for market_key, market in odds.markets.items():
        implied = calculate_implied_probabilities(market.outcomes)
        fair = remove_vig(implied)
        model, confidence, model_reasons = build_model_probabilities(match, market, fair, history)
        reference_odds = min(value for value in market.outcomes.values() if isinstance(value, (int, float)))
        risk_score, risk_level, risk_reasons = score_selection_risk(match, reference_odds, confidence, history)
        analyses.extend(
            analyze_market_outcomes(
                match=match,
                play_type=market_key,
                odds=market.outcomes,
                fair_probabilities=fair,
                model_probabilities=model,
                confidence=confidence,
                risk_level=risk_level,
                risk_score=risk_score,
                risk_reasons=risk_reasons,
                model_reasons=model_reasons,
            )
        )
    return analyses


def _filter_usable_markets(odds: MatchOdds) -> tuple[MatchOdds, list[str]]:
    usable: dict[str, MarketOdds] = {}
    reasons: list[str] = []
    for market_key, market in odds.markets.items():
        if _is_valid_market(market):
            usable[market_key] = market
        elif market_key == "had":
            reasons.append("胜平负赔率缺失或无效。")
        elif market_key == "hhad":
            reasons.append("让球胜平负赔率缺失或无效。")
        else:
            reasons.append(f"{market_key} 赔率缺失或无效。")
    if not usable and not reasons:
        reasons.append("未提供可用赔率。")
    return MatchOdds(match_id=odds.match_id, markets=usable), reasons


def _is_valid_market(market: MarketOdds) -> bool:
    values = [market.outcomes.get("home"), market.outcomes.get("draw"), market.outcomes.get("away")]
    if not all(isinstance(value, (int, float)) and value > 1 for value in values):
        return False
    if market.play_type == "hhad" and market.handicap is None:
        return False
    return True


def _build_parlay_candidates(selections: list, pass_type: str) -> list[ParlayCandidate]:
    leg_count = 2 if pass_type == "2x1" else 3
    qualified = [
        selection
        for selection in selections
        if selection.ev >= (0.04 if pass_type == "2x1" else 0.000001)
    ]
    if pass_type == "3x1":
        qualified = [
            selection
            for selection in qualified
            if selection.risk_level in {"low", "medium", "high"}
        ]
    candidates: list[ParlayCandidate] = []
    for combo in combinations(qualified, leg_count):
        if len({selection.match_id for selection in combo}) != leg_count:
            continue
        if pass_type == "3x1":
            stable_legs = [selection for selection in combo if selection.risk_level in {"low", "medium"}]
            if len(stable_legs) < 2:
                continue
        correlation_penalty = _correlation_penalty(list(combo))
        market_probability = 1.0
        hit_probability = 1.0
        combined_odds = 1.0
        for selection in combo:
            market_probability *= selection.fair_prob
            hit_probability *= selection.model_prob
            combined_odds *= selection.odds
        market_probability *= 1.0 - correlation_penalty
        hit_probability *= 1.0 - correlation_penalty
        ev = round(hit_probability * combined_odds - 1.0, 6)
        if ev <= 0:
            continue
        if pass_type == "2x1" and not 2.2 <= combined_odds <= 4.5:
            continue
        if pass_type == "3x1" and not 4.0 <= combined_odds <= 8.0:
            continue
        legs = build_parlay_combinations(list(combo), pass_type)[0]
        risk_score, risk_level, warnings = score_parlay_risk(list(combo), correlation_penalty)
        payout = estimate_payout(legs, stake_per_ticket=2)
        warnings.extend(exposure_warning(payout.total_stake))
        candidates.append(
            ParlayCandidate(
                pass_type=pass_type,
                legs=legs,
                combined_odds=round(combined_odds, 4),
                hit_probability=round(hit_probability, 6),
                market_probability=round(market_probability, 6),
                ev=ev,
                risk_level=risk_level,
                risk_score=risk_score,
                payout=payout,
                warnings=warnings,
            )
        )
    candidates.sort(key=lambda item: (item.ev, item.hit_probability), reverse=True)
    return candidates[:5]


def _choose_parlay_friendly_candidate(analyses: list[MatchAnalysis]) -> MatchAnalysis | None:
    filtered = [
        item
        for item in analyses
        if item.selection.odds >= 1.45
        and item.selection.odds <= 2.60
        and item.selection.ev >= 0.04
        and item.selection.risk_level in {"low", "medium"}
    ]
    if not filtered:
        return None
    return max(filtered, key=lambda item: (item.selection.ev, item.selection.model_prob))


def _correlation_penalty(selections: list) -> float:
    groups = [selection.correlation_group for selection in selections if selection.correlation_group]
    if not groups:
        return 0.0
    duplicates = len(groups) - len(set(groups))
    return min(0.18, duplicates * 0.08)

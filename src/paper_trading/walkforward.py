from __future__ import annotations

from collections import defaultdict

from src.backtesting.backtest_engine import MODEL_VERSION, _actual_result, _extract_had_odds, _market_probs, _model_probs
from src.paper_trading.bankroll import apply_settlement, create_bankroll
from src.paper_trading.diagnostics import diagnose_operation
from src.paper_trading.report import DISCLAIMER, build_paper_operation_report
from src.paper_trading.selection_policy import allocate_paper_stakes, build_parlay_candidates, select_daily_observations
from src.paper_trading.settlement import settle_observations

OUTCOME_LABELS = {"win": "主胜", "draw": "平", "lose": "客胜"}
ODDS_KEYS = {"win": "win", "draw": "draw", "lose": "lose"}


def run_paper_operation_walkforward(
    historical_matches: list,
    initial_bankroll: float = 10000.0,
    start_date: str | None = None,
    end_date: str | None = None,
    strategy_config: dict | None = None,
) -> dict:
    ordered = sorted(historical_matches, key=lambda match: (match.date, match.league, match.home_team, match.away_team))
    bankroll = create_bankroll(initial_bankroll)
    min_train_matches = int((strategy_config or {}).get("min_train_matches", 20))
    dates = sorted({match.date for match in ordered if (not start_date or match.date >= start_date) and (not end_date or match.date <= end_date)})
    daily_ledger = []
    walk_log = []
    warnings: list[str] = []
    skipped_days = 0
    for date in dates:
        day_matches = [match for match in ordered if match.date == date]
        prior_matches = [match for match in ordered if match.date < date]
        if len(prior_matches) < min_train_matches:
            skipped_days += 1
            daily_ledger.append(_day_row(date, bankroll.current_bankroll, bankroll.current_bankroll, 0.0, 0, "样本不足，跳过"))
            continue
        if bankroll.current_bankroll <= 0:
            warnings.append("纸面本金已归零，后续日期不再生成模拟观察。")
            break
        analysis = _daily_analysis_from_matches(day_matches, prior_matches, strategy_config)
        observations = select_daily_observations(analysis, strategy_config)
        allocated = allocate_paper_stakes(observations, bankroll.current_bankroll, strategy_config)
        if not allocated:
            daily_ledger.append(_day_row(date, bankroll.current_bankroll, bankroll.current_bankroll, 0.0, 0, "无符合条件的候选信号"))
            continue
        actual_results = { _match_id(match): _actual_result(match) for match in day_matches }
        settled = settle_observations(allocated, actual_results)
        starting = bankroll.current_bankroll
        daily_profit = 0.0
        for item in settled:
            profit = float(item.get("profit") or 0.0)
            stake = float(item.get("paper_stake") or 0.0)
            bankroll = apply_settlement(bankroll, stake, profit)
            daily_profit += profit
            walk_log.append(_walk_row(date, item, bankroll.current_bankroll))
        daily_ledger.append(_day_row(date, starting, bankroll.current_bankroll, daily_profit, len(settled), "已结算"))
    combo_summary = _combo_summary(walk_log)
    settled_count = sum(1 for item in walk_log if item.get("settlement_status") == "settled")
    hit_count = sum(1 for item in walk_log if item.get("hit") is True)
    total_staked = bankroll.total_staked
    report = {
        "simulation_version": "phase2l_paper_operation_v0",
        "model_version": MODEL_VERSION,
        "initial_bankroll": round(float(initial_bankroll), 2),
        "final_bankroll": bankroll.current_bankroll,
        "total_profit": round(bankroll.current_bankroll - bankroll.initial_bankroll, 2),
        "roi": round((bankroll.total_profit / total_staked), 6) if total_staked > 0 else 0.0,
        "hit_rate": round(hit_count / settled_count, 6) if settled_count else 0.0,
        "observation_count": len(walk_log),
        "settled_count": settled_count,
        "void_count": sum(1 for item in walk_log if item.get("settlement_status") == "void"),
        "unsettled_count": sum(1 for item in walk_log if item.get("settlement_status") == "unsettled"),
        "max_drawdown": bankroll.max_drawdown,
        "total_staked": bankroll.total_staked,
        "daily_ledger": daily_ledger,
        "walk_log": walk_log,
        "combo_summary": combo_summary,
        "warnings": warnings,
        "skipped_days": skipped_days,
        "fixture_warning": True,
        "disclaimer": DISCLAIMER,
    }
    report["diagnostics"] = diagnose_operation(report)
    return build_paper_operation_report(report)


def _daily_analysis_from_matches(day_matches: list, prior_matches: list, strategy_config: dict | None) -> dict:
    singles = []
    for match in day_matches:
        odds = _extract_had_odds(match)
        if not odds:
            continue
        market_probs = _market_probs(odds)
        model_probs = _model_probs(match, prior_matches, market_probs)
        for key in ("win", "draw", "lose"):
            odds_value = float(odds[ODDS_KEYS[key]])
            fair = float(market_probs[key])
            model = float(model_probs[key])
            edge = model - fair
            ev = model * odds_value - 1.0
            if ev <= 0:
                continue
            singles.append(
                {
                    "match_id": _match_id(match),
                    "date": match.date,
                    "league": match.league,
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "play_type": "had",
                    "outcome_key": key,
                    "outcome_label": OUTCOME_LABELS[key],
                    "odds": round(odds_value, 4),
                    "fair_prob": round(fair, 6),
                    "model_prob": round(model, 6),
                    "edge": round(edge, 6),
                    "ev": round(ev, 6),
                    "risk_level": _risk_level(odds_value, edge),
                    "risk_label": _risk_label(_risk_level(odds_value, edge)),
                }
            )
    singles = sorted(singles, key=lambda item: (item.get("ev", 0), item.get("edge", 0)), reverse=True)
    parlay = build_parlay_candidates(singles, max_size=3 if (strategy_config or {}).get("max_parlay_3x1_per_day", 0) else 2)
    return {"single_candidates": singles, **parlay, "warnings": []}


def _risk_level(odds: float, edge: float) -> str:
    if odds >= 4.2 or edge < 0.03:
        return "high"
    if odds >= 3.2 or edge < 0.06:
        return "medium"
    return "low"


def _risk_label(level: str) -> str:
    return {"low": "低", "medium": "中", "high": "高", "very_high": "很高"}.get(level, "未分级")


def _match_id(match) -> str:
    return f"{match.date}:{match.home_team}:{match.away_team}"


def _day_row(date: str, starting: float, ending: float, profit: float, count: int, status: str) -> dict:
    return {
        "date": date,
        "starting_bankroll": round(starting, 2),
        "ending_bankroll": round(ending, 2),
        "daily_profit": round(profit, 2),
        "observation_count": count,
        "status": status,
    }


def _walk_row(date: str, item: dict, bankroll_after: float) -> dict:
    match = f"{item.get('home_team', '')} vs {item.get('away_team', '')}".strip()
    return {
        **item,
        "date": date,
        "match": match,
        "direction": item.get("outcome_label") or item.get("pass_type", ""),
        "bankroll_after": round(bankroll_after, 2),
    }


def _combo_summary(walk_log: list[dict]) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in walk_log:
        grouped[str(item.get("observation_type", "single"))].append(item)
    summary = {}
    for kind in ("single", "parlay_2x1", "parlay_3x1"):
        rows = grouped.get(kind, [])
        settled = [item for item in rows if item.get("settlement_status") == "settled"]
        hits = [item for item in settled if item.get("hit") is True]
        stake = sum(float(item.get("paper_stake") or 0.0) for item in settled)
        profit = sum(float(item.get("profit") or 0.0) for item in settled)
        summary[kind] = {
            "count": len(rows),
            "settled": len(settled),
            "hits": len(hits),
            "hit_rate": round(len(hits) / len(settled), 6) if settled else 0.0,
            "paper_staked": round(stake, 2),
            "profit": round(profit, 2),
            "roi": round(profit / stake, 6) if stake > 0 else 0.0,
        }
    return summary

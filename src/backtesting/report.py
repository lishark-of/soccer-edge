from __future__ import annotations


DISCLAIMER = "Backtest results are research diagnostics and do not guarantee future outcomes."


def build_backtest_report(backtest_result: dict) -> dict:
    metrics = backtest_result.get("metrics", {})
    return {
        **backtest_result,
        "summary": {
            "bets_total": backtest_result.get("bets_total", 0),
            "roi": metrics.get("roi", 0.0),
            "hit_rate": metrics.get("hit_rate", 0.0),
            "max_drawdown": metrics.get("max_drawdown", 0.0),
        },
        "warnings": list(dict.fromkeys(backtest_result.get("warnings", []))),
        "disclaimer": DISCLAIMER,
    }

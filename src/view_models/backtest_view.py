from __future__ import annotations

from src.explain.local_explainer import explain_backtest_metrics, explain_risk_level
from src.explain.safety import DISCLAIMER_TEXT


def build_backtest_view(report: dict) -> dict:
    metrics = report.get("metrics", {}) or {}
    bets = list(report.get("bets", []) or [])
    calibration = report.get("calibration", {}) or {}
    return {
        "title": "概率回测诊断",
        "summary_cards": [
            {"label": "总比赛数", "value": report.get("matches_total", 0), "help": "历史数据中的总比赛数量。"},
            {"label": "有效评估", "value": report.get("matches_evaluated", 0), "help": "满足训练样本和赔率条件的比赛数。"},
            {"label": "候选触发", "value": report.get("bets_total", 0), "help": "策略规则在历史样本中触发的观察项数量。"},
            {"label": "命中率", "value": _pct(metrics.get("hit_rate")), "help": "历史样本中触发项命中的比例。"},
            {"label": "ROI", "value": _signed_pct(metrics.get("roi")), "help": "历史模拟单位投入收益率，不代表未来。"},
            {"label": "最大回撤", "value": _signed_pct(metrics.get("max_drawdown")), "help": "资金曲线从高点到低点的最大跌幅。"},
            {"label": "Brier Score", "value": _num(metrics.get("brier_score")), "help": "概率预测接近真实结果的程度，越低越好。"},
            {"label": "Log Loss", "value": _num(metrics.get("log_loss")), "help": "对过度自信错误预测惩罚更重，越低越好。"},
        ],
        "metric_explanations": explain_backtest_metrics(metrics),
        "calibration_table": _calibration_rows(calibration),
        "bets_table": [_bet_row(item) for item in bets[:50]],
        "risk_notes": [
            explain_risk_level("high", {"pass_type": "diagnostic"}),
            "回测使用历史样本诊断概率与策略规则，未来数据分布可能不同。",
        ],
        "warnings": list(report.get("warnings", []) or []),
        "disclaimer": DISCLAIMER_TEXT,
        "backtest_credibility": report.get("backtest_credibility", {}),
    }


def _bet_row(item: dict) -> dict:
    return {
        "date": item.get("date", ""),
        "league": item.get("league", ""),
        "match": f"{item.get('home_team', '')} vs {item.get('away_team', '')}".strip(),
        "direction": item.get("selection", ""),
        "odds": _num(item.get("odds")),
        "model_probability": _pct(item.get("model_prob")),
        "market_probability": _pct(item.get("market_prob")),
        "ev": _signed_pct(item.get("ev")),
        "hit": "是" if item.get("hit") else "否",
        "profit": _num(item.get("profit")),
    }


def _calibration_rows(calibration: dict) -> list[dict]:
    rows = []
    bins_by_class = calibration.get("by_class", calibration)
    if not isinstance(bins_by_class, dict):
        return rows
    for label, bins in bins_by_class.items():
        if not isinstance(bins, list):
            continue
        for item in bins:
            rows.append(
                {
                    "outcome": label,
                    "range": f"{_pct(item.get('bin_start'))} - {_pct(item.get('bin_end'))}",
                    "count": item.get("count", 0),
                    "avg_predicted_prob": _pct(item.get("avg_predicted_prob")),
                    "observed_frequency": _pct(item.get("observed_frequency")),
                    "gap": _signed_pct(item.get("gap")),
                }
            )
    return rows


def _pct(value):
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _signed_pct(value):
    try:
        return f"{float(value) * 100:+.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _num(value):
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "N/A"

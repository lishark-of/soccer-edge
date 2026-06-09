from __future__ import annotations

from src.paper_trading.report import DISCLAIMER


def build_operation_view(report: dict) -> dict:
    combo = report.get("combo_summary", {}) or {}
    diagnostics = report.get("diagnostics", {}) or {}
    return {
        "title": "模拟走盘",
        "summary_cards": [
            {"label": "初始模拟本金", "value": _rmb(report.get("initial_bankroll")), "help": "默认从 10,000 元纸面本金开始。"},
            {"label": "最终模拟本金", "value": _rmb(report.get("final_bankroll")), "help": "历史复盘结束后的纸面本金。"},
            {"label": "总盈亏", "value": _signed_rmb(report.get("total_profit")), "help": "纸面模拟盈亏，不代表未来表现。"},
            {"label": "ROI", "value": _pct(report.get("roi")), "help": "纸面盈亏 / 纸面总投入。"},
            {"label": "命中率", "value": _pct(report.get("hit_rate")), "help": "已结算观察项中命中的比例。"},
            {"label": "最大回撤", "value": _signed_pct(-float(report.get("max_drawdown") or 0.0)), "help": "纸面本金曲线从高点到低点的最大跌幅。"},
        ],
        "equity_curve": report.get("equity_curve", []) or [],
        "walk_log_table": report.get("walk_log_table", []) or [],
        "combo_summary": [_combo_row(name, data) for name, data in combo.items()],
        "diagnostics": list(diagnostics.get("issues", []) or []),
        "strengths": list(diagnostics.get("strengths", []) or []),
        "warnings": list(report.get("warnings", []) or []),
        "disclaimer": report.get("disclaimer") or DISCLAIMER,
    }


def _combo_row(name: str, data: dict) -> dict:
    return {
        "type": {"single": "单关观察", "parlay_2x1": "2串1 组合观察", "parlay_3x1": "3串1 组合观察"}.get(name, name),
        "count": data.get("count", 0),
        "settled": data.get("settled", 0),
        "hits": data.get("hits", 0),
        "hit_rate": _pct(data.get("hit_rate")),
        "paper_staked": _rmb(data.get("paper_staked")),
        "profit": _signed_rmb(data.get("profit")),
        "roi": _pct(data.get("roi")),
    }


def _rmb(value) -> str:
    try:
        return f"¥{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _signed_rmb(value) -> str:
    try:
        number = float(value)
        sign = "+" if number >= 0 else "-"
        return f"{sign}¥{abs(number):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _signed_pct(value) -> str:
    try:
        return f"{float(value) * 100:+.1f}%"
    except (TypeError, ValueError):
        return "N/A"

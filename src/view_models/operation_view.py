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
            {"label": "纸面盈亏", "value": _signed_rmb(report.get("total_profit")), "help": "最终模拟本金减初始模拟本金。"},
            {"label": "本金收益率", "value": _signed_pct(report.get("bankroll_return")), "help": "纸面盈亏 / 初始模拟本金。"},
            {"label": "总模拟投入", "value": _rmb(report.get("total_staked")), "help": "历史复盘中所有纸面观察金额合计。"},
            {"label": "模拟投入 ROI", "value": _pct(report.get("stake_roi", report.get("roi"))), "help": "纸面盈亏 / 总模拟投入。"},
            {"label": "命中率", "value": _pct(report.get("hit_rate")), "help": "已结算观察项中命中的比例。"},
            {"label": "最大回撤", "value": _signed_pct(-float(report.get("max_drawdown") or 0.0)), "help": "纸面本金曲线从高点到低点的最大跌幅。"},
        ],
        "equity_curve": report.get("equity_curve", []) or [],
        "walk_log_table": report.get("walk_log_table", []) or [],
        "combo_summary": [_combo_row(name, data) for name, data in combo.items()],
        "profit_explanation": _profit_explanation(report, combo),
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


def _profit_explanation(report: dict, combo: dict) -> list[str]:
    profit = _float(report.get("total_profit"))
    initial = _float(report.get("initial_bankroll"))
    total_staked = _float(report.get("total_staked"))
    bankroll_return = profit / initial if initial > 0 else 0.0
    stake_roi = profit / total_staked if total_staked > 0 else 0.0
    hit_rate = _float(report.get("hit_rate"))
    max_drawdown = _float(report.get("max_drawdown"))
    if total_staked <= 0:
        return [
            "本次没有形成已结算的纸面观察项，因此无法解释盈亏来源。",
            "请检查历史数据、赔率覆盖、EV/Edge 阈值和最小训练样本数量。",
            "模拟走盘只用于复盘诊断，不代表未来表现。",
        ]
    direction = "盈利" if profit > 0 else "亏损" if profit < 0 else "基本持平"
    notes = [
        f"本次纸面结果为{direction}：总盈亏 {_signed_rmb(profit)}，本金收益率 {_signed_pct(bankroll_return)}，模拟投入 ROI {_signed_pct(stake_roi)}。",
        f"口径说明：总模拟投入为 {_rmb(total_staked)}，不是全仓使用本金；因此本金收益率和模拟投入 ROI 会明显不同。",
        f"命中率为 {_pct(hit_rate)}，它只说明已结算观察项的命中比例，不能单独代表收益质量。",
        f"最大回撤为 {_signed_pct(-max_drawdown)}，用于观察纸面本金曲线曾经承受的最大不利波动。",
    ]
    contributors = _combo_contributors(combo)
    if contributors:
        notes.append("玩法贡献：" + "；".join(contributors))
    else:
        notes.append("玩法贡献暂不明显，可能是样本量不足或观察项太少。")
    notes.append("模拟走盘不代表未来表现，也不构成投注、下单、支付或代购建议。")
    return notes


def _combo_contributors(combo: dict) -> list[str]:
    rows = []
    labels = {"single": "单关观察", "parlay_2x1": "2串1 组合观察", "parlay_3x1": "3串1 组合观察"}
    for key, label in labels.items():
        data = combo.get(key, {}) or {}
        count = int(data.get("settled") or data.get("count") or 0)
        if count <= 0:
            continue
        rows.append(f"{label}结算 {count} 项，盈亏 {_signed_rmb(data.get('profit'))}，ROI {_pct(data.get('roi'))}")
    return rows


def _float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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

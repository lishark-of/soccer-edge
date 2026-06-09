from __future__ import annotations


def build_optimizer_view(result: dict) -> dict:
    portfolio = result.get("recommended_observation_portfolio", {}) or {}
    risk = result.get("risk_summary", {}) or {}
    return {
        "title": "赛前组合优化",
        "summary_cards": [
            {"label": "当前本金", "value": _rmb(result.get("bankroll")), "help": "用于计算纸面观察金额。"},
            {"label": "每日暴露上限", "value": _rmb(result.get("daily_exposure_cap")), "help": "默认不超过本金 3%。"},
            {"label": "推荐纸面投入", "value": _rmb(result.get("recommended_paper_exposure")), "help": "本次组合优化建议的总纸面投入。"},
            {"label": "单关观察", "value": len(portfolio.get("singles", []) or []), "help": "满足 EV、Edge、风险约束的单关候选。"},
            {"label": "2串1观察", "value": len(portfolio.get("parlay_2x1", []) or []), "help": "考虑相关性折扣后的组合观察。"},
            {"label": "3串1观察", "value": len(portfolio.get("parlay_3x1", []) or []), "help": "默认关闭，需显式启用。"},
        ],
        "singles_table": [_row(item) for item in portfolio.get("singles", []) or []],
        "parlay_2x1_table": [_row(item) for item in portfolio.get("parlay_2x1", []) or []],
        "parlay_3x1_table": [_row(item) for item in portfolio.get("parlay_3x1", []) or []],
        "rejected_table": list(result.get("rejected_candidates", []) or []),
        "risk_summary": risk,
        "explanations": list(result.get("explanations", []) or []),
        "warnings": list(result.get("warnings", []) or []),
        "disclaimer": result.get("disclaimer", "仅供概率研究，不构成投注建议。"),
    }


def _row(item: dict) -> dict:
    is_combo = bool(item.get("legs"))
    return {
        "type": {"single": "单关", "parlay_2x1": "2串1", "parlay_3x1": "3串1"}.get(item.get("candidate_type"), item.get("candidate_type")),
        "match": _label(item),
        "odds": _num(item.get("odds") or item.get("combo_odds")),
        "model_prob": _pct(item.get("model_prob") or item.get("combo_prob")),
        "market_prob": _pct(item.get("market_prob")),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        "paper_stake": _rmb(item.get("suggested_paper_stake")),
        "risk_level": item.get("risk_label") or item.get("risk_level"),
        "reason": item.get("selection_reason") or item.get("correlation_reason") or "满足约束。",
        "legs": _legs(item) if is_combo else "",
    }


def _label(item: dict) -> str:
    if item.get("legs"):
        return "组合观察"
    return f"{item.get('home_team','')} vs {item.get('away_team','')} {item.get('outcome_label','')}".strip()


def _legs(item: dict) -> str:
    return "；".join(f"{leg.get('home_team','')} vs {leg.get('away_team','')} {leg.get('outcome_label','')}".strip() for leg in item.get("legs", []) or [])


def _rmb(value) -> str:
    try:
        return f"¥{float(value):,.2f}"
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


def _num(value) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "N/A"

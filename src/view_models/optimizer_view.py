from __future__ import annotations

PROFILE_LABELS = {"conservative": "保守", "balanced": "均衡", "aggressive": "进取"}


def build_optimizer_view(result: dict) -> dict:
    portfolio = result.get("selected_portfolio") or result.get("recommended_observation_portfolio", {}) or {}
    risk = result.get("risk_summary", {}) or {}
    rankings = result.get("candidate_rankings", {}) or {}
    comparison = result.get("profile_comparison", {}) or {}
    best_parlay = result.get("best_parlay_summary", {}) or {}
    return {
        "title": "赛前组合优化",
        "date": result.get("date") or result.get("selected_date"),
        "provider_used": result.get("provider_used", "unknown"),
        "matches_analyzed": result.get("matches_analyzed", result.get("matches_count", 0)),
        "candidate_pool_count": result.get("candidate_pool_count", 0),
        "risk_profile": result.get("risk_profile", "conservative"),
        "risk_profile_label": result.get("risk_profile_label") or PROFILE_LABELS.get(result.get("risk_profile"), "保守"),
        "summary_cards": [
            {"label": "观察日期", "value": result.get("date") or result.get("selected_date") or "N/A", "help": "本次赛前优化使用的可售比赛日期。"},
            {"label": "实际数据源", "value": result.get("provider_used", "unknown"), "help": "Sporttery 成功时显示 sporttery，回退时显示 fallback/mock。"},
            {"label": "分析比赛数", "value": result.get("matches_analyzed", result.get("matches_count", 0)), "help": "进入本次赛前优化的可售比赛数量。"},
            {"label": "候选池", "value": result.get("candidate_pool_count", 0), "help": "进入严格筛选前的候选观察项数量。"},
            {"label": "风险档位", "value": result.get("risk_profile_label") or PROFILE_LABELS.get(result.get("risk_profile"), "保守"), "help": "保守 / 均衡 / 进取只影响纸面观察约束。"},
            {"label": "当前本金", "value": _rmb(result.get("bankroll")), "help": "用于计算纸面观察金额。"},
            {"label": "每日暴露上限", "value": _rmb(result.get("daily_exposure_cap")), "help": "按风险档位计算。"},
            {"label": "推荐纸面投入", "value": _rmb(result.get("recommended_paper_exposure")), "help": "本次组合优化建议的总纸面投入。"},
            {"label": "单关观察", "value": len(portfolio.get("singles", []) or []), "help": "满足 EV、Edge、风险约束的单关候选。"},
            {"label": "2串1观察", "value": len(portfolio.get("parlay_2x1", []) or []), "help": "考虑相关性折扣后的组合观察。"},
            {"label": "3串1观察", "value": len(portfolio.get("parlay_3x1", []) or []), "help": "默认关闭，进取档才会展示。"},
        ],
        "singles_table": [_row(item) for item in portfolio.get("singles", []) or []],
        "parlay_2x1_table": [_row(item) for item in portfolio.get("parlay_2x1", []) or []],
        "parlay_3x1_table": [_row(item) for item in portfolio.get("parlay_3x1", []) or []],
        "candidate_rankings": {
            "singles": [_ranking_row(item) for item in rankings.get("singles", []) or []],
            "parlay_2x1": [_ranking_row(item) for item in rankings.get("parlay_2x1", []) or []],
            "parlay_3x1": [_ranking_row(item) for item in rankings.get("parlay_3x1", []) or []],
        },
        "profile_comparison": [_comparison_row(key, value) for key, value in comparison.items()],
        "best_parlay_summary": best_parlay,
        "best_parlay_cards": _best_parlay_cards(best_parlay),
        "best_parlay_table": _best_parlay_table(best_parlay),
        "rejected_table": [_rejected_row(item) for item in list(result.get("rejected_candidates", []) or [])],
        "risk_summary": risk,
        "explanations": list(result.get("explanations", []) or []),
        "no_2x1_reason": result.get("no_2x1_reason", "当前没有 2串1 入选；请查看候选排行榜和被拒原因。"),
        "warnings": list(result.get("warnings", []) or []),
        "disclaimer": result.get("disclaimer", "仅供纸面模拟和概率研究，不构成投注建议。"),
    }


def _row(item: dict) -> dict:
    is_combo = bool(item.get("legs"))
    return {
        "type": _type_label(item.get("candidate_type")),
        "match": _label(item),
        "odds": _num(item.get("odds") or item.get("combo_odds")),
        "model_prob": _pct(item.get("model_prob") or item.get("combo_prob")),
        "market_prob": _pct(item.get("market_prob")),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        "confidence": _pct(item.get("observation_confidence") or item.get("confidence_score")),
        "confidence_label_zh": item.get("confidence_label_zh", ""),
        "odds_status_zh": item.get("odds_status_zh", ""),
        "ev_status_zh": item.get("ev_status_zh", ""),
        "recommended_action_zh": item.get("recommended_action_zh", ""),
        "paper_stake": _rmb(item.get("suggested_paper_stake")),
        "risk_level": item.get("risk_label") or item.get("risk_level"),
        "reason": item.get("selection_reason") or item.get("correlation_reason") or "满足约束。",
        "legs": _legs(item) if is_combo else "",
    }


def _ranking_row(item: dict) -> dict:
    return {
        "type": _type_label(item.get("type")),
        "match": item.get("match", ""),
        "legs": item.get("legs", ""),
        "odds": _num(item.get("odds")),
        "model_prob": _pct(item.get("model_prob")),
        "market_prob": _pct(item.get("market_prob")),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        "confidence": _pct(item.get("observation_confidence") or item.get("confidence_score")),
        "confidence_label_zh": item.get("confidence_label_zh", ""),
        "recommended_action_zh": item.get("recommended_action_zh", ""),
        "correlation_discount": _num(item.get("correlation_discount")),
        "risk_level": item.get("risk_level", ""),
        "paper_stake": _rmb(item.get("paper_stake")),
        "status": item.get("status", "未入选"),
        "reject_reason": item.get("reject_reason", ""),
    }


def _rejected_row(item: dict) -> dict:
    return {
        "type": _type_label(item.get("type")),
        "match": item.get("match", ""),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        "risk_level": item.get("risk_level", ""),
        "paper_stake": _rmb(item.get("paper_stake")),
        "reason": item.get("reason", "未入选"),
    }


def _comparison_row(key: str, value: dict) -> dict:
    return {
        "profile": value.get("risk_profile_label") or PROFILE_LABELS.get(key, key),
        "daily_exposure_cap": _rmb(value.get("daily_exposure_cap")),
        "recommended_paper_exposure": _rmb(value.get("recommended_paper_exposure")),
        "singles_count": value.get("singles_count", 0),
        "parlay_2x1_count": value.get("parlay_2x1_count", 0),
        "parlay_3x1_count": value.get("parlay_3x1_count", 0),
        "note": value.get("no_2x1_reason", ""),
    }


def _best_parlay_cards(best: dict) -> list[dict]:
    best_single = best.get("best_single") or {}
    best2 = best.get("best_2x1") or {}
    best3 = best.get("best_3x1_if_allowed") or {}
    risk_adjusted = best.get("best_risk_adjusted_combo") or {}
    return [
        {"label": "最佳单关", "value": _short_candidate(best_single), "help": best_single.get("selected_reason_zh", "")},
        {"label": "最佳2串1", "value": _short_candidate(best2), "help": best2.get("reject_reason") or best2.get("selected_reason_zh", "")},
        {"label": "最佳3串1", "value": _short_candidate(best3), "help": best3.get("reject_reason") or best3.get("selected_reason_zh", "")},
        {"label": "风险调整最佳", "value": _short_candidate(risk_adjusted), "help": best.get("conclusion_zh", "")},
    ]


def _best_parlay_table(best: dict) -> list[dict]:
    rows = []
    for label, key in [
        ("最佳单关", "best_single"),
        ("最佳2串1", "best_2x1"),
        ("最佳3串1", "best_3x1_if_allowed"),
        ("最稳组合", "safest_combo"),
        ("最高EV组合", "highest_ev_combo"),
        ("风险调整最佳", "best_risk_adjusted_combo"),
    ]:
        item = best.get(key) or {}
        rows.append(
            {
                "category": label,
                "candidate": item.get("legs") or item.get("match") or item.get("message_zh", "暂无"),
                "status": item.get("status", ""),
                "odds": _num(item.get("odds")),
                "model_prob": _pct(item.get("model_prob")),
                "market_prob": _pct(item.get("market_prob")),
                "ev": _signed_pct(item.get("ev")),
                "edge": _signed_pct(item.get("edge")),
                "confidence": _pct(item.get("confidence_score")),
                "correlation_discount": _num(item.get("correlation_discount")),
                "risk_adjusted_score": _num(item.get("risk_adjusted_score")),
                "paper_stake": _rmb(item.get("paper_stake")),
                "reason": item.get("selected_reason_zh") or item.get("reject_reason") or "",
                "opposing_factors": item.get("opposing_factors_zh", ""),
            }
        )
    return rows


def _short_candidate(item: dict) -> str:
    if not item or item.get("status") == "empty":
        return "暂无"
    label = item.get("legs") or item.get("match") or "候选"
    status = item.get("status")
    return f"{status} · {label}" if status else str(label)


def _type_label(value) -> str:
    return {"single": "单关", "parlay_2x1": "2串1", "parlay_3x1": "3串1"}.get(str(value), str(value or ""))


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

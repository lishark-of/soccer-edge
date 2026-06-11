from __future__ import annotations


def explain_signal_reliability(row: dict, context: dict) -> dict:
    completeness = context.get("intelligence_completeness") or {}
    source_cov = context.get("source_coverage") or {}
    play_type = row.get("play_type")
    model_prob = _float(row.get("model_prob") or row.get("probability"), 0.0)
    ev = row.get("ev")
    edge = row.get("edge")
    has_official_odds = bool(row.get("official_odds"))
    market_conf = 0.75 if has_official_odds else 0.25
    model_conf = 0.55 if play_type in {"had", "hhad"} else 0.42 if play_type == "total_goals" else 0.32
    intelligence_conf = _float(completeness.get("score"), 0.0) / 100.0
    source_conf = _source_confidence(source_cov)
    backtest_support = 0.45
    final = market_conf * 0.30 + model_conf * 0.25 + intelligence_conf * 0.20 + backtest_support * 0.15 + source_conf * 0.10
    if play_type == "correct_score":
        final -= 0.10
    if play_type == "total_goals":
        final -= 0.03
    final = max(0.05, min(0.95, final))
    label = _confidence_label(final)
    action = _recommended_action(final, ev, edge, play_type)
    odds_status = "官方赔率已接入" if has_official_odds else "该玩法官方赔率未接入"
    ev_status = "可计算 EV" if ev is not None else "暂不能计算 EV"
    return {
        "observation_confidence": round(final, 4),
        "confidence_label_zh": label,
        "confidence_breakdown": {
            "market_confidence": round(market_conf, 3),
            "model_confidence": round(model_conf, 3),
            "intelligence_completeness": round(intelligence_conf, 3),
            "backtest_support": round(backtest_support, 3),
            "source_reliability": round(source_conf, 3),
        },
        "odds_status_zh": odds_status,
        "ev_status_zh": ev_status,
        "recommended_action_zh": action,
        "reliability_explanation_zh": _explanation(row, completeness, odds_status, ev_status, label),
        "support_summary_zh": _support_summary(row, source_cov),
        "opposition_summary_zh": _opposition_summary(row, completeness),
    }


def explain_combo_discipline(row: dict, completeness_by_match: dict | None = None) -> dict:
    ev = _float(row.get("ev"), None)
    edge = _float(row.get("edge"), None)
    prob = _float(row.get("model_prob") or row.get("combo_prob"), 0.0)
    reasons = []
    if edge is None or edge < 0.02:
        reasons.append("Edge 较薄，赔率优势不够厚。")
    if ev is None or ev < 0.04:
        reasons.append("EV 不足，不能覆盖组合风险。")
    if prob < 0.18:
        reasons.append(f"组合命中概率约 {prob * 100:.1f}%，同时命中压力较高。")
    reasons.append("串关会把多场不确定性相乘，相关性折扣后吸引力下降。")
    reasons.append("伤停、首发、天气或战意缺失时，组合信心额外下降。")
    return {
        "discipline_breakdown": reasons,
        "discipline_summary_zh": "；".join(reasons),
        "final_judgement_zh": "不进入观察清单" if reasons else "可进入观察清单",
    }


def explain_score_goal_reliability(row: dict) -> dict:
    play = row.get("play_type")
    if play == "correct_score":
        return {
            "reliability_label_zh": "偏低",
            "usage_zh": "只作比分倾向参考，不适合作为强信号。",
            "why_zh": "比分是精确事件，天然波动高；当前缺少官方比分赔率、首发、伤停和天气。",
        }
    if play == "total_goals":
        return {
            "reliability_label_zh": "中等",
            "usage_zh": "适合观察比赛节奏偏大/偏小，不等于结果承诺。",
            "why_zh": "总进球是区间判断，比精确比分稳定，但仍依赖首发、天气和节奏信息。",
        }
    return {"reliability_label_zh": "中", "usage_zh": "结合赔率、EV、Edge 和情报完整度观察。", "why_zh": "胜平负/让球赔率已接入时可计算 EV。"}


def _source_confidence(coverage: dict) -> float:
    score = 0.45
    if (coverage.get("api_football") or {}).get("status") == "matched":
        score += 0.18
    if (coverage.get("the_odds_api") or {}).get("status") == "matched":
        score += 0.18
    if (coverage.get("sporttery") or {}).get("status") == "matched":
        score += 0.14
    return min(1.0, score)


def _confidence_label(value: float) -> str:
    if value >= 0.70:
        return "高"
    if value >= 0.55:
        return "中"
    if value >= 0.40:
        return "中低"
    return "低"


def _recommended_action(value: float, ev, edge, play_type: str | None) -> str:
    if play_type == "correct_score":
        return "弱观察：仅看比分倾向，不作为强信号。"
    if ev is None or edge is None:
        return "等待赔率：当前只能看模型概率，暂不能判断价值。"
    if value >= 0.55 and _float(ev, 0) > 0 and _float(edge, 0) > 0:
        return "可观察：赔率与模型存在一定差异，但仍需看缺失情报。"
    if _float(ev, 0) > 0:
        return "弱观察：EV 为正但信心不足，先观察。"
    return "放弃：当前没有足够观察价值。"


def _explanation(row: dict, completeness: dict, odds_status: str, ev_status: str, label: str) -> str:
    direction = row.get("direction", "观察项")
    score = completeness.get("score", "N/A")
    return f"{direction} 当前可信度 {label}；{odds_status}，{ev_status}；情报完整度 {score}/100。"


def _support_summary(row: dict, source_cov: dict) -> str:
    parts = list(row.get("supporting_factors") or [])
    if (source_cov.get("the_odds_api") or {}).get("status") == "matched":
        parts.append("海外赔率可作为交叉参考。")
    if (source_cov.get("api_football") or {}).get("status") == "matched":
        parts.append("API-Football 已匹配赛程补充。")
    return "；".join(parts) or "暂无强支持因素。"


def _opposition_summary(row: dict, completeness: dict) -> str:
    parts = list(row.get("opposing_factors") or [])
    gaps = completeness.get("main_gaps_zh") or []
    if gaps:
        parts.append("缺口：" + "、".join(gaps[:4]))
    return "；".join(parts) or "主要反对因素暂不明显。"


def _float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

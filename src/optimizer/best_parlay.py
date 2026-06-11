from __future__ import annotations


def build_best_parlay_summary(optimizer_result: dict) -> dict:
    rankings = optimizer_result.get("candidate_rankings") or {}
    selected = optimizer_result.get("selected_portfolio") or {}
    singles = _merge_rows(selected.get("singles", []), rankings.get("singles", []), "single")
    parlay2 = _merge_rows(selected.get("parlay_2x1", []), rankings.get("parlay_2x1", []), "parlay_2x1")
    parlay3 = _merge_rows(selected.get("parlay_3x1", []), rankings.get("parlay_3x1", []), "parlay_3x1")
    combos = parlay2 + parlay3
    rejected = [row for row in combos if not row.get("selected")]
    selected_combos = [row for row in combos if row.get("selected")]
    return {
        "summary_version": "phase2p_best_parlay_v0",
        "risk_profile": optimizer_result.get("risk_profile"),
        "risk_profile_label": optimizer_result.get("risk_profile_label"),
        "best_single": _best(singles, key="risk_adjusted_score"),
        "best_2x1": _best(parlay2, key="risk_adjusted_score"),
        "best_3x1_if_allowed": _best(parlay3, key="risk_adjusted_score"),
        "safest_combo": _best(combos, key="safety_score"),
        "highest_ev_combo": _best(combos, key="ev"),
        "best_risk_adjusted_combo": _best(combos, key="risk_adjusted_score"),
        "selected_combos": selected_combos[:10],
        "rejected_combos": rejected[:20],
        "conclusion_zh": _conclusion(singles, parlay2, parlay3),
        "risk_note_zh": "优秀串联只代表纸面观察排序。串关需要多场同时命中，会显著放大波动；不要因为组合赔率高就提高信心。",
        "disclaimer": "仅用于观察信号、纸面模拟和风险诊断，不构成投注建议。",
    }


def _merge_rows(selected_rows: list[dict], ranking_rows: list[dict], kind: str) -> list[dict]:
    rows = []
    for row in selected_rows or []:
        rows.append(_normalize_row(row, kind, selected=True))
    seen = {_row_key(row) for row in rows}
    for row in ranking_rows or []:
        normalized = _normalize_row(row, kind, selected=bool(row.get("selected")))
        key = _row_key(normalized)
        if key not in seen:
            rows.append(normalized)
            seen.add(key)
    return sorted(rows, key=lambda item: item.get("risk_adjusted_score", -999), reverse=True)


def _normalize_row(row: dict, kind: str, selected: bool) -> dict:
    odds = _float(row.get("odds") or row.get("combo_odds"))
    model_prob = _float(row.get("model_prob") or row.get("combo_prob"))
    market_prob = _float(row.get("market_prob"))
    ev = _float(row.get("ev"))
    edge = _float(row.get("edge"))
    confidence = _float(row.get("observation_confidence") or row.get("confidence_score"), default=0.45)
    correlation_discount = _float(row.get("correlation_discount"), default=1.0)
    risk = str(row.get("risk_level") or "medium")
    status = "入选" if selected or row.get("status") == "入选" else "未入选"
    reject_reason = row.get("reject_reason") or row.get("reason") or ("已入选" if status == "入选" else "未通过组合纪律。")
    hard_invalid = odds <= 1.01 or "同场互斥" in str(reject_reason)
    risk_penalty = {"low": 0.0, "medium": 0.08, "high": 0.18, "very_high": 0.32}.get(risk, 0.10)
    agreement = max(0.0, 1.0 - min(1.0, abs(model_prob - market_prob) * 4)) if model_prob and market_prob else 0.35
    odds_quality = min(1.0, odds / 5.0) if odds else 0.0
    normalized_ev = max(-1.0, min(1.0, ev / 0.25)) if ev is not None else -0.2
    low_correlation = max(0.0, min(1.0, correlation_discount))
    drawdown_safety = max(0.0, 1.0 - risk_penalty)
    combo_score = 0.35 * normalized_ev + 0.20 * confidence + 0.15 * agreement + 0.10 * odds_quality + 0.10 * low_correlation + 0.10 * drawdown_safety
    risk_adjusted = combo_score - risk_penalty
    if hard_invalid:
        combo_score = -999.0
        risk_adjusted = -999.0
    return {
        "type": row.get("type") or row.get("candidate_type") or kind,
        "label_zh": _type_label(kind),
        "match": row.get("match") or _match_label(row),
        "legs": row.get("legs") or _legs_label(row),
        "odds": odds,
        "model_prob": model_prob,
        "market_prob": market_prob,
        "ev": ev,
        "edge": edge,
        "confidence_score": round(confidence, 4),
        "market_model_agreement": round(agreement, 4),
        "odds_quality": round(odds_quality, 4),
        "correlation_discount": round(correlation_discount, 4),
        "drawdown_safety": round(drawdown_safety, 4),
        "combo_score": round(combo_score, 4),
        "risk_adjusted_score": round(risk_adjusted, 4),
        "safety_score": round(drawdown_safety + low_correlation - max(0, odds_quality - 0.6) * 0.2, 4),
        "paper_stake": _float(row.get("paper_stake") or row.get("suggested_paper_stake"), default=0.0),
        "risk_level": risk,
        "selected": status == "入选",
        "status": status,
        "selected_reason_zh": "该组合不可作为优秀串联。" if hard_invalid else _selected_reason(ev, edge, confidence, correlation_discount, risk),
        "opposing_factors_zh": _opposing_factors(row, model_prob, market_prob, confidence, risk),
        "missing_intelligence_zh": row.get("missing_signals") or row.get("missing_intelligence") or "查看数据可靠性页。",
        "reject_reason": reject_reason,
        "parlay_risk_note_zh": "串关需要所有腿同时命中，组合概率会低于单腿概率。",
    }


def _best(rows: list[dict], key: str) -> dict:
    if not rows:
        return {"status": "empty", "message_zh": "当前没有可排序候选。"}
    valid = [item for item in rows if _float(item.get(key), default=-999) > -900 and _float(item.get("odds"), default=0) > 1.01]
    if not valid:
        nearest = rows[0]
        return {
            "status": "empty",
            "message_zh": f"当前没有合格候选；最近被拒原因：{nearest.get('reject_reason', '未通过组合纪律。')}",
            "reject_reason": nearest.get("reject_reason", "未通过组合纪律。"),
        }
    selected = sorted(valid, key=lambda item: _float(item.get(key), default=-999), reverse=True)[0]
    return selected


def _conclusion(singles: list[dict], parlay2: list[dict], parlay3: list[dict]) -> str:
    best2 = _best(parlay2, "risk_adjusted_score")
    best3 = _best(parlay3, "risk_adjusted_score")
    if best2.get("status") == "入选":
        return "当前存在 2串1 纸面观察，但仍需重点查看相关性折扣、缺失情报和回撤风险。"
    if best2.get("status") == "未入选":
        return f"当前最优组合仍未入选，首要原因：{best2.get('reject_reason', '未通过组合纪律')}"
    if singles:
        return "当前最优观察主要来自单关，不宜为了组合赔率强行串联。"
    if best3.get("status") == "未入选":
        return f"3串1 风险更高，当前不建议启用；原因：{best3.get('reject_reason', '未通过组合纪律')}"
    return "当前候选不足，严格交易者结论为等待更可靠数据。"


def _selected_reason(ev, edge, confidence, correlation, risk) -> str:
    return f"EV {ev:.1%}、Edge {edge:.1%}、可信度 {confidence:.1%}、相关性折扣 {correlation:.2f}、风险 {risk}。"


def _opposing_factors(row: dict, model_prob: float, market_prob: float, confidence: float, risk: str) -> str:
    factors = []
    if model_prob and market_prob and abs(model_prob - market_prob) < 0.02:
        factors.append("模型与市场差距较薄")
    if confidence < 0.55:
        factors.append("外部情报不足导致信心不高")
    if risk in {"high", "very_high"}:
        factors.append("风险等级偏高")
    if row.get("reject_reason"):
        factors.append(str(row.get("reject_reason")))
    return "；".join(dict.fromkeys(factors)) or "暂无明显反对因素，但仍需遵守纸面观察纪律。"


def _row_key(row: dict) -> str:
    return "|".join(str(row.get(key, "")) for key in ("type", "match", "legs", "odds", "model_prob"))


def _type_label(kind: str) -> str:
    return {"single": "单关", "parlay_2x1": "2串1", "parlay_3x1": "3串1"}.get(kind, kind)


def _match_label(row: dict) -> str:
    return f"{row.get('home_team', '')} vs {row.get('away_team', '')} {row.get('outcome_label', '')}".strip()


def _legs_label(row: dict) -> str:
    legs = row.get("legs") or []
    if isinstance(legs, str):
        return legs
    return "；".join(_match_label(leg) for leg in legs)


def _float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

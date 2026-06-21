from __future__ import annotations

from itertools import combinations

from src.optimizer.correlation import correlation_discount, correlation_quality, correlation_reason, same_match_forbidden


def build_candidate_pool(analysis: dict) -> list[dict]:
    candidates = []
    for item in list(analysis.get("single_candidates", []) or []):
        odds = _float(item.get("odds"))
        model_prob = _float(item.get("model_prob"))
        market_prob = _float(item.get("fair_prob") if item.get("fair_prob") is not None else item.get("market_prob"))
        if odds <= 1 or model_prob <= 0 or market_prob <= 0:
            continue
        edge = model_prob - market_prob
        ev = model_prob * odds - 1.0
        candidates.append(
            {
                "candidate_type": "single",
                "match_id": item.get("match_id") or f"{item.get('date','')}:{item.get('home_team','')}:{item.get('away_team','')}",
                "date": item.get("date") or analysis.get("date"),
                "league": item.get("league", ""),
                "home_team": item.get("home_team", ""),
                "away_team": item.get("away_team", ""),
                "play_type": item.get("play_type", "had"),
                "outcome_key": item.get("outcome_key", ""),
                "outcome_label": item.get("outcome_label") or item.get("outcome_key", ""),
                "odds": round(odds, 4),
                "market_prob": round(market_prob, 6),
                "model_prob": round(model_prob, 6),
                "edge": round(edge, 6),
                "ev": round(ev, 6),
                "risk_level": item.get("risk_level", "medium"),
                "risk_label": item.get("risk_label", _risk_label(item.get("risk_level"))),
                "market_probability_audit": item.get("market_probability_audit", {}),
                "market_bias_audit": item.get("market_bias_audit", {}),
                "source": "analysis",
            }
        )
    return sorted(candidates, key=lambda item: (item["ev"], item["edge"]), reverse=True)


def build_parlay_candidates(candidates: list[dict], max_legs: int = 3) -> list[dict]:
    results = []
    max_size = max(2, int(max_legs or 2))
    for size in range(2, max_size + 1):
        for legs in combinations(candidates, size):
            legs = [dict(leg) for leg in legs]
            if same_match_forbidden(legs):
                results.append({"candidate_type": f"parlay_{size}x1", "rejected": True, "reject_reason": "同场互斥", "legs": legs, "correlation_quality": correlation_quality(legs)})
                continue
            discount = correlation_discount(legs)
            quality = correlation_quality(legs)
            combo_odds = 1.0
            combo_prob_raw = 1.0
            market_prob = 1.0
            min_edge = min(float(leg.get("edge") or 0.0) for leg in legs)
            for leg in legs:
                combo_odds *= float(leg["odds"])
                combo_prob_raw *= float(leg["model_prob"])
                market_prob *= float(leg["market_prob"])
            combo_prob = combo_prob_raw * discount
            combo_ev = combo_prob * combo_odds - 1.0
            risk = "high" if size >= 3 or discount < 0.95 else "medium"
            results.append(
                {
                    "candidate_type": f"parlay_{size}x1",
                    "pass_type": f"{size}x1",
                    "legs": legs,
                    "combo_odds": round(combo_odds, 4),
                    "combo_prob": round(combo_prob, 6),
                    "combo_prob_raw": round(combo_prob_raw, 6),
                    "market_prob": round(market_prob, 6),
                    "correlation_discount": round(discount, 4),
                    "correlation_reason": correlation_reason(legs),
                    "correlation_quality": quality,
                    "edge": round(min_edge, 6),
                    "ev": round(combo_ev, 6),
                    "risk_level": risk,
                    "risk_label": _risk_label(risk),
                    "market_probability_audit": _combo_audit_summary(legs, "market_probability_audit"),
                    "market_bias_audit": _combo_audit_summary(legs, "market_bias_audit"),
                }
            )
    return sorted(results, key=lambda item: item.get("ev", -999), reverse=True)


def _float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _risk_label(value) -> str:
    return {"low": "低", "medium": "中", "high": "高", "very_high": "很高"}.get(str(value or "medium"), "中")


def _combo_audit_summary(legs: list[dict], key: str) -> dict:
    audits = [leg.get(key) or {} for leg in legs if isinstance(leg, dict) and isinstance(leg.get(key), dict)]
    audits = [audit for audit in audits if audit]
    if not audits:
        return {}
    worst_shift = max((_float(audit.get("outcome_method_shift") if key == "market_bias_audit" else audit.get("max_method_shift")) for audit in audits), default=0.0)
    risky = [audit for audit in audits if str(audit.get("status") or "").lower() in {"unstable", "longshot_watch", "wide_margin"} or str(audit.get("outcome_bias_bucket") or "") == "longshot"]
    first = risky[0] if risky else audits[0]
    return {
        **first,
        "legs_checked": len(audits),
        "risky_legs_count": len(risky),
        "outcome_method_shift": round(worst_shift, 6),
        "max_method_shift": round(worst_shift, 6),
        "message_zh": first.get("message_zh") or first.get("outcome_message_zh") or "组合腿已进行赔率市场审计。",
    }

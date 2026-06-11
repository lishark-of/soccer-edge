from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.intelligence.completeness import build_intelligence_completeness, build_overall_completeness
from src.intelligence.feature_context import build_match_context
from src.intelligence.market_signals import odds_for_outcome
from src.intelligence.news_signals import load_external_signals_with_status
from src.intelligence.signal_explainer import explain_signal_reliability, explain_score_goal_reliability
from src.intelligence.source_coverage import build_source_coverage
from src.intelligence.coverage_status import normalize_coverage_status
from src.optimizer.best_parlay import build_best_parlay_summary
from src.optimizer.portfolio_optimizer import optimize_portfolio
from src.providers.factory import create_provider
from src.models.score_matrix import normalize_probs

DEFAULT_WEIGHTS = {
    "market_no_vig": 0.55,
    "poisson_xg": 0.20,
    "elo": 0.15,
    "dixon_coles": 0.05,
    "context": 0.05,
}
OUTCOME_LABELS = {"home": "主胜", "draw": "平", "away": "客胜"}
OUTCOME_KEYS = {"home": "win", "draw": "draw", "away": "lose"}


def fused_probability(match_context: dict, weights: dict | None = None) -> dict:
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    sources = {
        "market_no_vig": match_context.get("market_no_vig", {}).get("had", {}),
        "poisson_xg": match_context.get("poisson_xg", {}).get("outcome_probs", {}),
        "elo": match_context.get("elo_strength", {}),
        "dixon_coles": match_context.get("dixon_coles", {}).get("outcome_probs", {}),
        "context": _context_probs(match_context),
    }
    fused = _weighted_probs(sources, weights)
    hhad = _weighted_probs(
        {
            "market_no_vig": match_context.get("market_no_vig", {}).get("hhad", {}),
            "dixon_coles": match_context.get("hhad_probs", {}),
        },
        {"market_no_vig": 0.75, "dixon_coles": 0.25},
    )
    return {
        "had": fused,
        "hhad": hhad,
        "total_goals": match_context.get("total_goals", {}),
        "top_scores": match_context.get("top_scores", []),
        "confidence_score": match_context.get("confidence_score", 0.5),
    }


def build_intelligence_preview(provider_name: str = "auto", target_date: str | None = None, external_signals_path: str | None = None, bankroll: float = 10000.0, risk_profile: str = "aggressive") -> dict:
    from src.audit.credibility import audit_credibility

    provider = create_provider(provider_name)
    external_signals, external_signal_status = load_external_signals_with_status(external_signals_path)
    matches = provider.get_matches(target_date)
    source_coverage = build_source_coverage(matches, target_date)
    source_coverage_by_match = source_coverage.get("by_match_id", {})
    match_ids = _external_match_keys(matches)
    contexts = []
    observations = []
    optimizer_candidates = []
    for match in matches:
        context = build_match_context(match, external_signals=_external_signal_for_match(external_signals, match))
        match_coverage = source_coverage_by_match.get(str(match.match_id), {})
        context["source_coverage"] = match_coverage
        context["match_identity"] = match_coverage.get("identity", {})
        _apply_enriched_signals(context, match_coverage)
        context["intelligence_completeness"] = build_intelligence_completeness(context, match_coverage)
        fused = fused_probability(context)
        context["fused_probability"] = fused
        match_observations, match_candidates = build_observations_from_context(context)
        contexts.append(context)
        observations.extend(match_observations)
        optimizer_candidates.extend(match_candidates)
    provider_meta = _provider_meta(provider, provider_name)
    overall_completeness = build_overall_completeness(contexts)
    optimizer = optimize_portfolio(optimizer_candidates, bankroll=bankroll, config={"risk_profile": risk_profile, "compare_profiles": True, "enable_3x1": risk_profile == "aggressive"})
    credibility_audit = audit_credibility(
        {
            "provider_used": provider_meta.get("provider_used", provider_name),
            "intelligence_completeness": overall_completeness,
            "contexts": contexts,
            "optimizer": optimizer,
        },
        optimizer,
    )
    optimizer = _apply_credibility_gate(optimizer, credibility_audit)
    data_source_status = {
        "requested_provider": provider_name,
        "provider_used": provider_meta.get("provider_used", provider_name),
        "matches_count": len(matches),
        "status": "available" if matches else "empty",
        "warnings": list(provider_meta.get("provider_warnings", []) or []),
        "message_zh": "已读取可售竞彩足球比赛。" if matches else "当前日期未读取到可售比赛，系统可继续尝试未来日期。",
    }
    return {
        "intelligence_version": "phase2o_intelligence_fusion_v0",
        "date": target_date,
        "provider": provider_name,
        **provider_meta,
        "data_source_status": data_source_status,
        "source_coverage": source_coverage,
        "intelligence_completeness": overall_completeness,
        "reliability_summary": _reliability_summary(source_coverage, overall_completeness),
        "external_signals_status": _external_signals_status(external_signals_path, external_signals, match_ids, external_signal_status),
        "matches_count": len(matches),
        "contexts": contexts,
        "observations": observations,
        "optimizer_candidates": optimizer_candidates,
        "optimizer": optimizer,
        "credibility_audit": credibility_audit,
        "credibility_gate": credibility_audit.get("credibility_gate", {}),
        "top_single_observations": _top([item for item in observations if item["play_type"] in {"had", "hhad"} and item.get("official_odds")], 8),
        "top_total_goals_observations": _top([item for item in observations if item["play_type"] == "total_goals"], 5, key="probability"),
        "top_score_observations": _top([item for item in observations if item["play_type"] == "correct_score"], 5, key="probability"),
        "missing_signals": sorted({signal for context in contexts for signal in context.get("missing_signals", [])}),
        "warnings": list(dict.fromkeys(list(provider_meta.get("provider_warnings", [])) + list(source_coverage.get("warnings", [])))),
        "disclaimer": "赛前情报融合仅用于观察信号、纸面模拟和风险诊断，不构成投注建议。",
    }


def build_next_available_preview(
    provider_name: str = "auto",
    start_date: str | None = None,
    bankroll: float = 10000.0,
    risk_profile: str = "aggressive",
    days_ahead: int = 3,
    external_signals_path: str | None = None,
) -> dict:
    start = _parse_date(start_date)
    attempts = []
    first_preview = None
    first_available = None
    max_offset = max(0, days_ahead)
    for offset in range(max_offset + 1):
        current = (start + timedelta(days=offset)).isoformat()
        preview = build_intelligence_preview(provider_name, current, external_signals_path, bankroll=bankroll, risk_profile=risk_profile)
        if first_preview is None:
            first_preview = preview
        attempts.append(
            {
                "date": current,
                "matches_count": preview.get("matches_count", 0),
                "provider_used": preview.get("provider_used", provider_name),
                "status": preview.get("data_source_status", {}).get("status", "unknown"),
            }
        )
        if first_available is None and preview.get("matches_count", 0) > 0:
            first_available = preview
            break
    best = dict(first_available or first_preview or {})
    selected_date = best.get("date") or start.isoformat()
    best["selected_date"] = selected_date
    best["attempts"] = attempts
    best["scan_window"] = {
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=max_offset)).isoformat(),
        "days_checked": len(attempts),
        "complete": bool(first_available) or len(attempts) == max_offset + 1,
        "stopped_after_first_available": bool(first_available),
        "selection_rule": "从今天开始向后查找，找到第一个 matches_count > 0 的日期即停止；如果都为空，则返回首日空结果。",
    }
    best["next_available_version"] = "phase2o_next_available_v0"
    best["top_observations"] = {
        "singles": best.get("top_single_observations", [])[:5],
        "parlay_2x1": (best.get("optimizer", {}).get("selected_portfolio", {}) or {}).get("parlay_2x1", [])[:5],
        "total_goals": best.get("top_total_goals_observations", [])[:5],
        "scores": best.get("top_score_observations", [])[:5],
    }
    best["data_source_status"] = {
        **(best.get("data_source_status", {}) or {}),
        "selected_date": selected_date,
        "attempts": attempts,
        "scan_window": best["scan_window"],
        "message_zh": "已自动找到可售比赛。" if best.get("matches_count", 0) else "未来 1-3 天暂未读取到可售比赛。",
    }
    return best


def _external_signal_for_match(signals: dict[str, dict], match) -> dict:
    keys = [
        str(getattr(match, "match_id", "") or ""),
        str(getattr(match, "match_no", "") or ""),
        f"{getattr(match, 'home_team', '')}__{getattr(match, 'away_team', '')}",
    ]
    for key in keys:
        if key and key in signals:
            return signals[key]
    return {}


def _external_match_keys(matches: list) -> list[str]:
    keys = []
    for match in matches:
        for key in (
            getattr(match, "match_id", None),
            getattr(match, "match_no", None),
            f"{getattr(match, 'home_team', '')}__{getattr(match, 'away_team', '')}",
        ):
            if key:
                keys.append(str(key))
    return sorted(dict.fromkeys(keys))


def _apply_credibility_gate(optimizer: dict, credibility: dict) -> dict:
    gated = dict(optimizer or {})
    gate = credibility.get("credibility_gate", {}) or {}
    combo_gate = gate.get("combo_gate")
    selected = {**(gated.get("selected_portfolio") or {})}
    no_combo_reason = gate.get("reason_zh", "可信度不足、情报缺失较多、组合风险高于模型优势。")
    if combo_gate == "closed":
        selected["parlay_2x1"] = []
        selected["parlay_3x1"] = []
        _mark_rankings_gate(gated, "未通过可信度门控")
        gated["no_combo_reason"] = no_combo_reason
    elif combo_gate == "restricted":
        selected["parlay_3x1"] = []
        selected["parlay_2x1"] = [
            item for item in selected.get("parlay_2x1", []) or []
            if str(item.get("risk_level", "medium")) == "low"
        ]
        _mark_rankings_gate(gated, "可信度中低，仅允许低风险 2串1")
        gated["no_combo_reason"] = no_combo_reason if not selected.get("parlay_2x1") else ""
    gated["selected_portfolio"] = selected
    gated["recommended_observation_portfolio"] = selected
    gated["credibility_audit"] = credibility
    gated["credibility_gate"] = gate
    gated["best_parlay_summary"] = build_best_parlay_summary(gated)
    return gated


def _mark_rankings_gate(optimizer: dict, reason: str) -> None:
    rankings = optimizer.get("candidate_rankings") or {}
    for key in ("parlay_2x1", "parlay_3x1"):
        for row in rankings.get(key, []) or []:
            if row.get("selected"):
                row["selected"] = False
                row["status"] = "未入选"
            row["reject_reason"] = reason if not row.get("reject_reason") or row.get("reject_reason") == "已入选" else f"{reason}；{row.get('reject_reason')}"


def _external_signals_status(path: str | None, signals: dict[str, dict], match_ids: list[str], load_status: dict | None = None) -> dict:
    load_status = load_status or {}
    provided = bool(path)
    signal_ids = set(signals)
    match_id_set = set(match_ids)
    matched_ids = sorted(signal_ids & match_id_set)
    unmatched_ids = sorted(signal_ids - match_id_set)
    missing_match_ids = sorted(match_id_set - signal_ids)
    return {
        "source_type": load_status.get("source_type") or ("user_json" if provided else "not_provided"),
        "path_provided": provided,
        "path_label": load_status.get("path_label") or (Path(path).name if path else None),
        "load_status": load_status.get("load_status") or ("loaded" if provided else "not_provided"),
        "signals_loaded": len(signals),
        "invalid_items": load_status.get("invalid_items", 0),
        "matches_count": len(match_ids),
        "matched_count": len(matched_ids),
        "unmatched_count": len(unmatched_ids),
        "missing_match_count": len(missing_match_ids),
        "matched_match_ids": matched_ids,
        "unmatched_signal_ids": unmatched_ids,
        "message_zh": load_status.get("message_zh") or ("已读取用户提供的本地 JSON 情报；仅用于解释信心，不参与真实下单。" if provided else "未提供外部情报 JSON；新闻、伤停、首发、天气、战意保持 unknown。"),
    }


def build_observations_from_context(context: dict) -> tuple[list[dict], list[dict]]:
    match = context["match"]
    fused = fused_probability(context)
    observations = []
    candidates = []
    for play_type, probs, odds_map in (
        ("had", fused.get("had", {}), context.get("sporttery_odds", {}).get("had", {})),
        ("hhad", fused.get("hhad", {}), context.get("sporttery_odds", {}).get("hhad", {})),
    ):
        for outcome, prob in probs.items():
            odds = odds_for_outcome(odds_map, outcome)
            market_prob = context.get("market_no_vig", {}).get(play_type, {}).get(outcome)
            if not odds or not market_prob:
                continue
            ev = prob * odds - 1.0
            edge = prob - market_prob
            row = _observation(match, play_type, outcome, odds, market_prob, prob, edge, ev, context)
            observations.append(row)
            candidates.append(_candidate_from_observation(row))
    for total, prob in sorted((fused.get("total_goals") or {}).items(), key=lambda item: item[1], reverse=True):
        observations.append(_model_only_observation(match, "total_goals", f"总进球 {total}", prob, context))
    for score in fused.get("top_scores", [])[:5]:
        observations.append(_model_only_observation(match, "correct_score", f"比分 {score['score']}", score["probability"], context))
    observations.sort(key=lambda item: (item.get("ev") is not None, item.get("ev") or item.get("probability") or 0.0), reverse=True)
    return observations, candidates


def explain_trade_discipline(result: dict) -> list[str]:
    optimizer = result.get("optimizer", result)
    selected = optimizer.get("selected_portfolio", {})
    messages = []
    if not any(selected.get(key) for key in ("singles", "parlay_2x1", "parlay_3x1")):
        messages.append("无观察价值：当前候选没有通过 EV、Edge、风险或纸面暴露约束。")
    else:
        messages.append("入选原因：入选项通过市场去水概率、模型融合概率、EV、Edge 和纸面风险约束。")
    messages.append("拒绝原因：未入选项通常是 EV 不足、Edge 不足、风险等级过高、相关性折扣后不达标，或超过纸面暴露上限。")
    messages.append("赔率价值判断：只有模型融合概率足以覆盖官方赔率隐含概率时，才可能形成观察价值；否则显示“无观察价值”。")
    messages.append("串关纪律：2串1/3串1 会把多场不确定性叠加，不要因为赔率高就盲目组合。")
    missing = result.get("missing_signals") or []
    if missing:
        messages.append(f"信心下降因素：{', '.join(missing)} 未接入，新闻/伤停/天气/首发不得臆造。")
    return messages


def _parse_date(value: str | None) -> date:
    if value:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def _weighted_probs(sources: dict[str, dict], weights: dict[str, float]) -> dict[str, float]:
    acc = {"home": 0.0, "draw": 0.0, "away": 0.0}
    active_weight = 0.0
    for source, probs in sources.items():
        if not probs:
            continue
        weight = float(weights.get(source, 0.0))
        if weight <= 0:
            continue
        normalized = normalize_probs({key: probs.get(key, 0.0) for key in acc})
        for key in acc:
            acc[key] += normalized.get(key, 0.0) * weight
        active_weight += weight
    if active_weight <= 0:
        return {"home": 0.34, "draw": 0.32, "away": 0.34}
    return normalize_probs(acc)


def _context_probs(context: dict) -> dict[str, float]:
    base = context.get("market_no_vig", {}).get("had") or context.get("poisson_xg", {}).get("outcome_probs", {})
    confidence = float(context.get("confidence_score", 0.5) or 0.5)
    shrink = 0.08 * (1.0 - confidence)
    return normalize_probs({key: value * (1.0 - shrink) + shrink / 3.0 for key, value in base.items()})


def _observation(match: dict, play_type: str, outcome: str, odds: float, market_prob: float, model_prob: float, edge: float, ev: float, context: dict) -> dict:
    row = {
        "match_id": match["match_id"],
        "match_no": match.get("match_no", ""),
        "league": match.get("league", ""),
        "home_team": match.get("home_team", ""),
        "away_team": match.get("away_team", ""),
        "play_type": play_type,
        "direction": OUTCOME_LABELS.get(outcome, outcome),
        "outcome_key": OUTCOME_KEYS.get(outcome, outcome),
        "official_odds": round(float(odds), 4),
        "market_prob": round(float(market_prob), 6),
        "model_prob": round(float(model_prob), 6),
        "probability": round(float(model_prob), 6),
        "edge": round(float(edge), 6),
        "ev": round(float(ev), 6),
        "confidence_score": context.get("confidence_score", 0.5),
        "risk_level": _risk_level(model_prob, play_type),
        "supporting_factors": _supporting_factors(edge, ev, context),
        "opposing_factors": _opposing_factors(edge, ev, context),
        "missing_signals": context.get("missing_signals", []),
        "selection_status": "candidate" if ev > 0 and edge > 0 else "rejected",
        "selection_reason": "有观察价值" if ev > 0 and edge > 0 else "无观察价值：赔率未覆盖模型概率或 Edge 不足",
    }
    row.update(explain_signal_reliability(row, context))
    return row


def _model_only_observation(match: dict, play_type: str, direction: str, probability: float, context: dict) -> dict:
    row = {
        "match_id": match["match_id"],
        "match_no": match.get("match_no", ""),
        "league": match.get("league", ""),
        "home_team": match.get("home_team", ""),
        "away_team": match.get("away_team", ""),
        "play_type": play_type,
        "direction": direction,
        "official_odds": None,
        "market_prob": None,
        "model_prob": round(float(probability), 6),
        "probability": round(float(probability), 6),
        "edge": None,
        "ev": None,
        "confidence_score": context.get("confidence_score", 0.5),
        "risk_level": "model_only",
        "supporting_factors": ["由 Poisson/xG + Dixon-Coles 比分矩阵推导。"],
        "opposing_factors": ["该玩法官方赔率未接入，暂不能计算 EV。"],
        "missing_signals": context.get("missing_signals", []),
        "selection_status": "model_only",
        "selection_reason": "仅展示模型概率，等待官方赔率接入。",
    }
    row.update(explain_signal_reliability(row, context))
    row.update(explain_score_goal_reliability(row))
    return row


def _candidate_from_observation(row: dict) -> dict:
    return {
        "candidate_type": "single",
        "match_id": row["match_id"],
        "date": "",
        "league": row["league"],
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "play_type": row["play_type"],
        "outcome_key": row["outcome_key"],
        "outcome_label": row["direction"],
        "odds": row["official_odds"],
        "market_prob": row["market_prob"],
        "model_prob": row["model_prob"],
        "edge": row["edge"],
        "ev": row["ev"],
        "risk_level": row["risk_level"] if row["risk_level"] in {"low", "medium", "high"} else "medium",
        "risk_label": {"low": "低", "medium": "中", "high": "高"}.get(row["risk_level"], "中"),
        "confidence_score": row["confidence_score"],
        "supporting_factors": row["supporting_factors"],
        "opposing_factors": row["opposing_factors"],
        "missing_signals": row["missing_signals"],
        "observation_confidence": row.get("observation_confidence"),
        "confidence_label_zh": row.get("confidence_label_zh"),
        "confidence_breakdown": row.get("confidence_breakdown", {}),
        "reliability_explanation_zh": row.get("reliability_explanation_zh"),
        "recommended_action_zh": row.get("recommended_action_zh"),
        "odds_status_zh": row.get("odds_status_zh"),
        "ev_status_zh": row.get("ev_status_zh"),
    }


def _risk_level(probability: float, play_type: str) -> str:
    if play_type == "hhad":
        return "medium" if probability >= 0.28 else "high"
    if probability >= 0.42:
        return "low"
    if probability >= 0.25:
        return "medium"
    return "high"


def _supporting_factors(edge: float, ev: float, context: dict) -> list[str]:
    factors = []
    if edge > 0:
        factors.append("模型融合概率高于市场去水概率。")
    if ev > 0:
        factors.append("官方赔率相对模型概率形成正 EV。")
    if context.get("confidence_score", 0) >= 0.55:
        factors.append("基础赔率与模型信号一致性尚可。")
    return factors or ["暂无强支持因素。"]


def _opposing_factors(edge: float, ev: float, context: dict) -> list[str]:
    factors = []
    if edge <= 0:
        factors.append("模型概率未超过市场去水概率。")
    if ev <= 0:
        factors.append("赔率未覆盖模型概率。")
    if context.get("missing_signals"):
        factors.append("新闻、伤停、首发或天气等情报未接入。")
    return factors or ["主要反对因素暂不明显。"]


def _top(items: list[dict], limit: int, key: str = "ev") -> list[dict]:
    return sorted(items, key=lambda item: item.get(key) if item.get(key) is not None else -999, reverse=True)[:limit]


def _provider_meta(provider, requested: str) -> dict:
    warnings = list(dict.fromkeys(list(getattr(provider, "warnings", [])) + list(getattr(provider, "messages", []))))
    provider_used = getattr(provider, "provider_used", getattr(provider, "provider_name", requested))
    return {"provider_requested": requested, "provider_used": provider_used, "fallback_used": bool(getattr(provider, "fallback_used", False)), "provider_warnings": warnings}


def _apply_enriched_signals(context: dict, coverage: dict) -> None:
    signals = context.setdefault("signals", {})
    mapping = {
        "injuries": "injuries",
        "lineup": "lineup",
        "weather": "weather",
        "news": "news",
    }
    for signal_key, coverage_key in mapping.items():
        enriched = coverage.get(coverage_key) or {}
        if not enriched:
            continue
        current = signals.get(signal_key) or {}
        if current.get("status") in {"connected", "confirmed", "user_supplied"}:
            continue
        signals[signal_key] = {
            "status": _signal_status_for_context(enriched.get("status")),
            "raw_status": enriched.get("status"),
            "impact": enriched.get("impact", "unknown"),
            "items": enriched.get("items", []),
            "message_zh": enriched.get("message_zh") or enriched.get("label_zh") or "",
            "source": "auto_enrichment",
        }


def _signal_status_for_context(status: str | None) -> str:
    normalized = normalize_coverage_status(status)
    if normalized in {"confirmed", "user_supplied"}:
        return "connected"
    if normalized in {"checked_empty", "fallback_estimated"}:
        return "basic_only"
    return "not_connected"


def _reliability_summary(source_coverage: dict, completeness: dict) -> dict:
    cards = source_coverage.get("source_cards", []) or []
    return {
        "overall_label_zh": completeness.get("label_zh", "unknown"),
        "overall_score": completeness.get("score", 0),
        "main_gaps_zh": completeness.get("main_gaps_zh", []),
        "partial_gaps_zh": completeness.get("partial_gaps_zh", []),
        "source_cards": cards,
        "summary_zh": f"{completeness.get('summary_zh', '')} {source_coverage.get('summary_zh', '')}".strip(),
        "decision_guide_zh": "优先看 Sporttery 官方赔率和已匹配的第三方补充；缺伤停/首发/天气时，信号自动降为观察或弱观察。",
    }

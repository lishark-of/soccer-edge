from __future__ import annotations

from src.intelligence.missing_info import build_missing_info_from_preview


def audit_credibility(preview: dict | None = None, optimizer_result: dict | None = None, backtest_result: dict | None = None, operation_result: dict | None = None) -> dict:
    preview = preview or {}
    optimizer_result = optimizer_result or preview.get("optimizer") or {}
    score = 100.0
    reasons: list[str] = []
    missing: list[str] = []
    must_not: list[str] = []

    provider_used = str(preview.get("provider_used") or optimizer_result.get("provider_used") or "unknown")
    if provider_used in {"mock", "fallback", "fixture"}:
        score -= 25
        reasons.append("当前包含 mock/fallback/fixture 数据，可信度最高只能到 medium。")
        must_not.append("不要把演示数据当作真实可售比赛。")
    elif provider_used == "sporttery":
        reasons.append("Sporttery 主数据可用，官方赔率与可售比赛可信度较高。")
    else:
        score -= 12
        reasons.append("实际数据源不明确，降低可信度。")

    completeness = preview.get("intelligence_completeness") or {}
    completeness_score = float(completeness.get("score") or 0)
    if completeness_score:
        score = min(score, 45 + completeness_score * 0.65)
        reasons.append(f"情报完整度 {completeness_score:.1f}/100，外部情报缺失会压低最终可信度。")
    miss = build_missing_info_from_preview(preview) if preview.get("contexts") else {"missing_information": [], "partial_information": []}
    missing = list(dict.fromkeys(list(miss.get("missing_information", [])) + list(completeness.get("main_gaps_zh", []))))
    partial = list(dict.fromkeys(list(miss.get("partial_information", [])) + list(completeness.get("partial_gaps_zh", []))))
    if missing:
        score -= min(18, len(missing) * 3)
        reasons.append("缺失情报会扣分：" + "、".join(missing[:6]))
    if partial:
        score -= min(10, len(partial) * 1.5)
        reasons.append("部分覆盖信息需要谨慎：" + "、".join(partial[:6]))

    selected = optimizer_result.get("selected_portfolio") or {}
    all_selected = list(selected.get("singles", []) or []) + list(selected.get("parlay_2x1", []) or []) + list(selected.get("parlay_3x1", []) or [])
    if all_selected:
        thin = [item for item in all_selected if float(item.get("edge") or 0) < 0.025 or float(item.get("ev") or 0) < 0.04]
        high_risk = [item for item in all_selected if str(item.get("risk_level", "medium")) in {"high", "very_high"} or item.get("legs")]
        if thin:
            score -= 8
            reasons.append("部分入选观察 Edge/EV 较薄，高 EV 不等于高可信。")
            must_not.append("不要只因为 EV 为正就提高信心。")
        if high_risk:
            score -= min(12, len(high_risk) * 3)
            reasons.append("组合或高风险观察会放大回撤与连续亏损概率。")
            must_not.append("串关赔率高不代表更可靠。")
    else:
        score -= 8
        reasons.append("当前没有通过纪律的观察组合，说明边际优势不足或数据不足。")

    if backtest_result:
        sample = _first_number(backtest_result, ["sample_size", "valid_matches", "matches", "total_matches"])
        if sample is not None and sample < 100:
            score -= 8
            reasons.append(f"回测样本量 {sample} 偏少，稳定性不足。")
    else:
        must_not.append("没有同口径真实历史回测时，不要过度相信赛前输出。")

    score = max(0, min(100, round(score)))
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 45 else "D"
    confidence = "high" if score >= 80 else "medium" if score >= 55 else "low"
    if provider_used in {"mock", "fallback", "fixture"} and confidence == "high":
        confidence = "medium"
        grade = min(grade, "B")
    return {
        "credibility_score": score,
        "grade": grade,
        "confidence_level": confidence,
        "confidence_level_zh": {"high": "高", "medium": "中", "low": "低"}[confidence],
        "reasons": reasons,
        "missing_information": missing,
        "partial_information": partial,
        "must_not_overtrust": list(dict.fromkeys(must_not)),
        "dimensions": {
            "probability_calibration": "需要结合 Brier / Log loss / calibration bins；当前赛前页只做即时观察。",
            "sample_size": "fixture/mock 只用于演示；真实 CSV 样本越大越可信。",
            "data_source_quality": provider_used,
            "missing_intelligence": missing,
            "model_agreement": "市场、Poisson/xG、Elo、Dixon-Coles 分歧越大，可信度越低。",
            "edge_quality": "EV 和 Edge 必须同时足够，且不能替代情报完整度。",
            "risk_quality": "串关腿数、相关性折扣、回撤风险会降低评分。",
            "stability": "保守/均衡/进取结果差异越大，越应谨慎。",
        },
        "disclaimer": "可信度审计只用于观察信号和风险诊断，不构成投注建议。",
    }


def _first_number(payload: dict, keys: list[str]) -> float | None:
    for key in keys:
        try:
            if key in payload:
                return float(payload[key])
        except (TypeError, ValueError):
            continue
    return None

from __future__ import annotations

from src.audit.credibility import audit_credibility
from src.optimizer.best_parlay import build_best_parlay_summary


def build_trader_review(preview: dict, optimizer_result: dict | None = None) -> dict:
    optimizer = optimizer_result or preview.get("optimizer") or {}
    credibility = audit_credibility(preview, optimizer)
    best = optimizer.get("best_parlay_summary") or build_best_parlay_summary(optimizer)
    conclusions = []
    selected = optimizer.get("selected_portfolio") or {}
    singles_count = len(selected.get("singles", []) or [])
    p2_count = len(selected.get("parlay_2x1", []) or [])
    p3_count = len(selected.get("parlay_3x1", []) or [])
    if singles_count and not p2_count:
        conclusions.append("当前最优观察主要来自单关，不宜为了组合赔率强行串关。")
    if p2_count:
        conclusions.append("当前存在 2串1 纸面观察，必须同时看相关性折扣、组合命中概率和缺失情报。")
    else:
        best2 = best.get("best_2x1") or {}
        conclusions.append("当前没有足够强的 2串1 入选。" + (f"最接近候选原因：{best2.get('reject_reason')}" if best2.get("reject_reason") else ""))
    if p3_count:
        conclusions.append("当前有 3串1 纸面观察，但这是最高风险组合，只能作研究。")
    else:
        best3 = best.get("best_3x1_if_allowed") or {}
        conclusions.append("当前没有足够理由启用 3串1。" + (f"原因：{best3.get('reject_reason')}" if best3.get("reject_reason") else ""))
    if credibility.get("missing_information"):
        conclusions.append("缺少 " + "、".join(credibility["missing_information"][:5]) + "，信心降级。")
    return {
        "review_version": "phase2p_trader_review_v0",
        "selected_date": preview.get("selected_date") or preview.get("date"),
        "provider_used": preview.get("provider_used"),
        "credibility": credibility,
        "best_parlay": best,
        "conclusions_zh": conclusions,
        "final_call_zh": _final_call(credibility, best, p2_count, p3_count),
        "fixed_language_zh": "所有结论使用观察、纸面模拟和风险诊断语言，不提供真实交易动作。",
        "disclaimer": "严厉交易者复盘不构成投注建议，不提供投注、下单、支付、代购或自动化购彩能力。",
    }


def _final_call(credibility: dict, best: dict, p2_count: int, p3_count: int) -> str:
    score = int(credibility.get("credibility_score") or 0)
    if score < 55:
        return "可信度偏低，优先补齐情报或等待更多数据，不应强行组合。"
    if p3_count:
        return "进取档出现 3串1，但严厉交易者只允许纸面跟踪，不建议放大风险。"
    if p2_count:
        return "可观察少量 2串1，但必须接受组合命中概率下降和回撤放大。"
    return "当前纪律更偏向单关或弱观察，优秀串联不足。"

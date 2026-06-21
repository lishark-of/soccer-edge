from __future__ import annotations

from src.audit.credibility import audit_credibility
from src.view_models.intelligence_view import build_intelligence_coverage_table
from src.optimizer.best_parlay import build_best_parlay_summary


def build_trader_review(preview: dict, optimizer_result: dict | None = None) -> dict:
    optimizer = optimizer_result or preview.get("optimizer") or {}
    credibility = audit_credibility(preview, optimizer)
    gate = credibility.get("credibility_gate", {})
    pro_score = credibility.get("professional_model_score", {})
    best = optimizer.get("best_parlay_summary") or build_best_parlay_summary(optimizer)
    daily_2x1 = best.get("daily_2x1_candidate") or {}
    daily_3x1 = best.get("daily_3x1_candidate") or {}
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
        if _has_paper_candidate(daily_2x1):
            conclusions.append(_paper_combo_review_line("2串1", daily_2x1))
        else:
            conclusions.append("当前没有足够强的 2串1 通过门控观察项。" + (f"最接近候选原因：{best2.get('reject_reason')}" if best2.get("reject_reason") else ""))
    if p3_count:
        conclusions.append("当前有 3串1 纸面观察，但这是最高风险组合，只能作研究。")
    else:
        best3 = best.get("best_3x1_if_allowed") or {}
        if _has_paper_candidate(daily_3x1):
            conclusions.append(_paper_combo_review_line("3串1", daily_3x1))
        else:
            conclusions.append("当前没有足够理由启用 3串1。" + (f"原因：{best3.get('reject_reason')}" if best3.get("reject_reason") else ""))
    if credibility.get("missing_information"):
        conclusions.append("缺少 " + "、".join(credibility["missing_information"][:5]) + "，信心降级。")
    if pro_score:
        conclusions.append(pro_score.get("summary_zh", "职业模型成熟度仍需结合市场、校准和赛后学习验证。"))
    return {
        "review_version": "phase2p_trader_review_v0",
        "selected_date": preview.get("selected_date") or preview.get("date"),
        "provider_used": preview.get("provider_used"),
        "credibility": credibility,
        "credibility_gate": gate,
        "professional_model_score": pro_score,
        "intelligence_coverage": build_intelligence_coverage_table(preview),
        "best_parlay": best,
        "no_combo_reason": optimizer.get("no_combo_reason") or best.get("no_combo_reason") or gate.get("reason_zh", ""),
        "conclusions_zh": conclusions,
        "final_call_zh": _final_call(credibility, best, p2_count, p3_count),
        "post_match_review_policy_zh": _post_match_review_policy(best),
        "path_to_95_zh": pro_score.get("missing_to_95", []),
        "fixed_language_zh": "所有结论使用观察、纸面模拟和风险诊断语言，不提供真实交易动作。",
        "disclaimer": "严厉交易者复盘不构成投注建议，不提供投注、下单、支付、代购或自动化购彩能力。",
    }


def _has_paper_candidate(candidate: dict) -> bool:
    if not isinstance(candidate, dict) or not candidate:
        return False
    status = str(candidate.get("status") or candidate.get("selection_status") or "")
    return bool(candidate.get("legs") or candidate.get("match")) and status not in {"empty", "missing"}


def _paper_combo_review_line(label: str, candidate: dict) -> str:
    legs = candidate.get("legs") or candidate.get("match") or "候选腿待补齐"
    reason = (
        candidate.get("selected_reason_zh")
        or candidate.get("review_focus_zh")
        or candidate.get("reject_reason")
        or candidate.get("hit_rate_discipline_zh")
        or "用于检查组合纪律是否过严，以及赛后是否需要调整拒绝规则。"
    )
    return (
        f"没有通过门控的强{label}，但每日{label}纸面候选已进入赛后复盘：{legs}。"
        f"复盘重点：{reason}"
    )


def _post_match_review_policy(best: dict) -> str:
    daily_2x1 = best.get("daily_2x1_candidate") or {}
    daily_3x1 = best.get("daily_3x1_candidate") or {}
    tracked = []
    if _has_paper_candidate(daily_2x1):
        tracked.append("每日2串1纸面候选")
    if _has_paper_candidate(daily_3x1):
        tracked.append("每日3串1纸面候选")
    if not tracked:
        return "赛后复盘会审核单关、被拒组合和已有学习样本；若没有纸面组合候选，会记录为空样本而不是假装有组合。"
    return "赛后复盘必须审核" + "、".join(tracked) + "，即使它们未通过可信度门控；目的在于验证系统是否过度拒绝组合。"


def _final_call(credibility: dict, best: dict, p2_count: int, p3_count: int) -> str:
    score = int(credibility.get("credibility_score") or 0)
    gate = credibility.get("credibility_gate", {})
    workflow = credibility.get("prematch_workflow") or {}
    is_t_plus = str(workflow.get("stage") or "").startswith("t_plus_")
    if gate.get("combo_gate") == "closed" or score < 50:
        if is_t_plus:
            return "T+1 暂不最终串联：先保留预观察，等待首发、终盘赔率、伤停和临场天气复核。"
        return "暂不强行串联：可信度偏低，优先补齐情报或等待更多数据。"
    if score < 55:
        if is_t_plus:
            return "T+1 只保留弱观察：候选可以跟踪，但组合需要赛日复核后再决定。"
        return "可信度偏低，只保留弱观察，不应强行组合。"
    if p3_count:
        return "进取档出现 3串1，但严厉交易者只允许纸面跟踪，不建议放大风险。"
    if p2_count:
        return "可观察少量 2串1，但必须接受组合命中概率下降和回撤放大。"
    return "当前纪律更偏向单关或弱观察，优秀串联不足。"

from __future__ import annotations

PROFILE_LABELS = {"conservative": "保守", "balanced": "均衡", "aggressive": "进取"}


def build_optimizer_view(result: dict) -> dict:
    portfolio = result.get("selected_portfolio") or result.get("recommended_observation_portfolio", {}) or {}
    risk = result.get("risk_summary", {}) or {}
    rankings = result.get("candidate_rankings", {}) or {}
    comparison = result.get("profile_comparison", {}) or {}
    best_parlay = result.get("best_parlay_summary", {}) or {}
    clv = result.get("clv_tracking", {}) or {}
    credibility = result.get("credibility_audit", {}) or {}
    professional_score = credibility.get("professional_model_score", {}) or result.get("professional_model_score", {}) or {}
    gate = result.get("credibility_gate", {}) or {}
    ai = result.get("ai_combo_research", {}) or {}
    llm = result.get("llm_status", {}) or {}
    ai_status = _ai_research_status(ai, llm)
    trader_review = result.get("trader_review", {}) or {}
    play_bias = result.get("play_bias_diagnostics", {}) or {}
    play_type_learning_status = result.get("play_type_learning_status", {}) or {}
    strategy_adjustment_status = result.get("strategy_adjustment_status", {}) or {}
    probability_shrinkage_status = result.get("probability_shrinkage_status", {}) or {}
    no_combo_reason = result.get("no_combo_reason") or best_parlay.get("no_combo_reason") or gate.get("reason_zh", "")
    missing_information = list(gate.get("missing_information") or result.get("missing_signals") or [])
    combo_gate_summary = f"{gate.get('label_zh') or gate.get('combo_gate') or '待评估'}：{no_combo_reason or gate.get('reason_zh') or '请结合候选与被拒原因复盘。'}"
    ai_status_summary = ai_status.get("summary_zh") or ai.get("display_status_zh") or ai.get("ds_status_zh") or llm.get("status_detail_zh") or llm.get("status_zh") or "待检查"
    daily_candidate_brief = _daily_candidate_brief(best_parlay, professional_score, gate, play_bias, result)
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
            {"label": "可信度", "value": _credibility_value(credibility), "help": gate.get("reason_zh") or credibility.get("reasons", ["用于判断是否适合组合观察。"])[0]},
            {"label": "职业模型分", "value": _professional_score_value(professional_score), "help": professional_score.get("summary_zh", "按市场基准、模型融合、校准、CLV、组合纪律和赛后学习综合评分。")},
            {"label": "今日可用性", "value": daily_candidate_brief.get("score_zh", "待评估"), "help": daily_candidate_brief.get("summary_zh", "先看每日候选，再看复核清单。")},
            {"label": "串联纪律", "value": gate.get("label_zh") or "待评估", "help": no_combo_reason or "通过门控后才会进入优秀串联页。"},
            {"label": "AI研究", "value": ai_status.get("label_zh") or ai.get("ds_status_zh") or llm.get("status_zh") or "待检查", "help": ai_status_summary or llm.get("fallback_reason") or "用于解释强观察、被拒原因和赛后学习点。"},
            {"label": "玩法偏置", "value": play_bias.get("label_zh") or "待检查", "help": play_bias.get("summary_zh") or "检查候选是否过度集中在让球胜平负或同一方向。"},
            {"label": "玩法复盘", "value": _play_type_learning_status_label(play_type_learning_status), "help": play_type_learning_status.get("reason_zh") or "读取赛后玩法表现，用于降低历史表现偏弱的玩法。"},
            {"label": "学习调参", "value": _strategy_adjustment_status_label(strategy_adjustment_status), "help": strategy_adjustment_status.get("reason_zh") or "把赛后学习建议轻量应用到下一次候选排序。"},
            {"label": "概率校准", "value": _probability_shrinkage_status_label(probability_shrinkage_status), "help": probability_shrinkage_status.get("reason_zh") or "样本不足或 CLV 偏弱时，模型概率会向市场概率收缩。"},
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
            "singles": [_ranking_row(item, gate, missing_information) for item in rankings.get("singles", []) or []],
            "parlay_2x1": [_ranking_row(item, gate, missing_information) for item in rankings.get("parlay_2x1", []) or []],
            "parlay_3x1": [_ranking_row(item, gate, missing_information) for item in rankings.get("parlay_3x1", []) or []],
        },
        "profile_comparison": [_comparison_row(key, value) for key, value in comparison.items()],
        "best_parlay_summary": best_parlay,
        "daily_candidate_brief": daily_candidate_brief,
        "daily_output_lanes": best_parlay.get("daily_output_lanes", []),
        "best_parlay_cards": _best_parlay_cards(best_parlay),
        "best_parlay_table": _best_parlay_table(best_parlay),
        "no_combo_state": {
            "status": best_parlay.get("status") or ("no_combo" if no_combo_reason else "unknown"),
            "label_zh": best_parlay.get("label_zh") or ("暂无优秀串联观察" if no_combo_reason else "存在优秀串联观察"),
            "reason_zh": no_combo_reason,
        },
        "combo_gate_summary_zh": combo_gate_summary,
        "ai_status_summary_zh": ai_status_summary,
        "clv_tracking": _clv_view(clv),
        "rejected_table": [_rejected_row(item) for item in list(result.get("rejected_candidates", []) or [])],
        "risk_summary": risk,
        "llm_status": llm,
        "ai_combo_research": ai,
        "ai_research_status": ai_status,
        "ai_research_layer": {
            "config_status_zh": ai.get("config_status_zh") or (result.get("llm_status", {}) or {}).get("config_status_zh", ""),
            "runtime_notice_zh": ai.get("runtime_notice_zh") or (result.get("llm_status", {}) or {}).get("runtime_notice_zh", ""),
            "next_step_zh": ai.get("next_step_zh") or (result.get("llm_status", {}) or {}).get("next_step_zh", ""),
            "ds_status": ai.get("ds_status", ""),
            "ds_attempted": ai.get("ds_attempted", False),
            "ds_completed": ai.get("ds_completed", False),
            "ds_error_code": ai.get("ds_error_code", ""),
            "token_total": ai.get("token_total"),
            "display_status_zh": ai.get("display_status_zh") or ai_status_summary,
        },
        "credibility_gate": gate,
        "professional_model_score": professional_score,
        "play_bias_diagnostics": play_bias,
        "play_type_learning_status": play_type_learning_status,
        "strategy_adjustment_status": strategy_adjustment_status,
        "probability_shrinkage_status": probability_shrinkage_status,
        "trader_review": trader_review,
        "no_combo_reason": no_combo_reason,
        "daily_learning_metrics": result.get("daily_learning_metrics", []),
        "window_learning_metrics": result.get("window_learning_metrics", []),
        "latest_daily_summary_zh": result.get("latest_daily_summary_zh", ""),
        "window_learning_summaries_zh": result.get("window_learning_summaries_zh", []),
        "daily_learning_digest": result.get("daily_learning_digest", {}),
        "window_learning_digests": result.get("window_learning_digests", []),
        "explanations": _optimizer_explanations(result, play_bias),
        "no_2x1_reason": result.get("no_2x1_reason", result.get("no_combo_reason") or result.get("combo_gate") and "当前暂无通过门控的2串1观察项。" or "当前暂无通过门控的2串1观察；请先看单关与情报缺口再复核。"),
        "warnings": _filtered_optimizer_warnings(result),
        "disclaimer": result.get("disclaimer", "仅供纸面模拟和概率研究，不构成投注建议。"),
    }


def _optimizer_explanations(result: dict, play_bias: dict) -> list[str]:
    items = list(result.get("explanations", []) or [])
    if play_bias:
        items.insert(0, play_bias.get("summary_zh") or "玩法偏置诊断已完成。")
        if play_bias.get("next_step_zh"):
            items.insert(1, play_bias["next_step_zh"])
    return list(dict.fromkeys([str(item) for item in items if str(item).strip()]))


def _daily_candidate_brief(best_parlay: dict, professional_score: dict, gate: dict, play_bias: dict, result: dict | None = None) -> dict:
    result = result or {}
    lanes = list(best_parlay.get("daily_output_lanes") or [])
    evidence_score = _int_or_none(professional_score.get("score"))
    ceiling = _int_or_none(professional_score.get("ceiling_score")) or 95
    gate_mode = str(gate.get("combo_gate") or "")
    filled = [lane for lane in lanes if lane.get("status") not in {"empty", ""}]
    paper = [lane for lane in lanes if lane.get("status") == "paper_candidate"]
    selected = [lane for lane in lanes if lane.get("status") == "selected"]
    has_three_lanes = len(filled) >= 3
    play_bias_issue = bool((play_bias or {}).get("issues"))
    daily_diverse = _daily_combo_diversified(best_parlay)
    usability = 58
    if has_three_lanes:
        usability += 20
    elif filled:
        usability += 10
    if selected:
        usability += 5
    if paper:
        usability += 4
    if gate_mode == "closed":
        usability -= 3
    elif gate_mode == "restricted":
        usability += 1
    if play_bias_issue and not daily_diverse:
        usability -= 8
    elif play_bias_issue and daily_diverse:
        usability += 4
    else:
        usability += 5
    if evidence_score is not None and evidence_score >= 55:
        usability += 3
    if ceiling >= 64:
        usability += 2
    provider_used = str(result.get("provider_used") or "").lower()
    matches = _int_or_none(result.get("matches_analyzed") or result.get("matches_count")) or 0
    pool_count = _int_or_none(result.get("candidate_pool_count")) or 0
    if provider_used == "sporttery":
        usability += 5
    if matches >= 6:
        usability += 2
    if pool_count >= 30:
        usability += 3
    usability = max(0, min(95, round(usability)))
    if usability >= 82:
        label = "短赛会可用"
        headline = "今天可直接看三件套候选，再临场复核"
    elif usability >= 68:
        label = "可纸面观察"
        headline = "今天能看候选，但组合要谨慎"
    elif usability >= 52:
        label = "只适合预筛"
        headline = "先拿候选，重点等临场确认"
    else:
        label = "只适合学习"
        headline = "候选可复盘，不适合升级为强结论"
    blockers = []
    if gate_mode == "closed":
        blockers.append("可信度门控关闭")
    elif gate_mode == "restricted":
        blockers.append("串联只允许低风险纸面复核")
    if paper and not selected:
        blockers.append("2串1/3串1已给纸面候选，赛后验证是否过保守")
    if play_bias_issue and daily_diverse:
        blockers.append("候选池仍有偏置，但每日组合已做玩法/方向分散替代")
    elif play_bias_issue:
        blockers.append("玩法或方向存在同质化")
    if evidence_score is not None:
        blockers.append(f"长期证据分 {evidence_score}/{ceiling}")
    if provider_used == "sporttery":
        blockers.append(f"真实可售数据 {matches} 场，候选池 {pool_count} 项")
    if not blockers:
        blockers.append("继续复核终盘赔率、伤停和首发")
    return {
        "score": usability,
        "score_zh": f"{usability}/95",
        "label_zh": label,
        "headline_zh": headline,
        "summary_zh": "；".join(blockers[:4]),
        "evidence_score": evidence_score,
        "evidence_score_zh": f"{evidence_score}/{ceiling}" if evidence_score is not None else "待评估",
        "score_explain_zh": "短赛会实操分只评估今天是否能快速给出可复盘候选；长期职业分仍由赛后样本、CLV 和校准决定。",
        "provider_used": provider_used,
        "matches_count": matches,
        "candidate_pool_count": pool_count,
        "lanes_count": len(filled),
        "paper_candidate_count": len(paper),
        "selected_count": len(selected),
        "gate_zh": gate.get("label_zh") or gate_mode or "待评估",
        "next_action_zh": "先看每日三件套，再看同向/赔率覆盖/临场情报；赛后把结果回填学习。",
        "pre_match_checklist_zh": [
            "终盘前复核赔率是否反向漂移，尤其是让球胜平负方向。",
            "检查首发、伤停、天气和赛程密度；无法确认时只保留纸面观察。",
            "2串1/3串1逐腿确认玩法和方向不要过度同质化。",
            "如果模型概率与市场概率分歧扩大，优先降级，不强行升级组合。",
        ],
        "post_match_learning_checklist_zh": [
            "回填最终比分，计算单关、2串1、3串1是否命中。",
            "回填收盘赔率，用 CLV 检查赛前价格判断是否领先市场。",
            "更新 Brier Score / Log Loss，判断模型概率是否校准。",
            "复盘被替换或被拒的组合，验证规则是否过严或过松。",
        ],
}


def _daily_combo_diversified(best_parlay: dict) -> bool:
    for key in ("daily_2x1_candidate", "daily_3x1_candidate"):
        item = best_parlay.get(key) or {}
        play = str(item.get("play_type_zh") or item.get("play_type_mix_zh") or "")
        direction = str(item.get("direction_family_zh") or "")
        if "+" in play or "+" in direction:
            return True
    return False


def _ai_research_status(ai: dict, llm: dict) -> dict:
    direct = ai.get("ai_research_status")
    if isinstance(direct, dict) and direct.get("status"):
        return direct
    direct = llm.get("ai_research_status")
    if isinstance(direct, dict) and direct.get("status"):
        return direct
    error_code = str(ai.get("ds_error_code") or llm.get("ds_error_code") or llm.get("last_error_code") or "")
    error_label = str(llm.get("last_error_label_zh") or "")
    if ai.get("ds_status") == "cached":
        return {
            "status": "cached",
            "label_zh": "已复用 DS 研究",
            "error_code": error_code,
            "error_label_zh": error_label,
            "summary_zh": ai.get("display_status_zh") or ai.get("runtime_notice_zh") or "本轮已复用最近一次成功的 DS 研究结果。",
        }
    if ai.get("ds_completed"):
        return {
            "status": "done",
            "label_zh": "DS Pro 已参与",
            "error_code": "",
            "error_label_zh": "",
            "summary_zh": ai.get("display_status_zh") or ai.get("runtime_notice_zh") or "本轮已完成 DS Pro 研究。",
        }
    if ai.get("ds_attempted"):
        return {
            "status": "fallback",
            "label_zh": _fallback_label_zh(error_code, error_label),
            "error_code": error_code,
            "error_label_zh": error_label,
            "summary_zh": ai.get("fallback_reason") or ai.get("display_status_zh") or llm.get("runtime_notice_zh") or "本轮已自动尝试 DS，但当前回退为本地摘要。",
        }
    if llm.get("status") == "ready":
        return {
            "status": "ready",
            "label_zh": "等待自动研究",
            "error_code": "",
            "error_label_zh": "",
            "summary_zh": llm.get("next_step_zh") or "刷新今日观察或赛前优化后，会自动触发 DS 研究。",
        }
    if llm.get("status") in {"missing_api_key", "disabled", "unsupported_provider"}:
        return {
            "status": "not_configured",
            "label_zh": _config_label_zh(str(llm.get("status") or "")),
            "error_code": str(llm.get("status") or ""),
            "error_label_zh": _config_label_zh(str(llm.get("status") or "")),
            "summary_zh": llm.get("config_status_zh") or "请先检查 DeepSeek 开关、Provider 和 Key。",
        }
    return {
        "status": "unknown",
        "label_zh": "待检查",
        "error_code": error_code,
        "error_label_zh": error_label,
        "summary_zh": llm.get("status_detail_zh") or "当前还没有自动研究记录。",
    }


def _fallback_label_zh(error_code: str, error_label: str) -> str:
    if error_code == "invalid_api_key":
        return "Key 无效"
    if error_code == "insufficient_balance":
        return "额度不足"
    if error_code == "rate_limited":
        return "请求过频"
    if error_code == "request_timeout":
        return "请求超时"
    if error_code == "output_budget_exhausted":
        return "输出上限不足"
    if error_code == "reasoning_only_response":
        return "未返回最终正文"
    if error_code in {"provider_unavailable", "endpoint_not_found"}:
        return "服务暂不可用"
    if error_code == "network_error":
        return "请求失败"
    if error_label:
        return error_label
    return "已回退本地摘要"


def _config_label_zh(config_status: str) -> str:
    if config_status == "missing_api_key":
        return "缺少 API Key"
    if config_status == "disabled":
        return "未启用"
    if config_status == "unsupported_provider":
        return "Provider 不受支持"
    return "待配置"


def _row(item: dict) -> dict:
    is_combo = bool(item.get("legs"))
    market_audit = _market_audit_summary(item)
    return {
        "type": _type_label(item.get("candidate_type")),
        "play_type": item.get("play_type", ""),
        "play_type_zh": item.get("play_type_zh") or _play_type_label(item.get("play_type")),
        "direction": item.get("direction") or item.get("outcome_label") or "",
        "outcome_key": item.get("outcome_key", ""),
        "outcome_label": item.get("outcome_label") or item.get("direction") or "",
        "direction_family_zh": item.get("direction_family_zh") or _direction_family_label(item),
        "match": _label(item),
        "odds": _num(item.get("odds") or item.get("combo_odds")),
        "model_prob": _pct(item.get("model_prob") or item.get("combo_prob")),
        "market_prob": _pct(item.get("market_prob")),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        "confidence": _pct(item.get("observation_confidence") or item.get("confidence_score")),
        "calibrated_prob": _pct(item.get("calibrated_prob")),
        "calibrated_ev": _signed_pct(item.get("calibrated_ev")),
        "signal_category_zh": item.get("signal_category_zh", ""),
        "recommended_use_zh": item.get("recommended_use_zh", ""),
        "odds_bucket_zh": item.get("odds_bucket_zh", ""),
        "probability_bin": item.get("probability_bin", ""),
        "probability_bin_weight": item.get("probability_bin_weight"),
        "probability_bin_message_zh": item.get("probability_bin_message_zh", ""),
        "confidence_label_zh": item.get("confidence_label_zh", ""),
        "odds_status_zh": item.get("odds_status_zh", ""),
        "ev_status_zh": item.get("ev_status_zh", ""),
        "recommended_action_zh": item.get("recommended_action_zh", ""),
        "paper_stake": _rmb(item.get("suggested_paper_stake")),
        "risk_level": item.get("risk_label") or item.get("risk_level"),
        "reason": item.get("selection_reason") or item.get("correlation_reason") or "满足约束。",
        "decision_reason_zh": item.get("decision_reason_zh", ""),
        "odds_reading_zh": item.get("odds_reading_zh", ""),
        "parlay_policy_zh": item.get("parlay_policy_zh", ""),
        "hit_rate_discipline_zh": item.get("hit_rate_discipline_zh", ""),
        "longshot_warning": item.get("longshot_warning", ""),
        "play_type_learning_reason_zh": item.get("play_type_learning_reason_zh", ""),
        "play_type_learning": item.get("play_type_learning", {}),
        "strategy_adjustments_applied": item.get("strategy_adjustments_applied", []),
        "strategy_adjustment_penalty": item.get("strategy_adjustment_penalty"),
        "strategy_adjustment_reason_zh": item.get("strategy_adjustment_reason_zh", ""),
        "model_disagreement_reason_zh": item.get("model_disagreement_reason_zh", ""),
        "model_disagreement_penalty": item.get("model_disagreement_penalty"),
        "model_market_gap": _signed_pct(item.get("model_market_gap")),
        "raw_model_prob": _pct(item.get("raw_model_prob")),
        "raw_ev": _signed_pct(item.get("raw_ev")),
        "raw_edge": _signed_pct(item.get("raw_edge")),
        "probability_shrinkage_reason_zh": item.get("probability_shrinkage_reason_zh", ""),
        "probability_shrinkage_weight": _pct(item.get("probability_shrinkage_weight")),
        "market_benchmark_discipline_zh": ((item.get("probability_shrinkage") or {}).get("market_benchmark_discipline") or {}).get("message_zh", ""),
        "probability_interval": _probability_interval(item),
        "robust_edge": _signed_pct(item.get("robust_edge")),
        "robust_ev": _signed_pct(item.get("robust_ev")),
        "robust_value_label_zh": item.get("robust_value_label_zh", ""),
        "robust_value_reason_zh": item.get("robust_value_reason_zh", ""),
        "short_cycle_reason_zh": item.get("short_cycle_reason_zh", ""),
        "short_cycle_score_adjustment": item.get("short_cycle_score_adjustment", ""),
        "competition_segment_zh": item.get("competition_segment_zh", ""),
        "competition_segment_reason_zh": item.get("competition_segment_reason_zh", ""),
        "ai_factor_zh": item.get("ai_factor_zh", ""),
        "ai_factor_reason_zh": item.get("ai_factor_reason_zh", ""),
        "combo_homogeneity_reason_zh": item.get("combo_homogeneity_reason_zh", ""),
        "market_audit_zh": market_audit.get("summary_zh", ""),
        "market_bias_zh": market_audit.get("bias_zh", ""),
        "market_method_shift_zh": market_audit.get("method_shift_zh", ""),
        "market_audit_status_zh": market_audit.get("status_zh", ""),
        "market_audit_warning_zh": market_audit.get("warning_zh", ""),
        "legs": _legs(item) if is_combo else "",
    }


def _ranking_row(item: dict, gate: dict | None = None, missing_information: list[str] | None = None) -> dict:
    gate = gate or {}
    missing_information = [str(x) for x in (missing_information or []) if str(x).strip()]
    status = str(item.get("status") or "").strip()
    selected = bool(item.get("selected")) or status in {"selected", "pass", "通过门控", "selected_after_gate", "已通过"}
    reject_reason = str(item.get("reject_reason") or "").strip()
    decision_reason = str(item.get("decision_reason_zh") or "").strip()
    odds_reading = str(item.get("odds_reading_zh") or "").strip()
    parlay_policy = str(item.get("parlay_policy_zh") or "").strip()
    hit_rate_note = str(item.get("hit_rate_discipline_zh") or "").strip()
    market_audit = _market_audit_summary(item)
    concentration_note = str(item.get("play_concentration_reason_zh") or "").strip()
    play_learning_note = str(item.get("play_type_learning_reason_zh") or "").strip()
    strategy_adjustment_note = str(item.get("strategy_adjustment_reason_zh") or "").strip()
    model_disagreement_note = str(item.get("model_disagreement_reason_zh") or "").strip()
    shrinkage_note = str(item.get("probability_shrinkage_reason_zh") or "").strip()
    market_benchmark_note = str(((item.get("probability_shrinkage") or {}).get("market_benchmark_discipline") or {}).get("message_zh") or "").strip()
    robust_note = str(item.get("robust_value_reason_zh") or "").strip()
    short_cycle_note = str(item.get("short_cycle_reason_zh") or "").strip()
    ai_factor_label = str(item.get("ai_factor_zh") or "").strip()
    ai_factor_note = str(item.get("ai_factor_reason_zh") or "").strip()
    homogeneity_note = str(item.get("combo_homogeneity_reason_zh") or "").strip()
    risk_level = str(item.get("risk_level") or "").strip() or "待评估"
    gate_reason = str(gate.get("reason_zh") or "").strip()
    gate_label = str(gate.get("label_zh") or gate.get("combo_gate") or "").strip()
    coverage_line = f"情报缺口：{'、'.join(missing_information[:6])}" if missing_information else ""
    discipline_bits = []
    if selected:
        if decision_reason:
            discipline_bits.append(f"可进入原因：{decision_reason}")
        elif odds_reading:
            discipline_bits.append(f"可进入原因：{odds_reading}")
    else:
        if reject_reason:
            discipline_bits.append(f"未过门控原因：{reject_reason}")
        elif decision_reason:
            discipline_bits.append(f"未过门控原因：{decision_reason}")
        if gate_label or gate_reason:
            discipline_bits.append(f"门控：{gate_label or '待评估'}；{gate_reason or '当前仍需结合可信度与风险复核。'}")
    if hit_rate_note:
        discipline_bits.append(f"命中纪律：{hit_rate_note}")
    if market_audit.get("summary_zh"):
        discipline_bits.append(f"赔率审计：{market_audit['summary_zh']}")
    if model_disagreement_note:
        discipline_bits.append(f"模型分歧：{model_disagreement_note}")
    if shrinkage_note:
        discipline_bits.append(f"概率校准：{shrinkage_note}")
    if market_benchmark_note:
        discipline_bits.append(f"市场基准：{market_benchmark_note}")
    if robust_note:
        discipline_bits.append(f"稳健价值：{robust_note}")
    if short_cycle_note:
        discipline_bits.append(f"赛会短周期：{short_cycle_note}")
    if item.get("competition_segment_zh"):
        discipline_bits.append(f"赛事语境：{item.get('competition_segment_zh')}，{item.get('competition_segment_reason_zh') or '用于区分不同比赛类型的学习权重。'}")
    if ai_factor_label:
        discipline_bits.append(f"AI因子：{ai_factor_label}，{ai_factor_note or '用于赛后判断这类解释是否应继续加权。'}")
    if homogeneity_note:
        discipline_bits.append(f"同质化审计：{homogeneity_note}")
    if concentration_note:
        discipline_bits.append(f"玩法拥挤：{concentration_note}")
    if strategy_adjustment_note:
        discipline_bits.append(f"学习调参：{strategy_adjustment_note}")
    if parlay_policy:
        discipline_bits.append(f"组合纪律：{parlay_policy}")
    if coverage_line:
        discipline_bits.append(coverage_line)
    discipline_bits.append(f"风险：{risk_level}")
    return {
        "type": _type_label(item.get("type")),
        "play_type": item.get("play_type", ""),
        "play_type_zh": item.get("play_type_zh") or _play_type_label(item.get("play_type")),
        "direction": item.get("direction") or item.get("outcome_label") or "",
        "outcome_key": item.get("outcome_key", ""),
        "outcome_label": item.get("outcome_label") or item.get("direction") or "",
        "direction_family_zh": item.get("direction_family_zh") or _direction_family_label(item),
        "leg_play_types": item.get("leg_play_types", []),
        "leg_directions": item.get("leg_directions", []),
        "match": item.get("match", ""),
        "legs": item.get("legs", ""),
        "odds": _num(item.get("odds")),
        "model_prob": _pct(item.get("model_prob")),
        "market_prob": _pct(item.get("market_prob")),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        "confidence": _pct(item.get("observation_confidence") or item.get("confidence_score")),
        "calibrated_prob": _pct(item.get("calibrated_prob")),
        "calibrated_ev": _signed_pct(item.get("calibrated_ev")),
        "signal_category_zh": item.get("signal_category_zh", ""),
        "recommended_use_zh": item.get("recommended_use_zh", ""),
        "odds_bucket_zh": item.get("odds_bucket_zh", ""),
        "probability_bin": item.get("probability_bin", ""),
        "probability_bin_weight": item.get("probability_bin_weight"),
        "probability_bin_message_zh": item.get("probability_bin_message_zh", ""),
        "confidence_label_zh": item.get("confidence_label_zh", ""),
        "recommended_action_zh": item.get("recommended_action_zh", ""),
        "correlation_discount": _num(item.get("correlation_discount")),
        "correlation_quality_zh": (item.get("correlation_quality") or {}).get("label_zh", ""),
        "correlation_quality_reason_zh": (item.get("correlation_quality") or {}).get("reason_zh", ""),
        "risk_level": item.get("risk_level", ""),
        "paper_stake": _rmb(item.get("paper_stake")),
        "status": item.get("status", "待复核"),
        "reject_reason": reject_reason,
        "decision_reason_zh": decision_reason,
        "odds_reading_zh": odds_reading,
        "parlay_policy_zh": parlay_policy,
        "hit_rate_discipline_zh": hit_rate_note,
        "play_diversity": item.get("play_diversity", {}),
        "play_diversity_reason_zh": item.get("play_diversity_reason_zh", ""),
        "combo_homogeneity": item.get("combo_homogeneity", {}),
        "combo_homogeneity_reason_zh": item.get("combo_homogeneity_reason_zh", ""),
        "play_type_mix_zh": item.get("play_type_mix_zh", ""),
        "play_concentration_reason_zh": item.get("play_concentration_reason_zh", ""),
        "play_type_learning_reason_zh": item.get("play_type_learning_reason_zh", ""),
        "play_type_learning": item.get("play_type_learning", {}),
        "strategy_adjustments_applied": item.get("strategy_adjustments_applied", []),
        "strategy_adjustment_penalty": item.get("strategy_adjustment_penalty"),
        "strategy_adjustment_reason_zh": item.get("strategy_adjustment_reason_zh", ""),
        "model_disagreement_reason_zh": item.get("model_disagreement_reason_zh", ""),
        "model_disagreement_penalty": item.get("model_disagreement_penalty"),
        "model_market_gap": _signed_pct(item.get("model_market_gap")),
        "raw_model_prob": _pct(item.get("raw_model_prob")),
        "raw_ev": _signed_pct(item.get("raw_ev")),
        "raw_edge": _signed_pct(item.get("raw_edge")),
        "probability_shrinkage_reason_zh": item.get("probability_shrinkage_reason_zh", ""),
        "probability_shrinkage_weight": _pct(item.get("probability_shrinkage_weight")),
        "market_benchmark_discipline_zh": ((item.get("probability_shrinkage") or {}).get("market_benchmark_discipline") or {}).get("message_zh", ""),
        "probability_interval": _probability_interval(item),
        "robust_edge": _signed_pct(item.get("robust_edge")),
        "robust_ev": _signed_pct(item.get("robust_ev")),
        "robust_value_label_zh": item.get("robust_value_label_zh", ""),
        "robust_value_reason_zh": item.get("robust_value_reason_zh", ""),
        "short_cycle_reason_zh": item.get("short_cycle_reason_zh", ""),
        "short_cycle_score_adjustment": item.get("short_cycle_score_adjustment", ""),
        "competition_segment_zh": item.get("competition_segment_zh", ""),
        "competition_segment_reason_zh": item.get("competition_segment_reason_zh", ""),
        "ai_factor_zh": item.get("ai_factor_zh", ""),
        "ai_factor_reason_zh": item.get("ai_factor_reason_zh", ""),
        "market_audit_zh": market_audit.get("summary_zh", ""),
        "market_bias_zh": market_audit.get("bias_zh", ""),
        "market_method_shift_zh": market_audit.get("method_shift_zh", ""),
        "market_audit_status_zh": market_audit.get("status_zh", ""),
        "market_audit_warning_zh": market_audit.get("warning_zh", ""),
        "credibility_gate_zh": gate_label,
        "missing_signals_zh": missing_information,
        "discipline_summary_zh": "；".join([bit for bit in discipline_bits if bit]),
        "best_parlay_final_status": (item.get("best_parlay_quality") or {}).get("final_status", ""),
        "longshot_warning": item.get("longshot_warning", ""),
        "parlay_eligible": item.get("parlay_eligible", True),
    }


def _rejected_row(item: dict) -> dict:
    return {
        "type": _type_label(item.get("type")),
        "match": item.get("match", ""),
        "ev": _signed_pct(item.get("ev")),
        "edge": _signed_pct(item.get("edge")),
        "risk_level": item.get("risk_level", ""),
        "paper_stake": _rmb(item.get("paper_stake")),
        "reason": item.get("reason", "候选待复核"),
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
                "final_status": (item.get("best_parlay_quality") or {}).get("final_status", ""),
                "reason": item.get("selected_reason_zh") or item.get("reject_reason") or "",
                "opposing_factors": item.get("opposing_factors_zh", ""),
            }
        )
    return rows


def _market_audit_summary(item: dict) -> dict:
    if item.get("legs"):
        return _combo_market_audit_summary(item.get("legs") or [])
    audit = item.get("market_probability_audit") or {}
    bias = item.get("market_bias_audit") or {}
    if not audit and not bias:
        return {}
    shift = _float_or_none(bias.get("outcome_method_shift") if bias.get("outcome_method_shift") is not None else audit.get("max_method_shift"))
    bias_bucket = str(bias.get("outcome_bias_bucket") or "")
    status = str(audit.get("label_zh") or audit.get("status") or "市场审计")
    bias_label = str(bias.get("label_zh") or bias.get("status") or "")
    warning = str(bias.get("outcome_message_zh") or bias.get("message_zh") or audit.get("message_zh") or "")
    summary = f"{status}"
    if bias_label:
        summary += f"；{bias_label}"
    if shift is not None:
        summary += f"；方法分歧 {shift:.1%}"
    return {
        "status_zh": status,
        "bias_zh": _bias_bucket_zh(bias_bucket, bias_label),
        "method_shift_zh": f"{shift:.1%}" if shift is not None else "",
        "summary_zh": summary,
        "warning_zh": warning,
    }


def _combo_market_audit_summary(legs: list[dict]) -> dict:
    summaries = [_market_audit_summary(leg) for leg in legs if isinstance(leg, dict)]
    summaries = [row for row in summaries if row.get("summary_zh")]
    if not summaries:
        return {}
    shifts = [_float_or_none((row.get("method_shift_zh") or "").replace("%", "")) for row in summaries]
    shifts = [value / 100.0 for value in shifts if value is not None and value > 1]
    longshot_count = len([row for row in summaries if "冷门" in row.get("bias_zh", "") or "低概率" in row.get("warning_zh", "")])
    unstable_count = len([row for row in summaries if "不稳定" in row.get("summary_zh", "") or "分歧" in row.get("warning_zh", "")])
    weakest = next((row for row in summaries if "冷门" in row.get("bias_zh", "") or "不稳定" in row.get("summary_zh", "")), summaries[0])
    summary = f"组合腿赔率审计：{len(summaries)} 腿已检查"
    if longshot_count:
        summary += f"，{longshot_count} 腿有冷门偏差风险"
    if unstable_count:
        summary += f"，{unstable_count} 腿方法分歧偏高"
    return {
        "status_zh": "组合市场审计",
        "bias_zh": weakest.get("bias_zh", ""),
        "method_shift_zh": weakest.get("method_shift_zh", ""),
        "summary_zh": summary,
        "warning_zh": weakest.get("warning_zh", ""),
    }


def _bias_bucket_zh(bucket: str, fallback: str = "") -> str:
    return {
        "favorite": "热门方向",
        "middle": "中间概率方向",
        "longshot": "冷门偏差风险",
    }.get(bucket, fallback)


def _clv_view(clv: dict) -> dict:
    rows = []
    for row in clv.get("rows", []) or []:
        rows.append(
            {
                "match": row.get("match", ""),
                "direction": row.get("direction", ""),
                "entry_odds": _num(row.get("entry_odds")),
                "closing_odds": _num(row.get("closing_odds")),
                "status": row.get("label_zh") or row.get("status", ""),
                "clv": _signed_pct(row.get("clv_pct")),
                "message": row.get("message_zh", ""),
            }
        )
    return {
        "summary_cards": [
            {"label": "CLV 跟踪项", "value": clv.get("tracked_count", 0), "help": "已记录赛前赔率的观察项数量。"},
            {"label": "等待收盘赔率", "value": clv.get("pending_count", 0), "help": "临近开赛或赛后补充收盘赔率后再复盘。"},
            {"label": "平均 CLV", "value": _signed_pct(clv.get("average_clv_pct")), "help": "仅在有收盘赔率后计算。"},
        ],
        "rows": rows,
        "summary_zh": clv.get("summary_zh", "当前暂无 CLV 跟踪。"),
        "disclaimer": clv.get("disclaimer", "CLV 仅用于赛后复盘，不构成投注建议。"),
    }


def _short_candidate(item: dict) -> str:
    if not item or item.get("status") == "empty":
        return "暂无"
    label = item.get("legs") or item.get("match") or "候选"
    status = item.get("status")
    return f"{status} · {label}" if status else str(label)


def _type_label(value) -> str:
    return {"single": "单关", "parlay_2x1": "2串1", "parlay_3x1": "3串1"}.get(str(value), str(value or ""))


def _play_type_label(value) -> str:
    return {
        "had": "胜平负",
        "hhad": "让球胜平负",
        "total_goals": "总进球",
        "correct_score": "比分",
    }.get(str(value or ""), str(value or ""))


def _direction_family_label(item: dict) -> str:
    raw = str(item.get("outcome_key") or item.get("outcome_label") or item.get("direction") or "").lower()
    play = str(item.get("play_type") or "").lower()
    if "handicap_home" in raw or "让胜" in raw or ("home" in raw and play == "hhad"):
        return "主队让球方向"
    if "home" in raw or "主胜" in raw or raw in {"h", "win"}:
        return "主队方向"
    if "handicap_away" in raw or "让负" in raw or ("away" in raw and play == "hhad"):
        return "客队让球方向"
    if "away" in raw or "客胜" in raw or raw in {"a", "lose"}:
        return "客队方向"
    if "handicap_draw" in raw or "让平" in raw or "draw" in raw or "平" in raw or raw in {"d"}:
        return "平局方向"
    if "over" in raw or "大" in raw:
        return "大球方向"
    if "under" in raw or "小" in raw:
        return "小球方向"
    return "待判断方向"


def _credibility_value(credibility: dict) -> str:
    score = credibility.get("credibility_score")
    grade = credibility.get("grade")
    if score is None and not grade:
        return "待评估"
    if score is None:
        return str(grade or "待评估")
    if grade:
        return f"{grade} / {score}"
    return str(score)


def _professional_score_value(score: dict) -> str:
    if not score:
        return "待评估"
    value = score.get("score")
    ceiling = score.get("ceiling_score")
    grade = score.get("grade")
    if value is None:
        return "待评估"
    if ceiling:
        return f"{grade or ''} / {value}，上限 {ceiling}".strip()
    return f"{grade or ''} / {value}".strip()


def _play_type_learning_status_label(status: dict) -> str:
    raw = str((status or {}).get("status") or "unknown")
    count = (status or {}).get("play_type_count")
    label = {
        "loaded": "已读取",
        "provided": "已提供",
        "fallback": "未启用",
        "unknown": "待检查",
    }.get(raw, raw)
    if count is not None and raw in {"loaded", "provided"}:
        return f"{label} {count} 类"
    return label


def _strategy_adjustment_status_label(status: dict) -> str:
    raw = str((status or {}).get("status") or "unknown")
    count = (status or {}).get("adjustment_count")
    label = {
        "loaded": "已接入",
        "provided": "已提供",
        "fallback": "未启用",
        "unknown": "待检查",
    }.get(raw, raw)
    if count is not None and raw in {"loaded", "provided"}:
        return f"{label} {count} 条"
    return label


def _probability_shrinkage_status_label(status: dict) -> str:
    raw = str((status or {}).get("status") or "unknown")
    settled = (status or {}).get("settled_count")
    label = {
        "loaded": "已接入",
        "provided": "已提供",
        "fallback": "未启用",
        "unknown": "待检查",
    }.get(raw, raw)
    if settled is not None and raw in {"loaded", "provided"}:
        return f"{label} {settled} 条"
    return label


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


def _probability_interval(item: dict) -> str:
    lower = _pct(item.get("probability_lower"))
    upper = _pct(item.get("probability_upper"))
    if lower == "N/A" or upper == "N/A":
        return "N/A"
    return f"{lower} - {upper}"


def _float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _filtered_optimizer_warnings(result: dict) -> list[str]:
    raw = list(result.get("warnings", []) or [])
    filtered = []
    for item in raw:
        text = str(item or "").strip()
        if not text:
            continue
        if "sporttery provider failed:" in text and "fallback to mock" in text:
            continue
        filtered.append(text)
    return filtered

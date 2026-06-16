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
    gate = result.get("credibility_gate", {}) or {}
    ai = result.get("ai_combo_research", {}) or {}
    llm = result.get("llm_status", {}) or {}
    ai_status = _ai_research_status(ai, llm)
    trader_review = result.get("trader_review", {}) or {}
    no_combo_reason = result.get("no_combo_reason") or best_parlay.get("no_combo_reason") or gate.get("reason_zh", "")
    missing_information = list(gate.get("missing_information") or result.get("missing_signals") or [])
    combo_gate_summary = f"{gate.get('label_zh') or gate.get('combo_gate') or '待评估'}：{no_combo_reason or gate.get('reason_zh') or '请结合候选与被拒原因复盘。'}"
    ai_status_summary = ai_status.get("summary_zh") or ai.get("display_status_zh") or ai.get("ds_status_zh") or llm.get("status_detail_zh") or llm.get("status_zh") or "待检查"
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
            {"label": "串联纪律", "value": gate.get("label_zh") or "待评估", "help": no_combo_reason or "通过门控后才会进入优秀串联页。"},
            {"label": "AI研究", "value": ai_status.get("label_zh") or ai.get("ds_status_zh") or llm.get("status_zh") or "待检查", "help": ai_status_summary or llm.get("fallback_reason") or "用于解释强观察、被拒原因和赛后学习点。"},
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
        "trader_review": trader_review,
        "no_combo_reason": no_combo_reason,
        "daily_learning_metrics": result.get("daily_learning_metrics", []),
        "window_learning_metrics": result.get("window_learning_metrics", []),
        "latest_daily_summary_zh": result.get("latest_daily_summary_zh", ""),
        "window_learning_summaries_zh": result.get("window_learning_summaries_zh", []),
        "daily_learning_digest": result.get("daily_learning_digest", {}),
        "window_learning_digests": result.get("window_learning_digests", []),
        "explanations": list(result.get("explanations", []) or []),
        "no_2x1_reason": result.get("no_2x1_reason", "当前没有 2串1 入选；请查看候选排行榜和被拒原因。"),
        "warnings": _filtered_optimizer_warnings(result),
        "disclaimer": result.get("disclaimer", "仅供纸面模拟和概率研究，不构成投注建议。"),
    }


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
    return {
        "type": _type_label(item.get("candidate_type")),
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
        "legs": _legs(item) if is_combo else "",
    }


def _ranking_row(item: dict, gate: dict | None = None, missing_information: list[str] | None = None) -> dict:
    gate = gate or {}
    missing_information = [str(x) for x in (missing_information or []) if str(x).strip()]
    selected = bool(item.get("selected")) or str(item.get("status") or "").strip() == "已入选"
    reject_reason = str(item.get("reject_reason") or "").strip()
    decision_reason = str(item.get("decision_reason_zh") or "").strip()
    odds_reading = str(item.get("odds_reading_zh") or "").strip()
    parlay_policy = str(item.get("parlay_policy_zh") or "").strip()
    hit_rate_note = str(item.get("hit_rate_discipline_zh") or "").strip()
    risk_level = str(item.get("risk_level") or "").strip() or "待评估"
    gate_reason = str(gate.get("reason_zh") or "").strip()
    gate_label = str(gate.get("label_zh") or gate.get("combo_gate") or "").strip()
    coverage_line = f"情报缺口：{'、'.join(missing_information[:6])}" if missing_information else ""
    discipline_bits = []
    if selected:
        if decision_reason:
            discipline_bits.append(f"入选原因：{decision_reason}")
        elif odds_reading:
            discipline_bits.append(f"入选原因：{odds_reading}")
    else:
        if reject_reason:
            discipline_bits.append(f"未入选原因：{reject_reason}")
        elif decision_reason:
            discipline_bits.append(f"未入选原因：{decision_reason}")
        if gate_label or gate_reason:
            discipline_bits.append(f"门控：{gate_label or '待评估'}；{gate_reason or '当前仍需结合可信度与风险复核。'}")
    if hit_rate_note:
        discipline_bits.append(f"命中纪律：{hit_rate_note}")
    if parlay_policy:
        discipline_bits.append(f"组合纪律：{parlay_policy}")
    if coverage_line:
        discipline_bits.append(coverage_line)
    discipline_bits.append(f"风险：{risk_level}")
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
        "risk_level": item.get("risk_level", ""),
        "paper_stake": _rmb(item.get("paper_stake")),
        "status": item.get("status", "未入选"),
        "reject_reason": reject_reason,
        "decision_reason_zh": decision_reason,
        "odds_reading_zh": odds_reading,
        "parlay_policy_zh": parlay_policy,
        "hit_rate_discipline_zh": hit_rate_note,
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
                "final_status": (item.get("best_parlay_quality") or {}).get("final_status", ""),
                "reason": item.get("selected_reason_zh") or item.get("reject_reason") or "",
                "opposing_factors": item.get("opposing_factors_zh", ""),
            }
        )
    return rows


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

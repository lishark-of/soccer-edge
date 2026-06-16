from __future__ import annotations

from src.intelligence.fusion import explain_trade_discipline
from src.intelligence.coverage_status import confidence_zh, normalize_coverage_status, status_zh


def build_intelligence_view(preview: dict) -> dict:
    optimizer = preview.get("optimizer", {})
    portfolio = optimizer.get("selected_portfolio", {})
    coverage_table = build_intelligence_coverage_table(preview)
    coverage_notes = ((preview.get("source_coverage") or {}).get("audit_notes_zh") or (preview.get("source_coverage") or {}).get("warnings") or [])
    signal_rows = _signal_status_table(preview)
    critical_gap_list = _critical_gap_list(preview, signal_rows)
    return {
        "title": "赛前情报总览",
        "summary_cards": [
            {"label": "可售比赛数", "value": preview.get("matches_count", 0), "help": "来自 provider=auto 的可售竞彩足球比赛。"},
            {"label": "数据源", "value": preview.get("provider_used", "unknown"), "help": "实际使用的数据源。"},
            {"label": "单关观察", "value": len(portfolio.get("singles", []) or []), "help": "赔率与融合概率形成观察价值的方向。"},
            {"label": "2串1观察", "value": len(portfolio.get("parlay_2x1", []) or []), "help": "组合命中概率会下降，需看风险。"},
            {"label": "缺失情报", "value": len(preview.get("missing_signals", []) or []), "help": "新闻/伤停/天气/首发默认不编造。"},
        ],
        "top_singles": [_obs(row) for row in preview.get("top_single_observations", [])[:8]],
        "top_2x1": [_combo(row) for row in (portfolio.get("parlay_2x1", []) or [])[:5]],
        "top_total_goals": [_obs(row) for row in preview.get("top_total_goals_observations", [])[:5]],
        "top_scores": [_obs(row) for row in preview.get("top_score_observations", [])[:5]],
        "missing_signals": list(preview.get("missing_signals", []) or []),
        "intelligence_completeness": preview.get("intelligence_completeness", {}),
        "reliability_summary": preview.get("reliability_summary", {}),
        "source_coverage_cards": _source_cards(preview),
        "match_coverage_table": _match_coverage_table(preview),
        "intelligence_coverage": coverage_table,
        "coverage_summary_cards": _coverage_summary_cards(signal_rows),
        "coverage_audit_title_zh": "情报覆盖审计",
        "coverage_audit_notes": coverage_notes,
        "external_signals_status": preview.get("external_signals_status", {}) or {},
        "signal_status": signal_rows,
        "critical_gap_list_zh": critical_gap_list,
        "homepage_missing_actions": _homepage_missing_actions(preview),
        "today_focus_summary_zh": _today_focus_summary(preview, critical_gap_list),
        "intelligence_gap_actions": _intelligence_gap_actions(preview),
        "discipline": explain_trade_discipline(preview),
        "warnings": _filtered_user_warnings(preview, coverage_notes),
        "disclaimer": preview.get("disclaimer", "仅用于观察信号、纸面模拟和风险诊断。"),
    }


def _obs(row: dict) -> dict:
    return {
        "match": f"{row.get('match_no','')} {row.get('home_team','')} vs {row.get('away_team','')}",
        "play_type": _play(row.get("play_type")),
        "direction": row.get("direction"),
        "official_odds": _num(row.get("official_odds")),
        "odds_status_zh": row.get("odds_status_zh", "官方赔率已接入" if row.get("official_odds") else "该玩法官方赔率未接入"),
        "market_prob": _pct(row.get("market_prob")),
        "model_prob": _pct(row.get("model_prob")),
        "edge": _signed_pct(row.get("edge")),
        "ev": _signed_pct(row.get("ev")),
        "ev_status_zh": row.get("ev_status_zh", "可计算 EV" if row.get("ev") is not None else "暂不能计算 EV"),
        "break_even_prob": _pct(row.get("break_even_prob")),
        "safety_margin": _signed_pct(row.get("safety_margin")),
        "safety_margin_label_zh": row.get("safety_margin_label_zh", ""),
        "odds_reading_zh": row.get("odds_reading_zh", ""),
        "decision_level": row.get("decision_level", ""),
        "decision_label_zh": row.get("decision_label_zh", ""),
        "decision_action_zh": row.get("decision_action_zh", ""),
        "decision_reason_zh": row.get("decision_reason_zh", ""),
        "parlay_policy_zh": row.get("parlay_policy_zh", ""),
        "calibrated_prob": _pct(row.get("calibrated_prob")),
        "calibrated_ev": _signed_pct(row.get("calibrated_ev")),
        "signal_category_zh": row.get("signal_category_zh", ""),
        "recommended_use_zh": row.get("recommended_use_zh", ""),
        "odds_bucket_zh": row.get("odds_bucket_zh", ""),
        "calibration_message_zh": row.get("calibration_message_zh", ""),
        "probability_bin": row.get("probability_bin", ""),
        "probability_bin_weight": row.get("probability_bin_weight"),
        "probability_bin_message_zh": row.get("probability_bin_message_zh", ""),
        "odds_coach_verdict_zh": row.get("odds_coach_verdict_zh", ""),
        "ml_learning_note_zh": row.get("ml_learning_note_zh", ""),
        "next_review_zh": row.get("next_review_zh", ""),
        "user_priority_zh": row.get("user_priority_zh", ""),
        "learning_scores": row.get("learning_scores", {}),
        "learning_score_summary_zh": row.get("learning_score_summary_zh", ""),
        "matchday_review_zh": (row.get("matchday_review") or {}).get("message_zh", ""),
        "matchday_keep_min_odds": _num((row.get("matchday_review") or {}).get("keep_min_odds")),
        "matchday_no_value_below_odds": _num((row.get("matchday_review") or {}).get("no_value_below_odds")),
        "matchday_reverse_drift_watch_odds": _num((row.get("matchday_review") or {}).get("reverse_drift_watch_odds")),
        "confidence_score": _pct(row.get("confidence_score")),
        "observation_confidence": _pct(row.get("observation_confidence")),
        "confidence_label_zh": row.get("confidence_label_zh", ""),
        "reliability_label_zh": row.get("reliability_label_zh", row.get("confidence_label_zh", "")),
        "recommended_action_zh": row.get("recommended_action_zh", ""),
        "reliability_explanation_zh": row.get("reliability_explanation_zh", ""),
        "usage_zh": row.get("usage_zh", ""),
        "why_zh": row.get("why_zh", ""),
        "risk_level": row.get("risk_level"),
        "supporting_factors": row.get("support_summary_zh") or "；".join(row.get("supporting_factors", [])),
        "opposing_factors": row.get("opposition_summary_zh") or "；".join(row.get("opposing_factors", [])),
        "missing_signals": "、".join(row.get("missing_signals", [])),
        "selection_reason": row.get("selection_reason"),
        "longshot_warning": row.get("longshot_warning") or _longshot_warning(row.get("official_odds")),
    }


def _combo(row: dict) -> dict:
    legs = row.get("legs", []) or []
    value = _combo_value_fields(row)
    return {
        "type": row.get("candidate_type"),
        "legs": "；".join(_leg_label(leg) for leg in legs),
        "odds": _num(row.get("combo_odds")),
        "model_prob": _pct(row.get("combo_prob")),
        "market_prob": _pct(row.get("market_prob")),
        "ev": _signed_pct(row.get("ev")),
        **value,
        "risk_level": row.get("risk_level"),
        "paper_stake": _rmb(row.get("suggested_paper_stake")),
    }


def _combo_value_fields(row: dict) -> dict:
    odds = _float(row.get("combo_odds") or row.get("odds"))
    prob = _float(row.get("combo_prob") or row.get("model_prob"))
    if odds is None or odds <= 1 or prob is None:
        return {
            "break_even_prob": "N/A",
            "safety_margin": "N/A",
            "combo_decision_label_zh": "等待赔率",
            "combo_action_zh": "组合缺少有效赔率或概率，先不做价值判断。",
            "combo_value_reading_zh": "组合需要赔率、概率和相关性折扣后才能判断。",
            "combo_parlay_policy_zh": "不进入串联。",
        }
    break_even = 1.0 / odds
    margin = prob - break_even
    if margin < 0:
        label = "未覆盖赔率"
        action = "暂不组合。"
        policy = "组合概率低于盈亏线，不进入串联。"
    elif prob < 0.20:
        label = "命中率偏低"
        action = "只作风险观察，不作为优先组合。"
        policy = "组合命中概率低于 20%，不适合作为核心串联。"
    elif margin >= 0.05:
        label = "组合余量尚可"
        action = "可进入候选池，但还要看可信度门控和每腿质量。"
        policy = "仅作为纸面组合候选，需继续复核情报和终盘赔率。"
    else:
        label = "组合余量偏薄"
        action = "等待赔率或情报补强。"
        policy = "一般不进入串联。"
    return {
        "break_even_prob": _pct(break_even),
        "safety_margin": _signed_pct(margin),
        "combo_decision_label_zh": label,
        "combo_action_zh": action,
        "combo_value_reading_zh": f"组合赔率 {odds:.2f} 至少需要 {break_even:.1%} 同时命中；模型扣相关性后约 {prob:.1%}，安全边际 {margin:+.1%}。",
        "combo_parlay_policy_zh": policy,
    }


def _signal_status_table(preview: dict) -> list[dict]:
    contexts = preview.get("contexts") or []
    external_status = preview.get("external_signals_status", {}) or {}
    signal_names = ["news", "injuries", "lineup", "weather", "motivation", "schedule", "travel"]
    labels = {
        "news": "新闻",
        "injuries": "伤停",
        "lineup": "首发",
        "weather": "天气",
        "motivation": "战意",
        "schedule": "赛程",
        "travel": "旅行",
    }
    rows = []
    for name in signal_names:
        signals = []
        for context in contexts:
            signal = (context.get("signals") or {}).get(name)
            if isinstance(signal, dict):
                signals.append(signal)
        confirmed = [item for item in signals if normalize_coverage_status(item.get("status")) in {"confirmed", "user_supplied"} or item.get("status") == "connected"]
        partial = [item for item in signals if item.get("status") == "basic_only" or normalize_coverage_status(item.get("raw_status")) in {"checked_empty", "fallback_estimated"}]
        status = "confirmed" if confirmed else "checked_empty" if partial else "not_connected"
        if confirmed:
            message = "已有可用结构化覆盖记录，仅用于解释信心。"
            source = "用户 JSON" if external_status.get("source_type") == "user_json" else "外部结构化输入"
        elif partial:
            message = "已检查但未返回完整信息，或仅有兜底估算。"
            source = "自动覆盖审计"
        else:
            message = "未接入可靠数据，模型不会编造该情报。"
            source = "未接入"
        rows.append(
            {
                "signal": labels.get(name, name),
                "key": name,
                "status_raw": status,
                "status": status_zh(status),
                "confidence_zh": confidence_zh(status),
                "impact": "已知" if confirmed else "未知",
                "coverage": f"{len(confirmed) + len(partial)}/{len(contexts)}",
                "source_zh": source,
                "message_zh": message,
            }
        )
    return rows


def _source_cards(preview: dict) -> list[dict]:
    return [
        {
            "source": row.get("source"),
            "role": row.get("label_zh"),
            "status": status_zh(row.get("status")),
            "coverage": row.get("coverage"),
            "score": row.get("score"),
            "message_zh": row.get("message_zh"),
        }
        for row in ((preview.get("source_coverage") or {}).get("source_cards") or [])
    ]


def _coverage_summary_cards(signal_rows: list[dict]) -> list[dict]:
    return [
        {
            "label": row.get("signal"),
            "value": row.get("status"),
            "help": row.get("message_zh") or row.get("source_zh") or "",
        }
        for row in signal_rows
        if row.get("key") in {"injuries", "lineup", "weather", "news"}
    ][:4]


def _match_coverage_table(preview: dict) -> list[dict]:
    rows = []
    for row in ((preview.get("source_coverage") or {}).get("match_coverage") or []):
        rows.append(
            {
                "match": row.get("match"),
                "api_football": _coverage_cell(row.get("api_football") or {}),
                "the_odds_api": _coverage_cell(row.get("the_odds_api") or {}),
                "injuries": _coverage_cell(row.get("injuries") or {}),
                "lineup": _coverage_cell(row.get("lineup") or {}),
                "weather": _coverage_cell(row.get("weather") or {}),
                "news": _coverage_cell(row.get("news") or {}),
                "match_confidence": _pct((row.get("identity") or {}).get("match_confidence")),
                "message_zh": row.get("message_zh"),
            }
        )
    return rows


def _critical_gap_list(preview: dict, signal_rows: list[dict]) -> list[str]:
    lines = []
    for row in signal_rows:
        status = str(row.get("status_raw") or "")
        signal = str(row.get("signal") or "")
        if status in {"confirmed", "user_supplied"}:
            continue
        if status == "checked_empty":
            lines.append(f"{signal}：已检查但未返回，今天不能把它当作“没有影响”。")
        elif status == "fallback_estimated":
            lines.append(f"{signal}：当前是兜底估算，只能弱参考，不宜放大到组合核心。")
        elif status == "error":
            lines.append(f"{signal}：查询失败，今天按未知处理，可信度会下降。")
        else:
            lines.append(f"{signal}：当前未接入可靠来源，今天会按未知降权。")
    if not lines:
        missing = list(preview.get("missing_signals", []) or [])
        lines = [f"{item}：当前未接入，今天按未知处理。" for item in missing[:4]]
    return lines[:4]


def _homepage_missing_actions(preview: dict) -> list[str]:
    rows = _intelligence_gap_actions(preview)
    bullets = []
    for row in rows[:4]:
        bullets.append(f"补 {row.get('signal')}：{row.get('next_action_zh')}")
    return bullets


def _today_focus_summary(preview: dict, critical_gap_list: list[str]) -> str:
    top_single_count = len(preview.get("top_single_observations", []) or [])
    gate = (preview.get("credibility_gate") or {}).get("combo_gate")
    if gate == "closed":
        return "今天先看 Top 单关和总进球方向，串联先不升级为最终观察。"
    if top_single_count <= 0:
        return "今天先看数据源和缺口，再决定是否值得继续观察。"
    if critical_gap_list:
        return "今天有可跟踪的 Top 信号，但先补关键信息，再决定是否保留组合。"
    return "今天可以先看 Top 单关，再根据纪律门控决定是否保留组合观察。"


def _status_zh(status: str | None) -> str:
    return status_zh(status)


def build_intelligence_coverage_table(preview: dict) -> dict:
    rows = []
    for match in ((preview.get("source_coverage") or {}).get("match_coverage") or []):
        for key, label in [("injuries", "伤停"), ("lineup", "首发"), ("weather", "天气"), ("news", "新闻")]:
            signal = match.get(key) or {}
            status = normalize_coverage_status(signal.get("status"))
            rows.append(
                {
                    "match": match.get("match"),
                    "key": key,
                    "item": label,
                    "status": status,
                    "status_zh": status_zh(status),
                    "source": signal.get("source_zh") or _coverage_source(key, status),
                    "confidence": confidence_zh(status, fallback_source=signal.get("city_source")),
                    "message_zh": signal.get("message_zh") or signal.get("label_zh") or status_zh(status),
                    "explanation_zh": _coverage_explanation(label, status, signal),
                }
            )
    by_status = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    return {
        "title": "情报覆盖状态",
        "rows": rows,
        "by_status": by_status,
        "summary_zh": _coverage_summary_zh(by_status),
        "complex_intelligence_note_zh": "战意、中立场影响、国家队阵容完整度、教练轮换、旅行疲劳、更衣室状态和赛事重要性属于复杂情报；未确认时系统会降低可信度，不会编造。",
    }


def _coverage_summary_zh(by_status: dict) -> str:
    ordered = [
        ("confirmed", "已确认"),
        ("checked_empty", "已检查但未返回"),
        ("fallback_estimated", "兜底估算"),
        ("not_connected", "未接入"),
        ("user_supplied", "用户补充"),
        ("unknown", "未知"),
        ("error", "查询失败"),
    ]
    parts = [f"{label} {by_status.get(key, 0)}" for key, label in ordered if by_status.get(key, 0)]
    return "；".join(parts) if parts else "当前暂无情报覆盖记录。"


def _filtered_user_warnings(preview: dict, coverage_notes: list[str]) -> list[str]:
    preview_warnings = list(preview.get("warnings", []) or [])
    normalized_notes = {str(item).strip() for item in coverage_notes if str(item).strip()}
    return [item for item in preview_warnings if str(item).strip() and str(item).strip() not in normalized_notes]


def _coverage_source(key: str, status: str) -> str:
    if key in {"injuries", "lineup"}:
        return "API-Football"
    if key == "weather":
        return "Open-Meteo"
    if key == "news":
        return "GDELT"
    return "自动覆盖审计"


def _coverage_cell(signal: dict) -> str:
    status = normalize_coverage_status(signal.get("status"))
    label = signal.get("status_zh") or signal.get("label_zh") or status_zh(status)
    confidence = signal.get("confidence_zh") or confidence_zh(status, fallback_source=signal.get("city_source"))
    if confidence and confidence != "未知":
        return f"{label} · {confidence}"
    return str(label)


def _coverage_explanation(label: str, status: str, signal: dict) -> str:
    if status == "confirmed":
        return f"{label}已有可核实来源，可参与可信度判断。"
    if status == "user_supplied":
        return f"{label}来自用户补充，本地可读，但仍建议保留来源说明。"
    if status == "checked_empty":
        return f"{label}已检查但未返回，不等于确认没有该信息。"
    if status == "fallback_estimated":
        return f"{label}当前是兜底估算，只能弱参考。"
    if status == "error":
        return f"{label}查询失败，当前按未知处理。"
    message = signal.get("message_zh")
    if message:
        return str(message)
    return f"{label}当前未接入，系统不会编造。"


def _leg_label(row: dict) -> str:
    teams = f"{row.get('home_team', '')} vs {row.get('away_team', '')}".strip()
    play = _play(row.get("play_type"))
    direction = str(row.get("outcome_label") or row.get("direction") or "").strip()
    suffix = "·".join(part for part in [play, direction] if part)
    return f"{teams}｜{suffix}".strip("｜")


def _intelligence_gap_actions(preview: dict) -> list[dict]:
    rows = []
    suggestions = {
        "news": {
            "signal": "新闻",
            "why_it_matters": "重大新闻会影响赛前信心，但未接入时不能臆造。",
            "suggested_input": "external_signals JSON 中补充 news 数组，写明来源与摘要。",
        },
        "injuries": {
            "signal": "伤停",
            "why_it_matters": "关键球员缺阵会影响进攻/防守强度。",
            "suggested_input": "external_signals JSON 中补充 injuries 列表。",
        },
        "lineup": {
            "signal": "首发",
            "why_it_matters": "赛前首发能确认轮换和阵容强度。",
            "suggested_input": "external_signals JSON 中补充 lineup.home / lineup.away。",
        },
        "weather": {
            "signal": "天气",
            "why_it_matters": "大雨、大风等可能压低节奏和进球数。",
            "suggested_input": "external_signals JSON 中补充 weather 对象。",
        },
        "motivation": {
            "signal": "战意",
            "why_it_matters": "友谊赛、杯赛、轮换场景会影响模型信心。",
            "suggested_input": "external_signals JSON 中补充 motivation 文本。",
        },
        "travel": {
            "signal": "旅行",
            "why_it_matters": "长途旅行和中立场会影响体能判断。",
            "suggested_input": "本阶段不自动估算旅行距离；可在 external_signals JSON 中补充 travel_note。",
        },
        "schedule": {
            "signal": "赛程",
            "why_it_matters": "休息天数和密集赛程会影响体能。",
            "suggested_input": "系统已读取基础开赛时间；更细赛程可通过 external_signals JSON 补充。",
        },
    }
    status_by_key = {row.get("key"): row for row in _signal_status_table(preview)}
    for key, item in suggestions.items():
        status_row = status_by_key.get(key, {})
        status = status_row.get("status_raw", "not_connected")
        if status in {"connected", "confirmed", "user_supplied"}:
            confidence_impact = "已有覆盖记录，仅用于解释信心，不直接替代概率模型。"
            next_action = "继续核对来源可靠性。"
        elif status in {"basic_only", "checked_empty", "fallback_estimated"}:
            confidence_impact = "已有检查或兜底估算，但仍有关键细节 unknown。"
            next_action = "如有可靠结构化信息，可补充 external_signals JSON。"
        else:
            confidence_impact = "降低信心；系统不会编造该情报，也不会因此给出确定性结论。"
            next_action = item["suggested_input"]
        rows.append(
            {
                "signal": item["signal"],
                "json_key": key,
                "status": _status_zh(status),
                "confidence_impact": confidence_impact,
                "why_it_matters": item["why_it_matters"],
                "next_action_zh": next_action,
                "app_behavior": "缺失时显示 unknown，并在候选观察中降低解释信心。",
            }
        )
    return rows


def _play(value: str | None) -> str:
    return {"had": "胜平负", "hhad": "让球胜平负", "total_goals": "总进球", "correct_score": "比分"}.get(str(value), str(value or ""))


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


def _longshot_warning(odds) -> str:
    try:
        return "这是高赔率冷门观察，不是稳健信号；不适合作为串联核心。" if float(odds) >= 6 else ""
    except (TypeError, ValueError):
        return ""


def _rmb(value) -> str:
    try:
        return f"¥{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"

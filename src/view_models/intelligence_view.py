from __future__ import annotations

from src.intelligence.fusion import explain_trade_discipline


def build_intelligence_view(preview: dict) -> dict:
    optimizer = preview.get("optimizer", {})
    portfolio = optimizer.get("selected_portfolio", {})
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
        "external_signals_status": preview.get("external_signals_status", {}) or {},
        "signal_status": _signal_status_table(preview),
        "intelligence_gap_actions": _intelligence_gap_actions(preview),
        "discipline": explain_trade_discipline(preview),
        "warnings": list(preview.get("warnings", []) or []),
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
    }


def _combo(row: dict) -> dict:
    legs = row.get("legs", []) or []
    return {
        "type": row.get("candidate_type"),
        "legs": "；".join(_leg_label(leg) for leg in legs),
        "odds": _num(row.get("combo_odds")),
        "model_prob": _pct(row.get("combo_prob")),
        "market_prob": _pct(row.get("market_prob")),
        "ev": _signed_pct(row.get("ev")),
        "risk_level": row.get("risk_level"),
        "paper_stake": _rmb(row.get("suggested_paper_stake")),
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
        connected = [item for item in signals if item.get("status") == "connected"]
        basic_only = [item for item in signals if item.get("status") == "basic_only"]
        status = "connected" if connected else "basic_only" if basic_only else "not_connected"
        if connected:
            message = "已有外部结构化输入，仅用于解释信心。"
            source = "用户 JSON" if external_status.get("source_type") == "user_json" else "外部结构化输入"
        elif basic_only:
            message = "只有开赛时间等基础信息，休息天数或旅行距离仍为 unknown。"
            source = "基础赛程"
        else:
            message = "未接入可靠数据，模型不会编造该情报。"
            source = "未接入"
        rows.append(
            {
                "signal": labels.get(name, name),
                "key": name,
                "status_raw": status,
                "status": _status_zh(status),
                "impact": "已知" if connected else "未知",
                "coverage": f"{len(connected) + len(basic_only)}/{len(contexts)}",
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
            "status": _status_zh(row.get("status")),
            "coverage": row.get("coverage"),
            "score": row.get("score"),
            "message_zh": row.get("message_zh"),
        }
        for row in ((preview.get("source_coverage") or {}).get("source_cards") or [])
    ]


def _match_coverage_table(preview: dict) -> list[dict]:
    rows = []
    for row in ((preview.get("source_coverage") or {}).get("match_coverage") or []):
        rows.append(
            {
                "match": row.get("match"),
                "api_football": (row.get("api_football") or {}).get("label_zh"),
                "the_odds_api": (row.get("the_odds_api") or {}).get("label_zh"),
                "injuries": (row.get("injuries") or {}).get("label_zh"),
                "lineup": (row.get("lineup") or {}).get("label_zh"),
                "weather": (row.get("weather") or {}).get("label_zh"),
                "news": (row.get("news") or {}).get("label_zh"),
                "match_confidence": _pct((row.get("identity") or {}).get("match_confidence")),
                "message_zh": row.get("message_zh"),
            }
        )
    return rows


def _status_zh(status: str | None) -> str:
    return {
        "connected": "已接入",
        "matched": "已匹配",
        "ok": "可用",
        "available": "可用",
        "not_connected": "未接入",
        "not_configured": "未配置",
        "basic_only": "基础信息",
        "covered_empty": "已检查无公开条目",
        "not_available": "未公布/未覆盖",
        "not_found": "未发现",
        "timeout": "暂未返回",
        "unmatched": "未匹配",
        "missing": "缺失",
        "empty": "空结果",
        "error": "异常",
    }.get(str(status), str(status or "未知"))


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
        if status == "connected":
            confidence_impact = "已接入，仅用于解释信心，不直接替代概率模型。"
            next_action = "继续核对来源可靠性。"
        elif status == "basic_only":
            confidence_impact = "已有基础信息，但仍有关键细节 unknown。"
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


def _rmb(value) -> str:
    try:
        return f"¥{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"

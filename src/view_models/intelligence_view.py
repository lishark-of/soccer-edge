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
        "external_signals_status": preview.get("external_signals_status", {}) or {},
        "signal_status": _signal_status_table(preview),
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
        "market_prob": _pct(row.get("market_prob")),
        "model_prob": _pct(row.get("model_prob")),
        "edge": _signed_pct(row.get("edge")),
        "ev": _signed_pct(row.get("ev")),
        "confidence_score": _pct(row.get("confidence_score")),
        "risk_level": row.get("risk_level"),
        "supporting_factors": "；".join(row.get("supporting_factors", [])),
        "opposing_factors": "；".join(row.get("opposing_factors", [])),
        "missing_signals": "、".join(row.get("missing_signals", [])),
        "selection_reason": row.get("selection_reason"),
    }


def _combo(row: dict) -> dict:
    legs = row.get("legs", []) or []
    return {
        "type": row.get("candidate_type"),
        "legs": "；".join(f"{leg.get('home_team')} vs {leg.get('away_team')} {leg.get('outcome_label')}" for leg in legs),
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
                "status": status,
                "impact": "known" if connected else "unknown",
                "coverage": f"{len(connected) + len(basic_only)}/{len(contexts)}",
                "source_zh": source,
                "message_zh": message,
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

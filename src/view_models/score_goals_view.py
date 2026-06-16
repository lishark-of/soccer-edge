from __future__ import annotations

from src.view_models.intelligence_view import _obs


def build_score_goals_view(preview: dict) -> dict:
    totals = preview.get("top_total_goals_observations", []) or []
    scores = preview.get("top_score_observations", []) or []
    handicap = [row for row in preview.get("top_single_observations", []) or [] if row.get("play_type") == "hhad"]
    if not handicap:
        handicap = _handicap_rows_from_contexts(preview)
    integrity = _probability_integrity(preview)
    return {
        "title": "比分 / 进球数",
        "selected_date": preview.get("selected_date") or preview.get("date"),
        "provider_used": preview.get("provider_used", "unknown"),
        "summary_cards": [
            {"label": "可售比赛数", "value": preview.get("matches_count", 0), "help": "用于比分和总进球矩阵的比赛数量。"},
            {"label": "总进球观察", "value": len(totals), "help": "由 Poisson/xG 与 Dixon-Coles 矩阵推导。"},
            {"label": "比分 Top 5", "value": len(scores), "help": "只展示模型概率，不代表确定结果。"},
            {"label": "让球观察", "value": len(handicap), "help": "让球胜平负的模型概率、市场概率、Edge 和 EV。"},
            {"label": "矩阵完整性", "value": _integrity_label(integrity), "help": "检查总进球、胜平负和让球概率是否归一化。"},
            {"label": "数据源", "value": preview.get("provider_used", "unknown"), "help": "Sporttery 失败时会清晰标记 fallback。"},
        ],
        "total_goals_table": [_obs(row) for row in totals[:8]],
        "score_table": [_obs(row) for row in scores[:8]],
        "handicap_table": [_obs(row) for row in handicap[:8]],
        "probability_integrity": integrity,
        "risk_notes": [
            "比分和总进球来自概率矩阵，是模型观察项，不是结果承诺。",
            "如果官方赔率未接入，总进球和比分只展示模型概率，暂不计算 EV。",
            "新闻、伤停、首发、天气缺失时，信心分会被下调。",
        ],
        "reliability_notes": _reliability_notes(totals, scores),
        "missing_signals": list(preview.get("missing_signals", []) or []),
        "intelligence_completeness": preview.get("intelligence_completeness", {}),
        "warnings": list(preview.get("warnings", []) or []),
        "disclaimer": preview.get("disclaimer", "仅用于观察信号、纸面模拟和风险诊断。"),
    }



def _handicap_rows_from_contexts(preview: dict) -> list[dict]:
    rows: list[dict] = []
    labels = {"home": "让胜", "draw": "让平", "away": "让负", "win": "让胜", "lose": "让负"}
    for context in preview.get("contexts", []) or []:
        if not isinstance(context, dict):
            continue
        match = context.get("match", {}) or {}
        hhad = (context.get("fused_probability", {}) or {}).get("hhad", {}) or {}
        if not hhad:
            continue
        market = (context.get("market_no_vig", {}) or {}).get("hhad", {}) or {}
        odds = (context.get("sporttery_odds", {}) or {}).get("hhad", {}) or {}
        for key, probability in sorted(hhad.items(), key=lambda item: float(item[1] or 0.0), reverse=True):
            official_odds = _odds_for_key(odds, str(key))
            market_prob = market.get(key)
            ev = None
            edge = None
            if official_odds and market_prob is not None:
                try:
                    ev = float(probability) * float(official_odds) - 1.0
                    edge = float(probability) - float(market_prob)
                except (TypeError, ValueError):
                    ev = None
                    edge = None
            rows.append(
                {
                    "match_no": match.get("match_no") or match.get("match_id") or "",
                    "match_id": match.get("match_id") or match.get("match_no") or "",
                    "league": match.get("league", ""),
                    "home_team": match.get("home_team", ""),
                    "away_team": match.get("away_team", ""),
                    "play_type": "hhad",
                    "direction": labels.get(str(key), str(key)),
                    "official_odds": official_odds,
                    "market_prob": market_prob,
                    "model_prob": round(float(probability or 0.0), 6),
                    "probability": round(float(probability or 0.0), 6),
                    "edge": edge,
                    "ev": ev,
                    "risk_level": "model_only" if official_odds is None else "medium",
                    "odds_status_zh": "官方让球赔率已接入" if official_odds else "官方让球赔率未接入",
                    "ev_status_zh": "可计算 EV" if ev is not None else "暂不能计算 EV",
                    "recommended_action_zh": "先看让球方向概率，若赔率缺失则只作玩法覆盖参考。",
                    "reliability_explanation_zh": "该行由 Poisson/xG + Dixon-Coles 让球概率矩阵生成；赔率缺失时不计算 EV。",
                    "selection_reason": "让球胜平负矩阵覆盖行，非自动强信号。",
                    "missing_signals": context.get("missing_signals", []),
                }
            )
    rows.sort(key=lambda item: float(item.get("model_prob") or 0.0), reverse=True)
    return rows[:8]


def _odds_for_key(odds: dict, key: str):
    aliases = {"home": "win", "away": "lose", "win": "win", "draw": "draw", "lose": "lose"}
    value = odds.get(aliases.get(str(key), str(key))) if isinstance(odds, dict) else None
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

def _reliability_notes(totals: list[dict], scores: list[dict]) -> list[dict]:
    return [
        {
            "type": "总进球",
            "reliability": "中等",
            "usage": "用于观察比赛节奏偏大/偏小。",
            "why": "总进球是区间判断，比精确比分稳定；但缺少首发、伤停、天气时仍需降信心。",
            "top_example": _example(totals),
        },
        {
            "type": "比分",
            "reliability": "偏低",
            "usage": "只作比分倾向参考。",
            "why": "比分是精确事件，波动最大；当前官方比分赔率未接入，EV 暂不能计算。",
            "top_example": _example(scores),
        },
        {
            "type": "让球胜平负",
            "reliability": "中低",
            "usage": "用于补齐玩法覆盖，帮助理解让球方向概率。",
            "why": "让球方向依赖让球盘和球队强弱差；赔率或盘口缺失时只作模型矩阵参考。",
            "top_example": "查看让球胜平负观察表",
        },
    ]


def _example(rows: list[dict]) -> str:
    if not rows:
        return "暂无"
    first = rows[0]
    return f"{first.get('match_no','')} {first.get('home_team','')} vs {first.get('away_team','')} {first.get('direction','')}".strip()


def _probability_integrity(preview: dict) -> list[dict]:
    rows = []
    for context in preview.get("contexts", []) or []:
        if not isinstance(context, dict):
            continue
        match = context.get("match", {}) or {}
        total_goals = context.get("total_goals", {}) or {}
        top_scores = context.get("top_scores", []) or []
        had = (context.get("fused_probability", {}) or {}).get("had", {}) or {}
        hhad = (context.get("fused_probability", {}) or {}).get("hhad", {}) or {}
        rows.append(
            {
                "match": f"{match.get('match_no','')} {match.get('home_team','')} vs {match.get('away_team','')}".strip(),
                "total_goals_sum": _num(sum(float(value or 0.0) for value in total_goals.values())),
                "had_sum": _num(sum(float(value or 0.0) for value in had.values())),
                "hhad_sum": _num(sum(float(value or 0.0) for value in hhad.values())) if hhad else "N/A",
                "top5_score_mass": _pct(sum(float(item.get("probability") or 0.0) for item in top_scores[:5] if isinstance(item, dict))),
                "status": _integrity_status(total_goals, had, hhad),
                "message_zh": "概率矩阵已归一化；Top5 比分仅覆盖部分概率质量。" if _integrity_status(total_goals, had, hhad) == "pass" else "概率矩阵需要检查，可能存在缺失或未归一化。",
            }
        )
    return rows


def _integrity_status(total_goals: dict, had: dict, hhad: dict) -> str:
    checks = [_close_to_one(total_goals), _close_to_one(had)]
    if hhad:
        checks.append(_close_to_one(hhad))
    return "pass" if all(checks) else "warning"


def _close_to_one(values: dict) -> bool:
    try:
        total = sum(float(value or 0.0) for value in values.values())
        return abs(total - 1.0) <= 0.01
    except (TypeError, ValueError):
        return False


def _integrity_label(rows: list[dict]) -> str:
    if not rows:
        return "N/A"
    return "pass" if all(row.get("status") == "pass" for row in rows) else "warning"


def _num(value) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "N/A"


def _pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"

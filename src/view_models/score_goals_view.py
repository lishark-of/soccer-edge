from __future__ import annotations

from src.view_models.intelligence_view import _obs


def build_score_goals_view(preview: dict) -> dict:
    totals = preview.get("top_total_goals_observations", []) or []
    scores = preview.get("top_score_observations", []) or []
    handicap = [row for row in preview.get("top_single_observations", []) or [] if row.get("play_type") == "hhad"]
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
        "missing_signals": list(preview.get("missing_signals", []) or []),
        "warnings": list(preview.get("warnings", []) or []),
        "disclaimer": preview.get("disclaimer", "仅用于观察信号、纸面模拟和风险诊断。"),
    }


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

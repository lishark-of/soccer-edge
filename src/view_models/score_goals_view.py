from __future__ import annotations

from src.view_models.intelligence_view import _obs


def build_score_goals_view(preview: dict) -> dict:
    totals = preview.get("top_total_goals_observations", []) or []
    scores = preview.get("top_score_observations", []) or []
    return {
        "title": "比分 / 进球数",
        "selected_date": preview.get("selected_date") or preview.get("date"),
        "provider_used": preview.get("provider_used", "unknown"),
        "summary_cards": [
            {"label": "可售比赛数", "value": preview.get("matches_count", 0), "help": "用于比分和总进球矩阵的比赛数量。"},
            {"label": "总进球观察", "value": len(totals), "help": "由 Poisson/xG 与 Dixon-Coles 矩阵推导。"},
            {"label": "比分 Top 5", "value": len(scores), "help": "只展示模型概率，不代表确定结果。"},
            {"label": "数据源", "value": preview.get("provider_used", "unknown"), "help": "Sporttery 失败时会清晰标记 fallback。"},
        ],
        "total_goals_table": [_obs(row) for row in totals[:8]],
        "score_table": [_obs(row) for row in scores[:8]],
        "risk_notes": [
            "比分和总进球来自概率矩阵，是模型观察项，不是结果承诺。",
            "如果官方赔率未接入，总进球和比分只展示模型概率，暂不计算 EV。",
            "新闻、伤停、首发、天气缺失时，信心分会被下调。",
        ],
        "missing_signals": list(preview.get("missing_signals", []) or []),
        "warnings": list(preview.get("warnings", []) or []),
        "disclaimer": preview.get("disclaimer", "仅用于观察信号、纸面模拟和风险诊断。"),
    }

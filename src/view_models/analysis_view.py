from __future__ import annotations

from src.explain.local_explainer import explain_candidate, explain_model_components, explain_risk_level
from src.explain.safety import DISCLAIMER_TEXT


def build_analysis_view(analysis: dict) -> dict:
    singles = list(analysis.get("single_candidates", []) or [])
    parlay_2 = list(analysis.get("parlay_2x1_candidates", []) or [])
    parlay_3 = list(analysis.get("parlay_3x1_candidates", []) or [])
    warnings = _warnings(analysis)
    return {
        "title": "指定日期概率分析",
        "summary_cards": [
            {"label": "分析比赛数", "value": analysis.get("matches_analyzed", 0), "help": "当天 provider 返回且完成赔率处理的比赛数量。"},
            {"label": "单关候选", "value": len(singles), "help": "模型视角下形成正期望信号的单场观察项。"},
            {"label": "2串1组合", "value": len(parlay_2), "help": "由多个单场信号组成的模拟组合，风险会放大。"},
            {"label": "数据源", "value": analysis.get("provider_used") or analysis.get("provider") or "unknown", "help": "实际使用的数据 provider。"},
            {"label": "历史数据", "value": analysis.get("historical_data_status", "unknown"), "help": "fixture 表示开发样本，不适合生产推断。"},
            {"label": "校准状态", "value": analysis.get("calibration_status", "not_provided"), "help": "校准 artifact 只是诊断辅助，不保证未来表现。"},
        ],
        "candidate_tables": {
            "single": [_selection_row(item) for item in singles],
            "parlay_2x1": [_parlay_row(item) for item in parlay_2],
            "parlay_3x1": [_parlay_row(item) for item in parlay_3],
        },
        "component_notes": _component_notes(singles),
        "risk_notes": [
            "单场概率只是模型对不确定事件的量化，不代表结果确定。",
            "串关会把多个不确定事件相乘，命中概率通常下降，波动会显著放大。",
        ],
        "excluded_matches": list(analysis.get("excluded_matches", []) or []),
        "warnings": warnings,
        "disclaimer": DISCLAIMER_TEXT,
    }


def _selection_row(item: dict) -> dict:
    row = {
        "match": _match_label(item),
        "league": item.get("league", ""),
        "play_type": item.get("play_type", ""),
        "direction": item.get("outcome_label") or item.get("outcome_key", ""),
        "odds": _round(item.get("odds")),
        "market_probability": _pct_value(item.get("fair_prob")),
        "model_probability": _pct_value(item.get("model_prob")),
        "edge": _signed_pct(item.get("edge")),
        "ev": _signed_pct(item.get("ev")),
        "risk_level": item.get("risk_level", "unknown"),
        "risk_label": _risk_label(item.get("risk_level")),
        "explanation": explain_candidate(item),
        "model_components": item.get("model_components", {}),
    }
    return row


def _parlay_row(item: dict) -> dict:
    legs = list(item.get("legs", []) or [])
    context = {"pass_type": item.get("pass_type")}
    return {
        "pass_type": item.get("pass_type", ""),
        "legs": [_leg_label(leg) for leg in legs],
        "combined_odds": _round(item.get("combined_odds")),
        "hit_probability": _pct_value(item.get("hit_probability")),
        "market_probability": _pct_value(item.get("market_probability")),
        "ev": _signed_pct(item.get("ev")),
        "risk_level": item.get("risk_level", "unknown"),
        "risk_label": _risk_label(item.get("risk_level")),
        "explanation": explain_risk_level(str(item.get("risk_level", "unknown")), context),
        "warnings": list(item.get("warnings", []) or []),
    }


def _component_notes(singles: list[dict]) -> list[str]:
    for item in singles:
        notes = explain_model_components(item.get("model_components", {}))
        if notes:
            return notes
    return ["当前候选较少，暂无可展开的模型组件说明。"]


def _match_label(item: dict) -> str:
    return f"{item.get('home_team', '')} vs {item.get('away_team', '')}".strip()


def _leg_label(leg: dict) -> dict:
    return {
        "match": _match_label(leg),
        "direction": leg.get("outcome_label", ""),
        "odds": _round(leg.get("odds")),
        "model_probability": _pct_value(leg.get("model_prob")),
        "market_probability": _pct_value(leg.get("fair_prob")),
        "risk_label": _risk_label(leg.get("risk_level")),
    }


def _warnings(payload: dict) -> list[str]:
    return list(dict.fromkeys(list(payload.get("warnings", []) or []) + list(payload.get("provider_warnings", []) or [])))


def _risk_label(value) -> str:
    return {"low": "低", "medium": "中", "high": "高", "very_high": "很高"}.get(str(value or "").lower(), "未分级")


def _round(value):
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _pct_value(value):
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _signed_pct(value):
    try:
        return f"{float(value) * 100:+.1f}%"
    except (TypeError, ValueError):
        return "N/A"

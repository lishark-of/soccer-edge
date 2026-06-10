from __future__ import annotations

from src.view_models.intelligence_view import build_intelligence_view


def build_next_available_view(preview: dict) -> dict:
    view = build_intelligence_view(preview)
    status = preview.get("data_source_status", {}) or {}
    view.update(
        {
            "title": "今日观察",
            "selected_date": preview.get("selected_date") or preview.get("date"),
            "provider_used": preview.get("provider_used", "unknown"),
            "matches_count": preview.get("matches_count", 0),
            "data_source_status": status,
            "attempts": preview.get("attempts", []),
            "top_observations": preview.get("top_observations", {}),
            "max_risk_tip": _max_risk_tip(preview),
        }
    )
    return view


def _max_risk_tip(preview: dict) -> str:
    portfolio = (preview.get("optimizer", {}).get("selected_portfolio", {}) or {})
    if portfolio.get("parlay_3x1"):
        return "当前包含 3串1 纸面组合观察，风险最高，请重点查看组合风险。"
    if portfolio.get("parlay_2x1"):
        return "当前包含 2串1 纸面组合观察，串关会放大不确定性。"
    if portfolio.get("singles"):
        return "当前仅有单关观察通过约束，组合观察未通过风险纪律。"
    return "当前没有通过约束的观察信号，严格交易纪律显示无观察价值。"

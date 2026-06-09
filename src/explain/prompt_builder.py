from __future__ import annotations

import json

SYSTEM_PROMPT = """你是足球概率分析解释器。
只解释概率、风险、回测诊断。
不要给出投注指令。
不要承诺命中。
不要使用“必中、稳赢、稳赚、杀庄、保本、回血、倍投、追号”等表达。
必须说明概率模型不保证结果。
必须说明回测不代表未来。
必须说明串关会放大风险。
""".strip()


def build_candidate_explanation_prompt(candidate: dict, context: dict | None = None) -> list[dict]:
    payload = _compact(
        candidate,
        ["league", "home_team", "away_team", "play_type", "outcome_label", "odds", "fair_prob", "model_prob", "edge", "ev", "risk_level"],
    )
    return _messages("请用中文解释这个候选信号的概率、Edge、EV 和风险。", payload, context)


def build_backtest_explanation_prompt(report: dict, context: dict | None = None) -> list[dict]:
    payload = {
        "model_version": report.get("model_version"),
        "matches_total": report.get("matches_total"),
        "matches_evaluated": report.get("matches_evaluated"),
        "bets_total": report.get("bets_total"),
        "metrics": _compact(report.get("metrics", {}) or {}, ["hit_rate", "roi", "pnl", "yield", "average_odds", "max_drawdown", "brier_score", "log_loss", "sample_size"]),
    }
    return _messages("请用中文解释这个回测诊断结果。", payload, context)


def build_calibration_explanation_prompt(calibration: dict, context: dict | None = None) -> list[dict]:
    payload = {"calibration": calibration}
    return _messages("请用中文解释校准分箱反映的概率诊断含义。", payload, context)


def _messages(task: str, payload: dict, context: dict | None) -> list[dict]:
    safe_context = _safe_context(context or {})
    user_payload = {"task": task, "context": safe_context, "data": payload}
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True)},
    ]


def _compact(payload: dict, keys: list[str]) -> dict:
    return {key: payload.get(key) for key in keys if key in payload}


def _safe_context(context: dict) -> dict:
    allowed = ["language", "audience", "provider", "explain_mode"]
    return {key: context.get(key) for key in allowed if key in context}

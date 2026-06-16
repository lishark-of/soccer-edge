from __future__ import annotations

import json

SYSTEM_PROMPT = """你是足球概率分析解释器。
只解释概率、风险、回测诊断。
不要给出投注指令。
不要承诺命中。
不要使用或复述任何禁用词；即使是否定语境也不要写这些词。禁用含义包括：确定命中、稳定获利、追回损失、加倍追单、自动购买、代为购买、真实下单、支付购彩。
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


def build_combo_research_prompt(packet: dict, context: dict | None = None) -> list[dict]:
    if packet.get("coverage_repair_only"):
        return _messages(
            "只输出一段以 STRUCTURED_NOTES_JSON: 开头的 JSON，不要输出其他说明。JSON 只需要包含 match_notes 字段。match_notes 必须逐一覆盖 missing_top_targets，每个元素包含 target、type、role_zh、risk_level、note_zh、usage_zh。不要包含密钥、手机号、账号、个人信息或任何真实执行指令。",
            packet,
            context,
        )
    if packet.get("quality_repair_only"):
        return _messages(
            "只输出一段以 STRUCTURED_NOTES_JSON: 开头的 JSON，不要输出其他说明。目标是提高普通使用者可读性：daily_summary_zh 必须给出一句明确结论；single_notes、combo_notes、total_goals_notes、score_notes、rejected_combo_notes 和 match_notes 尽量覆盖输入里的 Top 项；每个 note_zh 必须说明为什么、可信度短板和下一步观察动作；usage_zh 只能写观察/复核/等待/放弃等研究动作，不要包含任何真实执行指令。JSON 字段必须包含 daily_summary_zh、single_notes、combo_notes、total_goals_notes、score_notes、rejected_combo_notes、match_notes。",
            packet,
            context,
        )
    if packet.get("repair_structured_json_only") or (context or {}).get("repair_structured_json_only"):
        return _messages(
            "只输出一段以 STRUCTURED_NOTES_JSON: 开头的 JSON，不要输出其他说明。JSON 字段必须包含 daily_summary_zh、single_notes、combo_notes、total_goals_notes、score_notes、rejected_combo_notes、match_notes。每个 notes 数组元素使用 target、note_zh、usage_zh；match_notes 额外包含 type、role_zh、risk_level。不要包含密钥、手机号、账号、个人信息或任何真实执行指令。",
            packet,
            context,
        )
    return _messages(
        "请像严厉足球赔率研究员一样，用中文解释今天是否存在强观察组合；如果没有，请明确说明为什么不应强行组合。重点解释赔率覆盖、校准概率、安全边际、串关命中率、缺失情报和赛后学习反馈。不要给出任何真实执行指令。最后必须追加一段以 STRUCTURED_NOTES_JSON: 开头的 JSON，字段包含 daily_summary_zh、single_notes、combo_notes、total_goals_notes、score_notes、rejected_combo_notes、match_notes。每个 notes 数组元素使用 target、note_zh、usage_zh；match_notes 额外包含 type、role_zh、risk_level。JSON 必须是单个对象，不要包含密钥或个人信息。",
        packet,
        context,
    )


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

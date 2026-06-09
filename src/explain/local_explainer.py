from __future__ import annotations

from math import isfinite

from src.explain.safety import DISCLAIMER_TEXT, sanitize_explanation


RISK_LABELS = {
    "low": "低风险",
    "medium": "中等风险",
    "high": "高风险",
    "very_high": "很高风险",
}


def explain_candidate(candidate: dict) -> str:
    edge = _float(candidate.get("edge"))
    ev = _float(candidate.get("ev"))
    model_prob = _float(candidate.get("model_prob", candidate.get("hit_probability")))
    market_prob = _float(candidate.get("fair_prob", candidate.get("market_probability")))
    risk_level = str(candidate.get("risk_level") or "unknown")
    parts = []
    if model_prob is not None and market_prob is not None:
        parts.append(
            f"模型概率约为 {_pct(model_prob)}，市场去水概率约为 {_pct(market_prob)}，两者存在 {_pct((model_prob - market_prob))} 的分歧。"
        )
    if edge is not None:
        parts.append(f"Edge 约为 {_pct(edge)}，表示模型与市场之间的概率差。")
    if ev is not None:
        if ev > 0:
            parts.append(f"EV 约为 {_pct(ev)}，模型视角下存在正期望信号，但这只是数学假设下的研究观察项。")
        else:
            parts.append(f"EV 约为 {_pct(ev)}，当前没有形成正期望信号。")
    parts.append(explain_risk_level(risk_level))
    parts.append("单场结果仍有显著随机性，不能据此推断结果确定。")
    return sanitize_explanation(" ".join(parts))


def explain_backtest_metrics(metrics: dict) -> list[str]:
    notes = []
    roi = _float(metrics.get("roi"))
    hit_rate = _float(metrics.get("hit_rate"))
    brier = _float(metrics.get("brier_score"))
    log_loss = _float(metrics.get("log_loss"))
    drawdown = _float(metrics.get("max_drawdown"))
    if hit_rate is not None:
        notes.append(f"命中率约为 {_pct(hit_rate)}，它只描述历史样本中模拟触发项的结果比例。")
    if roi is not None:
        notes.append(f"ROI 约为 {_pct(roi)}，反映历史样本中的单位投入模拟收益，不代表未来表现。")
    if drawdown is not None:
        notes.append(f"最大回撤约为 {_pct(drawdown)}，用于观察历史资金曲线的低谷风险。")
    if brier is not None:
        notes.append(f"Brier Score 为 {_num(brier)}，越低通常表示概率与真实结果越接近。")
    if log_loss is not None:
        notes.append(f"Log Loss 为 {_num(log_loss)}，会更重地惩罚过度自信且错误的概率。")
    notes.append("回测是诊断工具，不能保证未来样本复现相同表现。")
    return [sanitize_explanation(item) for item in notes]


def explain_risk_level(risk_level: str, context: dict | None = None) -> str:
    label = RISK_LABELS.get(str(risk_level or "").lower(), "未分级风险")
    if str(risk_level).lower() in {"low", "medium"}:
        message = f"风险等级为{label}，表示当前规则下波动相对可控，但并不代表结果更确定。"
    elif str(risk_level).lower() in {"high", "very_high"}:
        message = f"风险等级为{label}，说明赔率、模型分歧或组合相关性带来的不确定性更强。"
    else:
        message = "风险等级暂不明确，需要结合赔率、样本和模型分歧继续观察。"
    if context and context.get("pass_type"):
        message += " 串关会把多个不确定事件相乘，风险会被显著放大。"
    return sanitize_explanation(message)


def explain_model_components(components: dict) -> list[str]:
    if not isinstance(components, dict) or not components:
        return ["当前没有可展开的模型组件信息。"]
    notes = []
    if components.get("market") is not None:
        notes.append("市场组件来自赔率隐含概率并去除水位，是模型的保守锚点。")
    if components.get("poisson") is not None:
        notes.append("Poisson 组件使用进球期望估计比分分布，适合作为基础概率参考。")
    if components.get("elo") is not None:
        notes.append("Elo 组件用历史强弱变化估计胜平负倾向，属于简化基线。")
    weights = components.get("weights")
    if isinstance(weights, dict):
        notes.append("Ensemble 权重用于合成多个概率来源，缺失组件会自动归一化。")
    notes.append("所有组件都是研究基线，不保证单场结果。")
    return [sanitize_explanation(item) for item in notes]


def _float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(number):
        return None
    return number


def _pct(value: float) -> str:
    return f"{value * 100:+.1f}%" if value < 0 else f"{value * 100:.1f}%"


def _num(value: float) -> str:
    return f"{value:.4f}"

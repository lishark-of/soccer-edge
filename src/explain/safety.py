from __future__ import annotations

BANNED_OUTPUT_TERMS = [
    "必中",
    "稳赢",
    "稳赚",
    "杀庄",
    "保本",
    "回血",
    "倍投",
    "追号",
    "自动投注",
    "代下单",
    "支付购彩",
    "保证收益",
    "投注指令",
    "下单",
    "支付",
    "代购",
]
BANNED_EXPLANATION_TERMS = BANNED_OUTPUT_TERMS
OVERCONFIDENT_TERMS = ["必然", "一定", "保证", "确定获利", "确定命中"]

DISCLAIMER_TEXT = "仅供数据研究与娱乐参考。概率模型不保证结果，回测结果不保证未来表现，串关会显著放大风险。"


def sanitize_explanation(text: str) -> str:
    """Remove prohibited certainty/promotional phrasing from generated explanations."""
    cleaned = str(text or "").strip()
    replacements = {
        "值得买": "可作为研究观察项",
        "一定": "可能",
        "确定": "倾向于",
        "稳": "相对平缓",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    for term in BANNED_OUTPUT_TERMS:
        cleaned = cleaned.replace(term, "高风险表述")
    if not cleaned:
        cleaned = "暂无足够信息形成解释。"
    return cleaned


def validate_explanation_safety(text: str) -> list[str]:
    issues: list[str] = []
    content = str(text or "")
    for term in BANNED_OUTPUT_TERMS:
        if term in content:
            issues.append(f"contains banned term: {term}")
    for term in OVERCONFIDENT_TERMS:
        if term in content:
            issues.append(f"contains overconfident term: {term}")
    if "概率模型不保证结果" not in content and "不保证" not in content:
        issues.append("missing uncertainty reminder")
    if "回测" in content and "未来" not in content:
        issues.append("missing backtest future-performance reminder")
    return issues


def enforce_safe_explanation(text: str, fallback: str) -> str:
    issues = validate_explanation_safety(text)
    if issues:
        return sanitize_explanation(fallback)
    return sanitize_explanation(text)

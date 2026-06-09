from __future__ import annotations

BANNED_EXPLANATION_TERMS = [
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
]

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
    for term in BANNED_EXPLANATION_TERMS:
        cleaned = cleaned.replace(term, "高风险表述")
    if not cleaned:
        cleaned = "暂无足够信息形成解释。"
    return cleaned

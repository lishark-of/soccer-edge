from __future__ import annotations


def exposure_warning(total_stake: float, bankroll: float = 1000.0) -> list[str]:
    warnings: list[str] = []
    if bankroll <= 0:
        return ["资金基数无效，无法评估暴露。"]
    ratio = total_stake / bankroll
    if ratio >= 0.08:
        warnings.append("资金暴露偏高，请降低投注额。")
    elif ratio >= 0.04:
        warnings.append("资金暴露中等，请控制仓位。")
    return warnings

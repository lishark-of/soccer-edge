from __future__ import annotations

from src.version import get_build_info, get_version

DISCLAIMER = "仅供数据研究与娱乐参考。概率模型不保证结果。回测结果不保证未来表现。串关会显著放大风险。"


def build_release_metadata() -> dict:
    build = get_build_info()
    return {
        "project": "football-jc-analysis",
        "version": get_version(),
        "release_phase": build["release_phase"],
        "mode": build["mode"],
        "remote": build["remote"],
        "capabilities": [
            "provider fallback",
            "probability analysis",
            "backtesting",
            "import rehearsal",
            "calibration artifact",
            "local API",
            "local dashboard",
            "optional deepseek explainer disabled by default",
            "QA harness",
            "local release validation",
        ],
        "disabled_capabilities": [
            "betting",
            "payment",
            "order placement",
            "proxy purchase",
            "automation",
        ],
        "disclaimer": DISCLAIMER,
    }

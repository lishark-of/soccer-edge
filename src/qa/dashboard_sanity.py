from __future__ import annotations

import re
from pathlib import Path

from src.qa.checks import QaCheckResult


FORBIDDEN_BUTTON_TEXT = [
    "Bet",
    "Buy",
    "Order",
    "Pay",
    "Auto Bet",
    "Follow Bet",
    "Chase",
    "Martingale",
    "Recover Loss",
    "Guaranteed Win",
    "投注",
    "立即购买",
    "下单",
    "支付",
    "代购",
    "跟单",
    "自动投注",
    "追号",
    "倍投",
    "回血",
]


def check_dashboard_static_files(static_dir: str) -> list[QaCheckResult]:
    root = Path(static_dir)
    files = {name: root / name for name in ("index.html", "app.js", "style.css", "components.js", "glossary.js")}
    results = [QaCheckResult(f"dashboard.file.{name}", path.exists(), message=f"{name} exists") for name, path in files.items()]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files.values() if path.exists())
    lower = combined.lower()
    external_patterns = [
        r"<script[^>]+src=[\"']https://",
        r"<link[^>]+href=[\"']https://",
        r"@import\s+url\([\"']?https://",
        r"url\([\"']?https://fonts\.googleapis",
        r"src=[\"'][^\"']*cdn[^\"']*[\"']",
        r"href=[\"'][^\"']*cdn[^\"']*[\"']",
    ]
    external = [pattern for pattern in external_patterns if re.search(pattern, lower)]
    results.append(QaCheckResult("dashboard.external_network", not external, message="dashboard has no external CDN or fonts", details={"matches": external}))
    has_read_only = any(
        marker in combined
        for marker in (
            "Read-only local analysis mode",
            "Read-only local analysis",
            "只读",
            "本工具仅做本地概率分析",
            "不提供投注、下单、支付、代购",
        )
    )
    results.append(QaCheckResult("dashboard.read_only", has_read_only, message="dashboard shows read-only mode"))
    for label in FORBIDDEN_BUTTON_TEXT:
        results.append(
            QaCheckResult(
                f"dashboard.button.{label}",
                f">{label}<" not in combined and f">{label} " not in combined,
                message=f"no {label} button",
            )
        )
    results.append(QaCheckResult("dashboard.api_base", "127.0.0.1:8765" in combined, message="dashboard supports local API base"))
    return results

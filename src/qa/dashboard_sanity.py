from __future__ import annotations

from pathlib import Path

from src.qa.checks import QaCheckResult


FORBIDDEN_BUTTON_TEXT = ["Bet", "Buy", "Order", "Pay", "Auto Bet", "Follow Bet", "Chase", "Martingale", "Recover Loss", "Guaranteed Win"]


def check_dashboard_static_files(static_dir: str) -> list[QaCheckResult]:
    root = Path(static_dir)
    files = {name: root / name for name in ("index.html", "app.js", "style.css")}
    results = [QaCheckResult(f"dashboard.file.{name}", path.exists(), message=f"{name} exists") for name, path in files.items()]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files.values() if path.exists())
    external = [token for token in ("https://", "cdn", "fonts.googleapis") if token in combined.lower()]
    results.append(QaCheckResult("dashboard.external_network", not external, message="dashboard has no external CDN or fonts", details={"matches": external}))
    results.append(QaCheckResult("dashboard.read_only", "Read-only local analysis mode" in combined, message="dashboard shows read-only mode"))
    for label in FORBIDDEN_BUTTON_TEXT:
        results.append(QaCheckResult(f"dashboard.button.{label}", f">{label}<" not in combined, message=f"no {label} button"))
    results.append(QaCheckResult("dashboard.api_base", "127.0.0.1:8765" in combined, message="dashboard supports local API base"))
    return results

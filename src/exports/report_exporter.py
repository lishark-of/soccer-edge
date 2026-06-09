from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


DISCLAIMER = "Backtest results are research diagnostics and do not guarantee future outcomes."


def summarize_report(report: dict) -> dict:
    metrics = report.get("metrics", {})
    data_summary = report.get("data_summary", {})
    return {
        "model_version": report.get("model_version"),
        "date": report.get("date"),
        "matches": report.get("matches_evaluated", report.get("matches_analyzed", data_summary.get("matches"))),
        "bets_total": report.get("bets_total"),
        "roi": metrics.get("roi"),
        "hit_rate": metrics.get("hit_rate"),
        "warnings": list(report.get("warnings", [])),
    }


def export_report_to_markdown(report: dict, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = summarize_report(report)
    lines = [
        "# football-jc-analysis Report",
        "",
        f"Generated: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
        f"Model version: {summary.get('model_version') or 'unknown'}",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        if key != "warnings" and value is not None:
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Data"])
    for key, value in report.get("data_summary", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Metrics"])
    for key, value in report.get("metrics", {}).items():
        if key != "warnings":
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Warnings"])
    warnings = report.get("warnings", []) or ["none"]
    for warning in warnings:
        lines.append(f"- {warning}")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- 仅供数据研究与娱乐参考。",
            "- 概率模型不保证结果。",
            "- 回测结果不保证未来表现。",
            "- 串关会显著放大风险。",
            "- 不提供投注、下单、支付、代购或任何自动化购彩能力。",
            f"- {DISCLAIMER}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)

from __future__ import annotations

import argparse
import json

from src.intelligence.fusion import build_intelligence_preview
from src.view_models.reliability_view import build_reliability_view


def main() -> None:
    parser = argparse.ArgumentParser(description="JC Edge 数据可靠性审计")
    parser.add_argument("--provider", default="auto")
    parser.add_argument("--date", default=None)
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    preview = build_intelligence_preview(args.provider, args.date)
    view = build_reliability_view(preview)
    result = {
        "audit_version": "phase2p_data_reliability_audit_v0",
        "selected_date": view.get("selected_date"),
        "matches_count": view.get("matches_count"),
        "summary_cards": view.get("summary_cards", []),
        "source_cards": view.get("source_cards", []),
        "match_coverage_table": view.get("match_coverage_table", []),
        "decision_guide_zh": view.get("decision_guide_zh"),
        "warnings": view.get("warnings", []),
        "disclaimer": "仅用于数据可靠性审计，不构成投注建议。",
    }
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("JC Edge 数据可靠性审计")
    for card in result["summary_cards"]:
        print(f"{card.get('label')}: {card.get('value')}")
    print(result["decision_guide_zh"])


if __name__ == "__main__":
    main()

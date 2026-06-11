from __future__ import annotations

import argparse
import json
import sys

from src.intelligence.external_signals_loader import preview_external_signals
from src.intelligence.fusion import build_intelligence_preview
from src.intelligence.missing_info import build_missing_info_from_preview


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="预览本地 external_signals JSON 补齐效果，不联网、不写文件。")
    parser.add_argument("--signals", required=True)
    parser.add_argument("--provider", default="auto")
    parser.add_argument("--date")
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--risk-profile", choices=["conservative", "balanced", "aggressive"], default="aggressive")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        preview = preview_external_signals(args.signals, args.date)
        result = build_intelligence_preview(args.provider, args.date, args.signals, bankroll=args.bankroll, risk_profile=args.risk_profile)
        payload = {
            **preview,
            "credibility_gate": result.get("credibility_gate", {}),
            "credibility_audit": result.get("credibility_audit", {}),
            "external_signals_status": result.get("external_signals_status", {}),
            "missing_information_after_preview": build_missing_info_from_preview(result),
            "no_combo_reason": (result.get("optimizer") or {}).get("no_combo_reason", ""),
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            gate = payload.get("credibility_gate", {})
            print(f"情报补齐预览：{payload.get('signals_count', 0)} 场，门控：{gate.get('label_zh', 'unknown')}。")
        return 0
    except Exception as exc:  # noqa: BLE001
        message = f"情报补齐预览失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message, "warnings": ["不会暴露 Python traceback。"]}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

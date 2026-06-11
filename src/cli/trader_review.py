from __future__ import annotations

import argparse
import json
import sys

from src.audit.trader_review import build_trader_review
from src.intelligence.fusion import build_intelligence_preview


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成严厉交易者复盘，只做纸面观察和风险诊断。")
    parser.add_argument("--provider", default="auto")
    parser.add_argument("--date")
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--risk-profile", choices=["conservative", "balanced", "aggressive"], default="aggressive")
    parser.add_argument("--external-signals")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        preview = build_intelligence_preview(args.provider, args.date, args.external_signals, bankroll=args.bankroll, risk_profile=args.risk_profile)
        payload = build_trader_review(preview)
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload.get("final_call_zh"))
        return 0
    except Exception as exc:  # noqa: BLE001
        message = f"严厉交易者复盘失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message, "warnings": ["不会暴露 Python traceback。"]}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

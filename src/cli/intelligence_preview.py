from __future__ import annotations

import argparse
import json
import sys

from src.intelligence.fusion import build_intelligence_preview


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="赛前情报融合预览，只输出观察信号和风险诊断。")
    parser.add_argument("--provider", default="auto")
    parser.add_argument("--date")
    parser.add_argument("--external-signals")
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--risk-profile", choices=["conservative", "balanced", "aggressive"], default="aggressive")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        payload = build_intelligence_preview(args.provider, args.date, args.external_signals, bankroll=args.bankroll, risk_profile=args.risk_profile)
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"赛前情报融合完成：{payload.get('matches_count', 0)} 场，数据源 {payload.get('provider_used')}")
        return 0
    except Exception as exc:
        message = f"赛前情报融合失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

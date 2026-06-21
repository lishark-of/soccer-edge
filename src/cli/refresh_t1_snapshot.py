from __future__ import annotations

import argparse
import json
import sys

from src.learning.daily_snapshots import refresh_t1_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="刷新 T+1 赛前观察快照，只做本地纸面研究。")
    parser.add_argument("--provider", default="auto")
    parser.add_argument("--date")
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--risk-profile", choices=["conservative", "balanced", "aggressive"], default="aggressive")
    parser.add_argument("--external-signals", default=None)
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        payload = refresh_t1_snapshot(
            args.provider,
            args.date,
            bankroll=args.bankroll,
            risk_profile=args.risk_profile,
            external_signals_path=args.external_signals,
        )
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            status = payload.get("snapshot_status", {})
            print(status.get("summary_zh") or payload.get("summary_zh"))
            print(status.get("pre_match_path", ""))
        return 0
    except Exception as exc:
        message = f"T+1 快照刷新失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

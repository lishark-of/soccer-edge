from __future__ import annotations

import argparse
import json
import sys

from src.api.routes import dispatch_route


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="自动生成并保存赛前研究档案。")
    parser.add_argument("--provider", default="auto")
    parser.add_argument("--date")
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--risk-profile", default="aggressive", choices=["conservative", "balanced", "aggressive"])
    parser.add_argument("--external-signals", default=None)
    parser.add_argument("--ai-provider", default="auto")
    parser.add_argument("--run-ai", action="store_true", default=True)
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args(argv)
    query = {
        "provider": args.provider,
        "bankroll": str(args.bankroll),
        "risk_profile": args.risk_profile,
        "ai_provider": args.ai_provider,
        "run_ai": "0" if args.local_only else ("1" if args.run_ai else "0"),
        "refresh": "1",
    }
    if args.date:
        query["date"] = args.date
    if args.external_signals:
        query["external_signals"] = args.external_signals
    try:
        payload = dispatch_route("/api/learning/auto-archive-research", query)
    except Exception as exc:
        message = f"自动研究存档失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        data = payload.get("data", {})
        print(data.get("summary_zh", "已完成。"))
        print(data.get("path", ""))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

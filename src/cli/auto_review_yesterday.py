from __future__ import annotations

import argparse
import json
import sys

from src.learning.daily_snapshots import auto_review_yesterday


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="根据最近赛前快照自动做赛后复盘。")
    parser.add_argument("--date")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        payload = auto_review_yesterday(args.date)
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload.get("summary_zh") or payload.get("status_zh"))
        return 0
    except Exception as exc:
        message = f"昨日自动复盘失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json

from src.learning.data_expansion import build_data_expansion_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="审计本地真实数据拓展覆盖情况。")
    parser.add_argument("--date", default=None, help="目标日期，YYYY-MM-DD。默认今天。")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    payload = build_data_expansion_summary(args.date)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"数据拓展：{payload.get('status_zh')}，评分 {payload.get('coverage_score')}/100")
        for card in payload.get("summary_cards", []):
            print(f"- {card.get('label')}: {card.get('value')} - {card.get('help')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

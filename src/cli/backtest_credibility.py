from __future__ import annotations

import argparse
import json

from src.backtesting.credibility import build_backtest_credibility_report


def main() -> int:
    parser = argparse.ArgumentParser(description="评估用户 CSV / fixture 回测数据可信度。")
    parser.add_argument("--input", required=True, help="历史赛果/赔率 CSV 路径")
    parser.add_argument("--source-type", default="user_csv", help="user_csv / fixture / verified_market")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()
    report = build_backtest_credibility_report(args.input, source_type=args.source_type)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"可信度：{report.get('score')}/100，评级：{report.get('grade')}，等级：{report.get('confidence_level_zh')}")
        for reason in report.get("reasons", []) or []:
            print("- " + reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

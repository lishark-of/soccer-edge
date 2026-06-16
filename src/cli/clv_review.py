from __future__ import annotations

import argparse
import json

from src.market.clv import build_clv_tracking, load_closing_odds_csv, load_observations_json


def main() -> int:
    parser = argparse.ArgumentParser(description="用本地收盘赔率 CSV 复盘 CLV。")
    parser.add_argument("--observations-json", required=True, help="赛前优化 JSON 或观察项 JSON")
    parser.add_argument("--closing-odds", required=True, help="收盘赔率 CSV，需包含 key+closing_odds 或 match/play/direction 字段")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()
    observations = load_observations_json(args.observations_json)
    closing = load_closing_odds_csv(args.closing_odds)
    report = build_clv_tracking(observations, closing)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report.get("summary_zh", "暂无 CLV 复盘。"))
        print(f"tracked={report.get('tracked_count', 0)} settled={report.get('settled_count', 0)} positive={report.get('positive_clv_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

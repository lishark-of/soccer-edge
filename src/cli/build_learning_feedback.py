from __future__ import annotations

import argparse
import json
import sys

from src.learning.feedback_builder import build_feedback_from_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把赛前观察 JSON 和赛果 CSV 匹配成赛后学习反馈。")
    parser.add_argument("--observations-json", required=True, help="赛前观察 JSON，可来自 optimizer 输出或观察项列表")
    parser.add_argument("--results-csv", required=True, help="赛果 CSV，至少包含 home_team/away_team/home_goals/away_goals")
    parser.add_argument("--date", default=None)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args(argv)
    try:
        payload = build_feedback_from_files(args.observations_json, args.results_csv, date=args.date)
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            summary = payload.get("builder_summary", {})
            report = payload.get("report", {})
            print(summary.get("message_zh", "已生成赛后学习反馈。"))
            print(f"匹配观察 {summary.get('matched_observations', 0)}/{summary.get('observations_loaded', 0)}，命中率 {_pct(report.get('hit_rate'))}")
        return 0
    except Exception as exc:
        message = f"生成赛后学习反馈失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message, "warnings": ["不会暴露 Python traceback。"]}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


def _pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


if __name__ == "__main__":
    raise SystemExit(main())

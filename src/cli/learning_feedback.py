from __future__ import annotations

import argparse
import json
import sys

from src.learning.result_feedback import build_feedback_report, load_feedback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="赛后学习复盘：用赛果反馈校准赔率段、冷门和观察信号。")
    parser.add_argument("--feedback", default="data/fixtures/result_feedback_20260611.json", help="赛果反馈 JSON 路径")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args(argv)
    try:
        report = build_feedback_report(load_feedback(args.feedback))
        if args.format == "json":
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"赛后学习：{report.get('date', 'N/A')}")
            print(f"观察 {report.get('observation_count', 0)}，命中 {report.get('hit_count', 0)}，命中率 {_pct(report.get('hit_rate'))}")
            print(report.get("main_lesson_zh", "暂无学习结论。"))
            print(report.get("next_model_action_zh", ""))
        return 0
    except Exception as exc:
        message = f"赛后学习复盘失败：{str(exc).splitlines()[0]}"
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

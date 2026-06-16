from __future__ import annotations

import argparse
import json
import sys

from src.learning.history import build_learning_history


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="累计赛后学习：汇总赔率段、信号类型和命中率。")
    parser.add_argument("--feedback-dir", default="data/learning_feedback")
    parser.add_argument("--no-fixtures", action="store_true", help="不包含项目 fixture 示例")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args(argv)
    try:
        payload = build_learning_history(args.feedback_dir, include_fixtures=not args.no_fixtures)
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"累计学习：文件 {payload.get('files_loaded', 0)}，观察 {payload.get('settled_count', 0)}，命中率 {_pct(payload.get('hit_rate'))}")
            for item in payload.get("lessons", []):
                print("- " + item)
        return 0
    except Exception as exc:
        message = f"累计学习失败：{str(exc).splitlines()[0]}"
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

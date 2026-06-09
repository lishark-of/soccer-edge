from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.qa.runner import run_qa, write_qa_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run football-jc-analysis QA harness")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--rehearsal", action="store_true")
    parser.add_argument("--write-report", default=None)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path.cwd()
    report = run_qa(str(root), rehearsal=args.rehearsal, strict=args.strict)
    if args.write_report:
        try:
            report["report_markdown_path"] = write_qa_markdown(report, args.write_report)
        except Exception as exc:
            report.setdefault("warnings", []).append(f"QA markdown report failed: {str(exc)[:180]}")
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report)
    return 0


def _print_text(report: dict) -> None:
    print(f"QA version: {report.get('qa_version')}")
    print(f"Overall passed: {report.get('overall_passed')}")
    for key, value in report.get("summary", {}).items():
        print(f"{key}: {value}")
    for warning in report.get("warnings", []):
        print(f"- {warning}")


if __name__ == "__main__":
    raise SystemExit(main())

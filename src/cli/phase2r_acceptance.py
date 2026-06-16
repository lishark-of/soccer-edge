from __future__ import annotations

import argparse
import json

from src.acceptance.phase2r import build_phase2r_acceptance_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2-R 本地验收检查。")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()
    report = build_phase2r_acceptance_report()
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Phase 2-R acceptance: {report['passed_count']}/{report['total_count']} passed")
        for check in report["checks"]:
            print(f"- {check['id']}: {'pass' if check['passed'] else 'fail'} - {check['summary_zh']}")
    return 0 if report["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

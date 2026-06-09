from __future__ import annotations

import argparse
import json

from src.ingestion.importer import import_historical_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="竞彩足球历史数据本地导入工具")
    parser.add_argument("--input", required=True)
    parser.add_argument("--adapter", default="auto", choices=["auto", "generic_csv", "sporttery_export", "football_data"])
    parser.add_argument("--mapping", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = import_historical_file(
            input_path=args.input,
            adapter_name=args.adapter,
            mapping_path=args.mapping,
            output_path=args.output,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        payload = {
            "input_path": args.input,
            "adapter": args.adapter,
            "dry_run": args.dry_run,
            "rows_read": 0,
            "rows_normalized": 0,
            "rows_skipped": 0,
            "output_path": None,
            "quality": {},
            "manifest": {},
            "warnings": [f"import failed: {str(exc)[:180]}"],
        }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_text(payload)
    return 0


def _print_text(payload: dict) -> None:
    print(f"adapter: {payload.get('adapter')}")
    print(f"rows: {payload.get('rows_normalized')}/{payload.get('rows_read')} normalized")
    if payload.get("output_path"):
        print(f"output: {payload['output_path']}")
    for warning in payload.get("warnings", []):
        print(f"- {warning}")


if __name__ == "__main__":
    raise SystemExit(main())

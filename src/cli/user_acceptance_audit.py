from __future__ import annotations

import argparse
import json
import sys

from src.audit.user_journey import run_user_acceptance_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="运行 JC Edge 使用者实操验收。")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        payload = run_user_acceptance_audit(".")
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"使用者实操验收：{'通过' if payload.get('overall_passed') else '存在问题'}，可信度 {payload.get('credibility_score')}/100")
        return 0 if payload.get("overall_passed") else 1
    except Exception as exc:  # noqa: BLE001
        message = f"使用者实操验收失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message, "warnings": ["不会暴露 Python traceback。"]}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

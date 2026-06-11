from __future__ import annotations

import argparse
import json

from src.providers.free_data_sources import build_free_data_source_status


def main() -> None:
    parser = argparse.ArgumentParser(description="查看 JC Edge 免费优先数据源状态。")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    payload = build_free_data_source_status()
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(payload["summary_zh"])
    for item in payload["sources"]:
        env = item.get("env_var") or "不需要"
        print(f"- {item['name']}: {item['status']}，{item['cost_zh']}，配置：{env}")


if __name__ == "__main__":
    main()

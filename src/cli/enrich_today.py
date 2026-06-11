from __future__ import annotations

import argparse
import json

from src.intelligence.fusion import build_intelligence_preview


def main() -> None:
    parser = argparse.ArgumentParser(description="JC Edge 今日赛前情报增强预览")
    parser.add_argument("--provider", default="auto")
    parser.add_argument("--date", default=None)
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--risk-profile", default="aggressive")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    payload = build_intelligence_preview(args.provider, args.date, bankroll=args.bankroll, risk_profile=args.risk_profile)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    reliability = payload.get("reliability_summary", {})
    print("JC Edge 今日增强预览")
    print(f"日期: {payload.get('date')}")
    print(f"比赛数: {payload.get('matches_count')}")
    print(f"数据源: {payload.get('provider_used')}")
    print(f"情报完整度: {reliability.get('overall_score')}/100 {reliability.get('overall_label_zh')}")
    print(f"主要缺口: {'、'.join(reliability.get('main_gaps_zh', [])) or '暂无'}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json

from src.application import build_analysis_payload, default_target_date


DISCLAIMER_BLOCK = [
    "仅供数据研究与娱乐参考",
    "概率模型不保证结果",
    "串关会显著放大风险",
    "请勿投入无法承受损失的资金",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="竞彩足球概率推演与组合候选分析工具")
    parser.add_argument("--date", dest="target_date", default=None, help="Target date in YYYY-MM-DD")
    parser.add_argument("--format", dest="output_format", default="text", choices=["text", "json"])
    parser.add_argument("--export", dest="export_format", default=None, choices=["csv", "xlsx"])
    parser.add_argument("--provider", dest="provider_name", default="auto", choices=["auto", "mock", "sporttery"])
    parser.add_argument("--historical-data", dest="historical_data_path", default=None, help="Path to historical CSV data")
    parser.add_argument("--no-historical-fixture", dest="no_historical_fixture", action="store_true")
    parser.add_argument("--calibration-artifact", dest="calibration_artifact_path", default=None)
    parser.add_argument("--report-md", dest="report_markdown_path", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_date = args.target_date or default_target_date()
    payload = build_analysis_payload(
        target_date=target_date,
        provider_name=args.provider_name,
        export_format=args.export_format,
        historical_data_path=args.historical_data_path,
        use_fixture_historical=not args.no_historical_fixture,
        calibration_artifact_path=args.calibration_artifact_path,
        report_markdown_path=args.report_markdown_path,
    )

    if args.output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    _print_text_report(payload)
    return 0


def _print_text_report(payload: dict[str, object]) -> None:
    print(f"日期: {payload['date']}")
    print(f"分析场次: {payload['matches_analyzed']}")
    print(
        "数据源: "
        f"{payload.get('provider_used', 'unknown')} "
        f"(requested={payload.get('provider', payload.get('provider_requested', 'unknown'))})"
    )
    print(f"模型版本: {payload.get('model_version', 'unknown')}")
    print(f"校准状态: {payload.get('calibration_status', 'not_provided')}")
    print(f"历史数据状态: {payload.get('historical_data_status', 'unknown')}")
    print(f"模型组件: {', '.join(payload.get('model_components_available', []))}")
    if payload.get("fallback_used"):
        print("已自动降级到备用 provider")
    if payload.get("provider_warnings"):
        print("provider warnings:")
        for warning in payload["provider_warnings"]:
            print(f"- {warning}")
    print()
    print("单关候选:")
    singles = payload["single_candidates"]
    if singles:
        for item in singles:
            print(f"- {item['match_no']} {item['home_team']} vs {item['away_team']} | {item['play_type']} {item['outcome_label']} @ {item['odds']}")
            print(f"  去水概率 {item['fair_prob']:.3f} | 模型概率 {item['model_prob']:.3f} | Edge {item['edge']:.3f} | EV {item['ev']:.3f}")
            print(f"  风险 {item['risk_level']} | 推荐用途 {item['recommended_use']}")
    else:
        print("- 无")

    print()
    print("2串1 候选:")
    parlays_2x1 = payload["parlay_2x1_candidates"]
    if parlays_2x1:
        for item in parlays_2x1:
            print(f"- 组合赔率 {item['combined_odds']} | 命中概率 {item['hit_probability']:.3f} | EV {item['ev']:.3f} | 风险 {item['risk_level']}")
    else:
        print("- 无")

    print()
    print("3串1 候选:")
    parlays_3x1 = payload["parlay_3x1_candidates"]
    if parlays_3x1:
        for item in parlays_3x1:
            print(f"- 组合赔率 {item['combined_odds']} | 命中概率 {item['hit_probability']:.3f} | EV {item['ev']:.3f} | 风险 {item['risk_level']}")
    else:
        print("- 无")

    if payload.get("warnings"):
        print()
        print("警告:")
        for warning in payload["warnings"]:
            print(f"- {warning}")

    print()
    for line in DISCLAIMER_BLOCK:
        print(f"- {line}")


if __name__ == "__main__":
    raise SystemExit(main())

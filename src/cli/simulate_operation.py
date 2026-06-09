from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.backtesting.historical_loader import load_historical_matches_with_warnings
from src.paper_trading.report import build_paper_operation_report
from src.paper_trading.walkforward import run_paper_operation_walkforward


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="运行本地纸面模拟走盘，不涉及真实资金。")
    parser.add_argument("--historical-data", required=True)
    parser.add_argument("--initial-bankroll", type=float, default=10000.0)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--max-single-per-day", type=int, default=2)
    parser.add_argument("--max-parlay-2x1-per-day", type=int, default=1)
    parser.add_argument("--enable-3x1", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--write-report")
    args = parser.parse_args(argv)
    try:
        matches, warnings = load_historical_matches_with_warnings(args.historical_data)
        if not matches:
            raise ValueError("未能读取可用历史比赛。请检查 CSV 路径、字段和比分信息。")
        report = run_paper_operation_walkforward(
            matches,
            initial_bankroll=args.initial_bankroll,
            start_date=args.start_date,
            end_date=args.end_date,
            strategy_config={
                "max_single_per_day": args.max_single_per_day,
                "max_parlay_2x1_per_day": args.max_parlay_2x1_per_day,
                "max_parlay_3x1_per_day": 1 if args.enable_3x1 else 0,
            },
        )
        report["warnings"] = list(dict.fromkeys(list(warnings or []) + list(report.get("warnings", []) or [])))
        if args.write_report:
            report["report_path"] = _write_markdown(report, args.write_report)
        if args.format == "json":
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            _print_text(report)
        return 0
    except Exception as exc:
        message = f"模拟走盘失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message, "warnings": ["不会暴露 Python traceback，请检查输入 CSV 和字段。"]}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


def _print_text(report: dict) -> None:
    print("模拟走盘完成")
    print(f"初始模拟本金: ¥{report.get('initial_bankroll', 0):,.2f}")
    print(f"最终模拟本金: ¥{report.get('final_bankroll', 0):,.2f}")
    print(f"总盈亏: ¥{report.get('total_profit', 0):,.2f}")
    print("本结果仅为纸面模拟，不代表未来表现。")


def _write_markdown(report: dict, path: str) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 模拟走盘报告",
        "",
        f"- 初始模拟本金: ¥{report.get('initial_bankroll', 0):,.2f}",
        f"- 最终模拟本金: ¥{report.get('final_bankroll', 0):,.2f}",
        f"- 总盈亏: ¥{report.get('total_profit', 0):,.2f}",
        f"- ROI: {float(report.get('roi', 0)) * 100:.2f}%",
        f"- 命中率: {float(report.get('hit_rate', 0)) * 100:.2f}%",
        "",
        "本工具只做本地概率分析、纸面模拟和回测诊断。不提供投注、下单、支付、代购或任何自动化购彩能力。",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return str(target)


if __name__ == "__main__":
    raise SystemExit(main())

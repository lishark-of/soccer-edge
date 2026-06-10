from __future__ import annotations

import argparse
import json
import sys

from src.application import build_analysis_payload
from src.optimizer.candidate_pool import build_candidate_pool
from src.optimizer.portfolio_optimizer import optimize_portfolio


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成赛前观察组合优化结果，只做本地概率研究。")
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--date")
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--enable-3x1", action="store_true")
    parser.add_argument("--risk-profile", choices=["conservative", "balanced", "aggressive"], default="conservative")
    parser.add_argument("--show-rejected", action="store_true")
    parser.add_argument("--compare-profiles", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        payload = build_analysis_payload(target_date=args.date, provider_name=args.provider)
        candidates = build_candidate_pool(payload)
        result = optimize_portfolio(candidates, bankroll=args.bankroll, config={"enable_3x1": args.enable_3x1, "risk_profile": args.risk_profile, "show_rejected": args.show_rejected, "compare_profiles": args.compare_profiles})
        result.update({"provider": args.provider, "date": payload.get("date") or args.date, "matches_analyzed": payload.get("matches_analyzed", 0), "candidate_pool_count": len(candidates), "warnings": payload.get("warnings", []) + payload.get("provider_warnings", [])})
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"赛前组合优化完成：{result.get('risk_profile_label')}档，推荐纸面投入 ¥{result.get('recommended_paper_exposure', 0):,.2f}")
            print(result.get("disclaimer"))
        return 0
    except Exception as exc:
        message = f"赛前组合优化失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message, "warnings": ["不会暴露 Python traceback。"]}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

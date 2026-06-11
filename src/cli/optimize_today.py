from __future__ import annotations

import argparse
import json
import sys

from src.intelligence.fusion import build_intelligence_preview


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成赛前观察组合优化结果，只做本地概率研究。")
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--date")
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--external-signals", default=None)
    parser.add_argument("--enable-3x1", action="store_true")
    parser.add_argument("--risk-profile", choices=["conservative", "balanced", "aggressive"], default="conservative")
    parser.add_argument("--show-rejected", action="store_true")
    parser.add_argument("--compare-profiles", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        payload = build_intelligence_preview(args.provider, args.date, args.external_signals, bankroll=args.bankroll, risk_profile=args.risk_profile)
        result = dict(payload.get("optimizer", {}))
        result.update({
            "provider": args.provider,
            "provider_used": payload.get("provider_used"),
            "date": payload.get("date") or args.date,
            "matches_analyzed": payload.get("matches_count", 0),
            "candidate_pool_count": len(payload.get("optimizer_candidates", []) or []),
            "top_total_goals_observations": payload.get("top_total_goals_observations", []),
            "top_score_observations": payload.get("top_score_observations", []),
            "missing_signals": payload.get("missing_signals", []),
            "credibility_gate": payload.get("credibility_gate", {}),
            "credibility_audit": payload.get("credibility_audit", {}),
            "external_signals_status": payload.get("external_signals_status", {}),
            "no_combo_reason": result.get("no_combo_reason") or (payload.get("credibility_gate", {}) or {}).get("reason_zh", ""),
            "warnings": payload.get("warnings", []),
        })
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

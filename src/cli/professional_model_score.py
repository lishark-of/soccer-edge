from __future__ import annotations

import argparse
import json
import sys

from src.audit.credibility import audit_credibility
from src.intelligence.fusion import build_intelligence_preview


def build_professional_score_payload(
    provider: str,
    date: str | None,
    bankroll: float,
    risk_profile: str,
    external_signals: str | None,
) -> dict:
    preview = build_intelligence_preview(
        provider,
        date,
        external_signals,
        bankroll=bankroll,
        risk_profile=risk_profile,
    )
    optimizer = preview.get("optimizer", {}) or {}
    credibility = preview.get("credibility_audit") or audit_credibility(preview, optimizer)
    professional_score = credibility.get("professional_model_score", {}) or {}
    return {
        "title": "职业模型评分审计",
        "selected_date": preview.get("selected_date") or preview.get("date") or date,
        "provider_used": preview.get("provider_used"),
        "matches_count": preview.get("matches_count", 0),
        "risk_profile": risk_profile,
        "score": professional_score.get("score"),
        "ceiling_score": professional_score.get("ceiling_score"),
        "grade": professional_score.get("grade"),
        "label_zh": professional_score.get("label_zh"),
        "summary_zh": professional_score.get("summary_zh"),
        "components": professional_score.get("components", []),
        "learning_evidence": professional_score.get("learning_evidence", {}),
        "evidence_requirements": professional_score.get("evidence_requirements", {}),
        "score_trend": professional_score.get("score_trend", {}),
        "ai_research_quality": professional_score.get("ai_research_quality", {}),
        "roadmap_to_95": professional_score.get("roadmap_to_95", {}),
        "missing_to_95": professional_score.get("missing_to_95", []),
        "industry_benchmark_zh": professional_score.get("industry_benchmark_zh", []),
        "research_sources_zh": professional_score.get("research_sources_zh", []),
        "principles_zh": professional_score.get("principles_zh", []),
        "credibility_gate": credibility.get("credibility_gate", preview.get("credibility_gate", {})),
        "warnings": preview.get("warnings", []),
        "disclaimer": "仅用于本地概率研究、纸面观察和模型审计，不提供真实投注、下单、支付或代购能力。",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="输出 JC Edge 职业模型评分审计。")
    parser.add_argument("--provider", default="auto")
    parser.add_argument("--date")
    parser.add_argument("--bankroll", type=float, default=10000.0)
    parser.add_argument("--risk-profile", choices=["conservative", "balanced", "aggressive"], default="aggressive")
    parser.add_argument("--external-signals")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    try:
        payload = build_professional_score_payload(
            args.provider,
            args.date,
            args.bankroll,
            args.risk_profile,
            args.external_signals,
        )
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"职业模型分：{payload.get('score')}/{payload.get('ceiling_score')}，评级 {payload.get('grade')}")
            print(payload.get("summary_zh") or "暂无摘要。")
            actions = (payload.get("roadmap_to_95") or {}).get("next_best_actions", [])
            if actions:
                print("下一步最有效改进：")
                for item in actions[:3]:
                    print(f"- {item.get('title_zh')}: {item.get('action_zh')}")
        return 0
    except Exception as exc:  # noqa: BLE001
        message = f"职业模型评分失败：{str(exc).splitlines()[0]}"
        if args.format == "json":
            print(json.dumps({"ok": False, "error_zh": message, "warnings": ["不会暴露 Python traceback。"]}, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

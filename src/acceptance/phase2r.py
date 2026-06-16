from __future__ import annotations

from pathlib import Path

from src.backtesting.credibility import build_backtest_credibility_report
from src.explain.deepseek_config import llm_status_payload
from src.market.clv import build_clv_tracking, load_closing_odds_csv, load_observations_json
from src.optimizer.portfolio_optimizer import optimize_portfolio


ROOT = Path(__file__).resolve().parents[2]
DISCLAIMER = "Phase 2-R 验收仅检查本地观察、解释、CLV 与回测可信度能力，不构成投注建议。"


def build_phase2r_acceptance_report() -> dict:
    checks = [
        _check_parlay_discipline(),
        _check_today_simplification(),
        _check_deepseek_layer(),
        _check_clv_review(),
        _check_backtest_credibility(),
    ]
    passed = [check for check in checks if check.get("passed")]
    return {
        "acceptance_version": "phase2r_acceptance_v0",
        "overall_passed": len(passed) == len(checks),
        "passed_count": len(passed),
        "total_count": len(checks),
        "checks": checks,
        "next_steps": _next_steps(checks),
        "disclaimer": DISCLAIMER,
    }


def _check_parlay_discipline() -> dict:
    result = optimize_portfolio(
        [
            _candidate("m1", "A", "B", "客胜", 8.0, 0.18, 0.10, 0.44, 0.08),
            _candidate("m2", "C", "D", "主胜", 2.0, 0.58, 0.50, 0.16, 0.08),
        ],
        bankroll=10000,
        config={"risk_profile": "aggressive"},
    )
    limits = result.get("risk_summary", {}).get("profile_limits", {})
    singles = result.get("candidate_rankings", {}).get("singles", [])
    reasons = " ".join(row.get("reject_reason", "") for row in result.get("candidate_rankings", {}).get("parlay_2x1", []))
    passed = (
        limits.get("min_parlay_2x1_prob") == 0.20
        and limits.get("min_parlay_3x1_prob") == 0.12
        and any(row.get("longshot_warning") and row.get("parlay_eligible") is False for row in singles)
        and "高赔率冷门腿不适合作为串联核心" in reasons
    )
    return {
        "id": "R1_parlay_discipline",
        "passed": passed,
        "summary_zh": "串联纪律包含命中率门槛、单腿可信度和高赔率冷门限制。",
        "evidence": {
            "limits": limits,
            "longshot_blocked": any(row.get("longshot_warning") and row.get("parlay_eligible") is False for row in singles),
            "reject_reasons": reasons,
        },
    }


def _check_today_simplification() -> dict:
    html = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
    today = html.split('id="view-today"', 1)[1].split('id="view-credibility"', 1)[0]
    passed = (
        "Top 单关观察" in today
        and "Top 2串1观察" in today
        and "Top 总进球观察" in today
        and "Top 比分观察" in today
        and "API Base" not in today
    )
    return {
        "id": "R2_today_simplified",
        "passed": passed,
        "summary_zh": "今日观察优先展示 Top 信号，技术配置不在今日观察第一屏。",
        "evidence": {
            "has_top_single": "Top 单关观察" in today,
            "has_top_parlay2": "Top 2串1观察" in today,
            "has_top_total_goals": "Top 总进球观察" in today,
            "has_top_scores": "Top 比分观察" in today,
            "api_base_hidden_from_today": "API Base" not in today,
        },
    }


def _check_deepseek_layer() -> dict:
    status = llm_status_payload()
    html = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")
    llm_state = status.get("status")
    key_gated_ok = llm_state == "disabled" or (llm_state == "ready" and status.get("api_key_present") is True)
    safe_explainer_only = (
        status.get("external_calls_default") is False
        and status.get("safe_usage") == "optional_explainer_only"
        and "不参与概率、EV、候选筛选或组合决策" in (html + app_js)
    )
    passed = (
        key_gated_ok
        and safe_explainer_only
        and "DeepSeek Pro key" in app_js
    )
    return {
        "id": "R3_deepseek_optional_explainer",
        "passed": passed,
        "summary_zh": "DeepSeek Pro 由本地 key 显式启用，只做解释层，不参与概率和组合筛选。",
        "evidence": {
            "status": status.get("status"),
            "api_key_present": status.get("api_key_present"),
            "external_calls_default": status.get("external_calls_default"),
            "safe_usage": status.get("safe_usage"),
            "has_key_input": "DeepSeek Pro key" in app_js,
            "safe_explainer_only": safe_explainer_only,
        },
    }


def _check_clv_review() -> dict:
    data = build_clv_tracking(
        load_observations_json("data/fixtures/clv_observations_example.json"),
        load_closing_odds_csv("data/fixtures/closing_odds_example.csv"),
    )
    passed = data.get("settled_count") == 2 and data.get("positive_clv_count") == 1
    return {
        "id": "R4_clv_tracking",
        "passed": passed,
        "summary_zh": "CLV 支持赛前记录、App/API 状态和本地收盘赔率复盘。",
        "evidence": {
            "tracked_count": data.get("tracked_count"),
            "settled_count": data.get("settled_count"),
            "positive_clv_count": data.get("positive_clv_count"),
            "negative_clv_count": data.get("negative_clv_count"),
        },
    }


def _check_backtest_credibility() -> dict:
    data = build_backtest_credibility_report("data/fixtures/operation_walkforward_sample.csv", source_type="fixture")
    passed = data.get("score", 999) <= 60 and data.get("grade") in {"C", "D"}
    return {
        "id": "R5_backtest_credibility",
        "passed": passed,
        "summary_zh": "用户 CSV / fixture 回测可信度按数据质量评分，fixture 不会被评为高可信。",
        "evidence": {
            "score": data.get("score"),
            "grade": data.get("grade"),
            "confidence_level_zh": data.get("confidence_level_zh"),
            "odds_coverage": data.get("odds_coverage"),
            "result_coverage": data.get("result_coverage"),
        },
    }


def _candidate(match_id, home, away, outcome, odds, model_prob, market_prob, ev, edge):
    return {
        "candidate_type": "single",
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "play_type": "had",
        "outcome_key": outcome,
        "outcome_label": outcome,
        "odds": odds,
        "model_prob": model_prob,
        "market_prob": market_prob,
        "ev": ev,
        "edge": edge,
        "risk_level": "medium",
        "observation_confidence": 0.62,
    }


def _next_steps(checks: list[dict]) -> list[str]:
    failed = [check for check in checks if not check.get("passed")]
    if failed:
        return [f"修复 {check['id']}：{check['summary_zh']}" for check in failed]
    return [
        "可进行浏览器视觉验收。",
        "如环境支持，可运行 python3 -m pytest。",
        "验收通过后再本地 commit；不要 push，除非用户提供 remote 并明确授权。",
    ]

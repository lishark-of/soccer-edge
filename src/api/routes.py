from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import time

from src.api.errors import ApiError
from src.api.read_only import ensure_read_only_operation
from src.api.schemas import success_response
from src.application import build_analysis_payload, build_matches_payload
from src.audit.credibility import audit_credibility
from src.audit.trader_review import build_trader_review
from src.audit.user_journey import run_user_acceptance_audit
from src.backtesting.backtest_engine import run_backtest
from src.backtesting.credibility import build_backtest_credibility_report
from src.backtesting.historical_loader import load_historical_matches_with_warnings
from src.backtesting.report import build_backtest_report
from src.backtesting.schema import validate_historical_dataset
from src.calibration.persistence import load_calibration_artifact
from src.calibration.store import validate_calibration_artifact
from src.cli.user_data_workflow import preview_user_data_workflow
from src.acceptance.phase2r import build_phase2r_acceptance_report
from src.explain.deepseek_config import llm_status_payload
from src.explain.deepseek_runtime import update_runtime_status
from src.explain.deepseek_explainer import explain_with_optional_deepseek
from src.explain.ai_combo_research import build_ai_combo_research
from src.exports.report_exporter import summarize_report
from src.ingestion.field_report import build_field_recognition_report
from src.ingestion.importer import import_historical_file
from src.ingestion.repair_suggestions import build_repair_suggestions
from src.intelligence.fusion import build_intelligence_preview, build_next_available_preview
from src.intelligence.external_signals_loader import preview_external_signals
from src.intelligence.missing_info import build_missing_info_from_preview
from src.market.clv import build_clv_tracking, build_clv_history, load_closing_odds_csv, load_observations_json, save_clv_review
from src.learning.home_learning_view import build_home_learning_panel
from src.learning.odds_education import build_odds_learning_view
from src.learning.feedback_builder import build_feedback_from_files, save_feedback_from_files
from src.learning.daily_learning_pack import prepare_daily_learning_pack, save_daily_learning_results, save_quick_learning_results
from src.learning.history import build_learning_history
from src.learning.observation_snapshot import save_observation_snapshot
from src.learning.result_template import save_result_template_from_observations
from src.learning.closing_odds_template import save_closing_odds_template_from_observations
from src.release.metadata import build_release_metadata
from src.paper_trading.walkforward import run_paper_operation_walkforward
from src.optimizer.candidate_pool import build_candidate_pool
from src.optimizer.best_parlay import build_best_parlay_summary
from src.optimizer.portfolio_optimizer import optimize_portfolio
from src.config.local_env import save_local_env_values
from src.providers.free_data_sources import build_free_data_source_status
from src.providers.third_party_verify import verify_third_party_source
from src.version import get_build_info
from src.view_models.analysis_view import build_analysis_view
from src.view_models.backtest_view import build_backtest_view
from src.view_models.calibration_view import build_calibration_view
from src.view_models.import_view import build_import_preview_view
from src.view_models.intelligence_view import build_intelligence_coverage_table, build_intelligence_view
from src.view_models.matches_view import build_matches_view, build_sporttery_status_view
from src.view_models.next_available_view import build_next_available_view
from src.view_models.onboarding_view import build_onboarding_view
from src.view_models.operation_view import build_operation_view
from src.view_models.optimizer_view import build_optimizer_view
from src.view_models.qa_view import build_qa_view
from src.view_models.reliability_view import build_reliability_view
from src.view_models.score_goals_view import build_score_goals_view
from src.view_models.signal_explanation_view import build_signal_explanation_view


VERSION = "0.1.0-local"
DISABLED_CAPABILITIES = ["betting", "payment", "order_placement", "proxy_purchase", "automation"]
NEXT_AVAILABLE_VIEW_CACHE_TTL_SECONDS = 180
AI_COMBO_RESEARCH_CACHE_TTL_SECONDS = 180
AI_COMBO_RESEARCH_STALE_FALLBACK_TTL_SECONDS = 21600
AI_COMBO_RESEARCH_CACHE_DIRNAME = "jc_edge_ai_combo_cache"
_NEXT_AVAILABLE_VIEW_CACHE: dict[tuple, dict] = {}
_AI_COMBO_RESEARCH_CACHE: dict[tuple, dict] = {}


def _cacheable_ai_combo_payload(payload: dict | None) -> bool:
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("ds_completed") or payload.get("reused_from_cached_ds"))


def _refresh_runtime_status_from_cached_ai_payload(payload: dict) -> None:
    if not _cacheable_ai_combo_payload(payload):
        return
    update_runtime_status(
        provider_requested=str(payload.get("provider_requested") or "auto"),
        provider_target=str(payload.get("provider_target") or "deepseek"),
        provider_resolved=str(payload.get("provider_resolved") or "deepseek"),
        ds_status="cached",
        ds_status_zh="已复用最近一次 DS 研究",
        ds_attempted=True,
        ds_completed=True,
        ds_error_code=str(payload.get("ds_error_code") or ""),
        fallback_reason=str(payload.get("fallback_reason") or ""),
        token_in=payload.get("token_in"),
        token_out=payload.get("token_out"),
        token_total=payload.get("token_total"),
    )


def _ai_combo_research_cache_path(key: tuple) -> Path:
    digest = hashlib.sha1(repr(key).encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / AI_COMBO_RESEARCH_CACHE_DIRNAME / f"{digest}.json"


def _load_ai_combo_research_disk_cache(key: tuple, ttl_seconds: int, now: float | None = None) -> dict | None:
    path = _ai_combo_research_cache_path(key)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    created_at = float(raw.get("created_at", 0.0) or 0.0)
    payload = raw.get("payload", {})
    current_time = now if now is not None else time.time()
    if created_at <= 0 or current_time - created_at > ttl_seconds:
        return None
    if not _cacheable_ai_combo_payload(payload):
        return None
    return {"created_at": created_at, "payload": dict(payload)}


def _persist_ai_combo_research_disk_cache(key: tuple, created_at: float, payload: dict) -> None:
    if not _cacheable_ai_combo_payload(payload):
        return
    path = _ai_combo_research_cache_path(key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"created_at": created_at, "payload": payload}, ensure_ascii=False), encoding="utf-8")
    except (OSError, TypeError, ValueError):
        return


def dispatch_route(path: str, query: dict[str, str]) -> dict:
    if path == "/api/health":
        build_info = get_build_info()
        return success_response(
            {
                "status": "ok",
                "service": "football-jc-analysis",
                "mode": "read_only",
                "version": build_info["version"],
                "release_phase": build_info["release_phase"],
            }
        )
    if path == "/api/info":
        metadata = build_release_metadata()
        return success_response(
            {
                **metadata,
                "project": "football-jc-analysis",
                "mode": metadata["mode"],
                "capabilities": [
                    "matches",
                    "analyze",
                    "backtest",
                    "import_preview",
                    "calibration_validate",
                    "report_summary",
                    "view_analyze",
                    "view_backtest",
                    "view_backtest_credibility",
                    "view_import_preview",
                    "view_calibration_validate",
                    "view_qa",
                    "llm_status",
                    "view_learning_history",
                    "explain_candidate",
                    "user_workflow_preview",
                    "view_user_workflow",
                    "view_matches",
                    "view_onboarding",
                    "view_sporttery_status",
                    "operation_simulate",
                    "view_operation",
                    "optimizer_pre_match",
                    "view_optimizer",
                    "intelligence_preview",
                    "view_intelligence",
                    "view_next_available",
                    "view_score_goals",
                    "view_data_sources",
                    "view_reliability",
                    "view_source_coverage",
                    "view_signal_explain",
                    "intelligence_enriched_preview",
                    "intelligence_coverage",
                    "audit_user_journey",
                    "audit_credibility",
                    "view_best_parlay",
                    "view_ai_combo_research",
                    "view_trader_review",
                    "view_clv",
                    "view_clv_review",
                    "view_backtest_credibility",
                    "view_phase2r_acceptance",
                ],
                "disabled_capabilities": DISABLED_CAPABILITIES,
                "version": metadata["version"],
                "release_phase": metadata["release_phase"],
                "disclaimer": "For research and entertainment reference only. No betting, payment, or order placement.",
            }
        )
    if path == "/api/llm/status":
        return success_response(llm_status_payload())
    if path == "/api/view/learning-history":
        payload = build_learning_history()
        return success_response(payload, [item.get("message_zh", "") for item in payload.get("errors", []) if item.get("message_zh")])
    if path == "/api/explain/candidate":
        mode = query.get("provider", "local")
        sample = {
            "home_team": query.get("home_team", "Alpha FC"),
            "away_team": query.get("away_team", "Beta United"),
            "play_type": query.get("play_type", "had"),
            "outcome_label": query.get("outcome_label", "主胜"),
            "odds": _float_param(query, "odds", 2.1),
            "fair_prob": _float_param(query, "fair_prob", 0.45),
            "model_prob": _float_param(query, "model_prob", 0.52),
            "edge": _float_param(query, "edge", 0.07),
            "ev": _float_param(query, "ev", 0.092),
            "risk_level": query.get("risk_level", "medium"),
        }
        result = explain_with_optional_deepseek("candidate", sample, {"provider": mode, "language": "zh-CN"})
        return success_response(result, result.get("warnings", []))
    if path == "/api/matches":
        return success_response(build_matches_payload(target_date=query.get("date"), provider_name=query.get("provider", "auto")))
    if path == "/api/analyze":
        _reject_write_params(query, {"export", "report_md", "report-md"})
        payload = build_analysis_payload(
            target_date=query.get("date"),
            provider_name=query.get("provider", "auto"),
            historical_data_path=query.get("historical_data"),
            use_fixture_historical=_truthy(query.get("no_historical_fixture")) is False,
            calibration_artifact_path=query.get("calibration_artifact"),
        )
        return success_response(payload, payload.get("warnings", []))
    if path == "/api/backtest":
        _reject_write_params(query, {"export", "save_calibration", "save-calibration", "report_md", "report-md"})
        return success_response(_run_backtest_from_query(query))
    if path == "/api/import/preview":
        _reject_write_params(query, {"output"})
        input_path = _required(query, "input")
        payload = import_historical_file(
            input_path=input_path,
            adapter_name=query.get("adapter", "auto"),
            mapping_path=query.get("mapping"),
            dry_run=True,
        )
        _attach_field_guidance(payload)
        return success_response(payload, payload.get("warnings", []))
    if path == "/api/user-workflow/preview":
        payload = preview_user_data_workflow(_required(query, "input"), mapping_path=query.get("mapping"))
        return success_response(payload, payload.get("warnings", []))
    if path == "/api/user-workflow/run":
        ensure_read_only_operation("user-workflow/run", write_requested=True)
    if path == "/api/calibration/validate":
        return success_response(_validate_calibration_from_query(query))
    if path == "/api/report/summary":
        report_type = query.get("type", "analysis")
        if report_type == "backtest":
            return success_response(summarize_report(_run_backtest_from_query(query)))
        if report_type == "analysis":
            payload = build_analysis_payload(target_date=query.get("date"), provider_name=query.get("provider", "mock"))
            return success_response(summarize_report(payload))
        raise ApiError("bad_request", "type must be analysis or backtest")
    if path == "/api/view/matches":
        payload = build_matches_payload(target_date=query.get("date"), provider_name=query.get("provider", "auto"))
        view = build_matches_view(payload)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/onboarding":
        view = build_onboarding_view()
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/sporttery-status":
        payload = build_matches_payload(target_date=query.get("date"), provider_name=query.get("provider", "auto"))
        view = build_sporttery_status_view(payload)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/next-available":
        view = _cached_next_available_view(query)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/data-sources":
        payload = build_free_data_source_status()
        return success_response(payload, [])
    if path == "/api/data-sources/verify":
        source = _required(query, "source")
        payload = verify_third_party_source(source)
        return success_response(payload, [] if payload.get("status") == "ok" else [payload.get("message_zh", "")])
    if path == "/api/intelligence/preview":
        result = _run_intelligence_from_query(query)
        return success_response(result, result.get("warnings", []))
    if path == "/api/intelligence/enriched-preview":
        result = _run_intelligence_from_query(query)
        return success_response(result, result.get("warnings", []))
    if path == "/api/intelligence/missing":
        result = _run_intelligence_from_query(query)
        payload = build_missing_info_from_preview(result)
        payload["credibility_gate"] = result.get("credibility_gate", {})
        return success_response(payload, [])
    if path == "/api/intelligence/signals-preview":
        signals_path = query.get("signals_path") or query.get("signals") or query.get("external_signals")
        payload = preview_external_signals(signals_path, query.get("date"))
        if signals_path:
            result = build_intelligence_preview(
                query.get("provider", "auto"),
                query.get("date"),
                signals_path,
                bankroll=_float_param(query, "bankroll", 10000.0),
                risk_profile=query.get("risk_profile", "aggressive"),
            )
            payload["credibility_gate"] = result.get("credibility_gate", {})
            payload["credibility_audit"] = result.get("credibility_audit", {})
            payload["missing_information_after_preview"] = build_missing_info_from_preview(result)
        return success_response(payload, [])
    if path == "/api/intelligence/coverage":
        result = _run_intelligence_from_query(query)
        payload = build_intelligence_coverage_table(result)
        payload["credibility_gate"] = result.get("credibility_gate", {})
        payload["source_coverage"] = result.get("source_coverage", {})
        return success_response(payload, result.get("warnings", []))
    if path == "/api/view/intelligence":
        result = _run_intelligence_from_query(query)
        view = build_intelligence_view(result)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/reliability":
        result = _run_intelligence_from_query(query)
        view = build_reliability_view(result)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/source-coverage":
        result = _run_intelligence_from_query(query)
        coverage = result.get("source_coverage", {})
        return success_response(coverage, coverage.get("warnings", []))
    if path == "/api/view/signal-explain":
        result = _run_intelligence_from_query(query)
        view = build_signal_explanation_view(result)
        return success_response(view, view.get("warnings", []))
    if path == "/api/audit/user-journey":
        payload = run_user_acceptance_audit(".")
        return success_response(payload, [] if payload.get("overall_passed") else ["使用者实操验收发现可改进项。"])
    if path == "/api/audit/credibility":
        result = _run_intelligence_from_query(query)
        payload = audit_credibility(result, result.get("optimizer", {}))
        return success_response(payload, [])
    if path == "/api/view/credibility-gate":
        result = _run_intelligence_from_query(query)
        payload = result.get("credibility_gate", {})
        payload = {**payload, "credibility_audit": result.get("credibility_audit", {}), "no_combo_reason": (result.get("optimizer") or {}).get("no_combo_reason", "")}
        return success_response(payload, [])
    if path == "/api/view/score-goals":
        result = _run_intelligence_from_query(query)
        view = build_score_goals_view(result)
        return success_response(view, view.get("warnings", []))
    if path == "/api/optimizer/pre-match":
        result = _run_optimizer_from_query(query)
        run_ai = _truthy(query.get("run_ai")) if "run_ai" in query else True
        result["ai_combo_research"] = _cached_ai_combo_research(result, query, run_ai)
        result["llm_status"] = result.get("llm_status") or llm_status_payload()
        result["ai_research_status"] = build_optimizer_view(result).get("ai_research_status", {})
        return success_response(result, result.get("warnings", []))
    if path == "/api/view/optimizer":
        result = _run_optimizer_from_query(query)
        run_ai = _truthy(query.get("run_ai")) if "run_ai" in query else True
        if run_ai:
            result["ai_combo_research"] = _cached_ai_combo_research(result, query, True)
        view = build_optimizer_view(result)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/best-parlay":
        result = _run_optimizer_from_query(query)
        payload = result.get("best_parlay_summary") or build_best_parlay_summary(result)
        return success_response(payload, payload.get("warnings", []))
    if path == "/api/view/ai-combo-research":
        result = _run_ai_combo_optimizer_from_query(query)
        run_ai = _truthy(query.get("run")) if "run" in query else True
        payload = _cached_ai_combo_research(result, query, run_ai)
        payload["no_combo_reason"] = result.get("no_combo_reason", "")
        payload["credibility_gate"] = result.get("credibility_gate", {})
        payload["best_parlay_summary"] = result.get("best_parlay_summary", {})
        payload["daily_learning_metrics"] = result.get("daily_learning_metrics", [])
        payload["window_learning_metrics"] = result.get("window_learning_metrics", [])
        payload["latest_daily_summary_zh"] = result.get("latest_daily_summary_zh", "")
        payload["window_learning_summaries_zh"] = result.get("window_learning_summaries_zh", [])
        payload["daily_learning_digest"] = result.get("daily_learning_digest", {})
        payload["window_learning_digests"] = result.get("window_learning_digests", [])
        payload["best_risk_adjusted_final_status"] = (
            (((result.get("best_parlay_summary") or {}).get("best_risk_adjusted_combo") or {}).get("best_parlay_quality") or {}).get("final_status", "")
        )
        warnings = list(payload.get("ai_summary", {}).get("warnings", []) or [])
        return success_response(payload, warnings)
    if path == "/api/view/clv":
        result = _run_optimizer_from_query(query)
        payload = result.get("clv_tracking", {})
        return success_response(payload, payload.get("warnings", []))
    if path == "/api/view/clv-review":
        observations_path = query.get("observations_json") or query.get("observations") or _required(query, "observations_json")
        closing_path = query.get("closing_odds") or query.get("closing") or _required(query, "closing_odds")
        payload = build_clv_tracking(load_observations_json(observations_path), load_closing_odds_csv(closing_path))
        return success_response(payload, [])
    if path == "/api/learning/save-clv-review":
        observations_path = query.get("observations_json") or query.get("observations") or _required(query, "observations_json")
        closing_path = query.get("closing_odds") or query.get("closing") or _required(query, "closing_odds")
        payload = save_clv_review(observations_path, closing_path)
        return success_response(payload, [])
    if path == "/api/view/clv-history":
        payload = build_clv_history()
        return success_response(payload, [])
    if path == "/api/view/learning-feedback":
        payload = build_home_learning_panel(query.get("feedback_path"))
        return success_response(payload, [])
    if path == "/api/view/build-learning-feedback":
        payload = build_feedback_from_files(
            _required(query, "observations_json"),
            _required(query, "results_csv"),
            date=query.get("date"),
        )
        return success_response(payload, [])
    if path == "/api/learning/save-observation-snapshot":
        preview = _run_next_available_from_query(query)
        payload = save_observation_snapshot(preview)
        return success_response(payload, [])
    if path == "/api/learning/prepare-daily-pack":
        preview = _run_next_available_from_query(query)
        payload = prepare_daily_learning_pack(preview)
        return success_response(payload, [])
    if path == "/api/learning/save-daily-results":
        payload = save_daily_learning_results(
            _required(query, "observations_json"),
            _required(query, "results_csv"),
            query.get("closing_odds") or query.get("closing") or "",
        )
        return success_response(payload, [])
    if path == "/api/learning/save-result-template":
        payload = save_result_template_from_observations(_required(query, "observations_json"))
        return success_response(payload, [])
    if path == "/api/learning/save-closing-odds-template":
        payload = save_closing_odds_template_from_observations(_required(query, "observations_json"))
        return success_response(payload, [])
    if path == "/api/learning/save-feedback":
        payload = save_feedback_from_files(
            _required(query, "observations_json"),
            _required(query, "results_csv"),
            date=query.get("date"),
        )
        return success_response(payload, [])
    if path == "/api/view/learning-history":
        payload = build_learning_history(query.get("feedback_dir"), include_fixtures=_truthy(query.get("no_fixtures")) is False)
        return success_response(payload, [])
    if path == "/api/view/odds-learning":
        payload = build_odds_learning_view()
        return success_response(payload, [])
    if path == "/api/view/backtest-credibility":
        input_path = query.get("input") or query.get("historical_data") or _required(query, "input")
        payload = build_backtest_credibility_report(input_path, source_type=query.get("source_type", "user_csv"))
        return success_response(payload, [] if payload.get("status") != "error" else [payload.get("message_zh", "CSV 可信度检查失败。")])
    if path == "/api/view/phase2r-acceptance":
        payload = build_phase2r_acceptance_report()
        return success_response(payload, [] if payload.get("overall_passed") else ["Phase 2-R 验收仍有未通过项。"])
    if path == "/api/view/trader-review":
        result = _run_intelligence_from_query(query)
        payload = build_trader_review(result, result.get("optimizer", {}))
        return success_response(payload, payload.get("warnings", []))
    if path == "/api/operation/simulate":
        report = _run_operation_from_query(query)
        return success_response(report, report.get("warnings", []))
    if path == "/api/view/operation":
        report = _run_operation_from_query(query)
        view = build_operation_view(report)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/analyze":
        _reject_write_params(query, {"export", "report_md", "report-md"})
        payload = build_analysis_payload(
            target_date=query.get("date"),
            provider_name=query.get("provider", "auto"),
            historical_data_path=query.get("historical_data"),
            use_fixture_historical=_truthy(query.get("no_historical_fixture")) is False,
            calibration_artifact_path=query.get("calibration_artifact"),
        )
        view = build_analysis_view(payload, explain_mode=query.get("explain", "local"))
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/backtest":
        _reject_write_params(query, {"export", "save_calibration", "save-calibration", "report_md", "report-md"})
        historical_data = _required(query, "historical_data")
        view = build_backtest_view(_run_backtest_from_query(query))
        source_type = query.get("source_type") or ("fixture" if "fixtures" in historical_data else "user_csv")
        view["backtest_credibility"] = build_backtest_credibility_report(historical_data, source_type=source_type)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/import/preview":
        _reject_write_params(query, {"output"})
        payload = import_historical_file(
            input_path=_required(query, "input"),
            adapter_name=query.get("adapter", "auto"),
            mapping_path=query.get("mapping"),
            dry_run=True,
        )
        _attach_field_guidance(payload)
        view = build_import_preview_view(payload)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/user-workflow":
        payload = preview_user_data_workflow(_required(query, "input"), mapping_path=query.get("mapping"))
        return success_response(payload.get("user_view", {}), payload.get("warnings", []))
    if path == "/api/view/calibration/validate":
        view = build_calibration_view(_validate_calibration_from_query(query))
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/qa":
        from src.qa.runner import run_qa

        view = build_qa_view(run_qa(project_root=".", rehearsal=_truthy(query.get("rehearsal"))))
        return success_response(view, view.get("warnings", []))
    raise ApiError("not_found", f"unknown endpoint: {path}", status=404)


def dispatch_post_route(path: str, body: dict) -> dict:
    if path == "/api/config/local-env":
        payload = save_local_env_values(body if isinstance(body, dict) else {})
        return success_response(payload, [])
    if path == "/api/learning/save-quick-results":
        observations_json = str((body or {}).get("observations_json") or "")
        rows = (body or {}).get("rows") or []
        if not observations_json:
            raise ApiError("validation_error", "请先准备赛前观察快照，再保存赛后学习。")
        if not isinstance(rows, list) or not rows:
            raise ApiError("validation_error", "请至少填写一场比赛的比分。")
        payload = save_quick_learning_results(observations_json, rows)
        return success_response(payload, [])
    raise ApiError("not_found", f"unknown endpoint: {path}", status=404)



def _run_intelligence_from_query(query: dict[str, str]) -> dict:
    return build_intelligence_preview(
        query.get("provider", "auto"),
        query.get("date"),
        query.get("external_signals") or query.get("signals_path") or query.get("signals"),
        bankroll=_float_param(query, "bankroll", 10000.0),
        risk_profile=query.get("risk_profile", "aggressive"),
    )


def _run_next_available_from_query(query: dict[str, str]) -> dict:
    return build_next_available_preview(
        query.get("provider", "auto"),
        query.get("date"),
        bankroll=_float_param(query, "bankroll", 10000.0),
        risk_profile=query.get("risk_profile", "aggressive"),
        external_signals_path=query.get("external_signals") or query.get("signals_path") or query.get("signals"),
    )


def _cached_next_available_view(query: dict[str, str]) -> dict:
    key = (
        query.get("provider", "auto"),
        query.get("date", ""),
        str(_float_param(query, "bankroll", 10000.0)),
        query.get("risk_profile", "aggressive"),
        query.get("external_signals") or query.get("signals_path") or query.get("signals") or "",
    )
    now = time.time()
    if not _truthy(query.get("refresh")):
        cached = _NEXT_AVAILABLE_VIEW_CACHE.get(key)
        if cached and now - float(cached.get("created_at", 0.0)) <= NEXT_AVAILABLE_VIEW_CACHE_TTL_SECONDS:
            view = dict(cached.get("view", {}))
            view["cache_status"] = "hit"
            view["cache_status_zh"] = "已使用本地短时缓存，避免重复慢算。"
            view["cache_age_seconds"] = round(now - float(cached.get("created_at", now)), 2)
            return view
    result = _run_next_available_from_query(query)
    view = build_next_available_view(result)
    view["cache_status"] = "miss"
    view["cache_status_zh"] = "已重新计算明日预观察。"
    view["cache_age_seconds"] = 0
    _NEXT_AVAILABLE_VIEW_CACHE[key] = {"created_at": now, "view": dict(view)}
    return view


def _run_optimizer_from_query(query: dict[str, str]) -> dict:
    preview = _run_intelligence_from_query(query)
    return _optimizer_result_from_preview(preview, query)


def _cached_ai_combo_research(result: dict, query: dict[str, str], run_ai: bool) -> dict:
    ai_provider = query.get("ai_provider") or query.get("explain_provider") or "auto"
    key = (
        result.get("selected_date") or result.get("date") or query.get("date", ""),
        query.get("provider", "auto"),
        result.get("provider_used", ""),
        str(_float_param(query, "bankroll", 10000.0)),
        query.get("risk_profile", "aggressive"),
        query.get("external_signals") or query.get("signals_path") or query.get("signals") or "",
        ai_provider,
        "1" if run_ai else "0",
    )
    now = time.time()
    if not _truthy(query.get("refresh")):
        cached = _AI_COMBO_RESEARCH_CACHE.get(key)
        if cached and _cacheable_ai_combo_payload(cached.get("payload", {})) and now - float(cached.get("created_at", 0.0)) <= AI_COMBO_RESEARCH_CACHE_TTL_SECONDS:
            payload = dict(cached.get("payload", {}))
            _refresh_runtime_status_from_cached_ai_payload(payload)
            payload["cache_status"] = "hit"
            payload["cache_status_zh"] = "已复用最近一次 AI 研究结果，避免重复调用 DS Pro。"
            payload["cache_age_seconds"] = round(now - float(cached.get("created_at", now)), 2)
            return payload
        disk_cached = _load_ai_combo_research_disk_cache(key, AI_COMBO_RESEARCH_CACHE_TTL_SECONDS, now)
        if disk_cached:
            _AI_COMBO_RESEARCH_CACHE[key] = disk_cached
            payload = dict(disk_cached.get("payload", {}))
            _refresh_runtime_status_from_cached_ai_payload(payload)
            payload["cache_status"] = "disk_hit"
            payload["cache_status_zh"] = "已复用最近一次成功的 DS 研究结果（跨进程缓存）。"
            payload["cache_age_seconds"] = round(now - float(disk_cached.get("created_at", now)), 2)
            return payload
    previous_cached = _AI_COMBO_RESEARCH_CACHE.get(key) or _load_ai_combo_research_disk_cache(
        key,
        AI_COMBO_RESEARCH_STALE_FALLBACK_TTL_SECONDS,
        now,
    )
    payload = build_ai_combo_research(
        result,
        run_ai=run_ai,
        ai_provider=ai_provider,
    )
    reused = _reuse_cached_deepseek_payload(previous_cached, payload, now) if run_ai else None
    if reused:
        _AI_COMBO_RESEARCH_CACHE[key] = {"created_at": now, "payload": dict(reused)}
        _persist_ai_combo_research_disk_cache(key, now, reused)
        return reused
    payload["cache_status"] = "miss"
    payload["cache_status_zh"] = "已重新生成本轮 AI 研究结果。"
    payload["cache_age_seconds"] = 0
    if _cacheable_ai_combo_payload(payload):
        _AI_COMBO_RESEARCH_CACHE[key] = {"created_at": now, "payload": dict(payload)}
        _persist_ai_combo_research_disk_cache(key, now, payload)
    else:
        _AI_COMBO_RESEARCH_CACHE.pop(key, None)
    return payload


def _reuse_cached_deepseek_payload(cached: dict | None, failed_payload: dict, now: float) -> dict | None:
    if not cached:
        return None
    age_seconds = now - float(cached.get("created_at", 0.0))
    if age_seconds > AI_COMBO_RESEARCH_STALE_FALLBACK_TTL_SECONDS:
        return None
    cached_payload = dict(cached.get("payload", {}) or {})
    if not cached_payload.get("ds_completed"):
        return None
    if str(failed_payload.get("provider_resolved") or failed_payload.get("provider_target") or "") != "deepseek":
        return None
    if failed_payload.get("ds_completed"):
        return None
    live_fallback_reason = str(
        failed_payload.get("fallback_reason")
        or failed_payload.get("display_status_zh")
        or failed_payload.get("runtime_notice_zh")
        or "本轮 DS 请求失败。"
    )
    reused = dict(cached_payload)
    reused.update(
        {
            "cache_status": "stale_ds_hit",
            "cache_status_zh": "本轮 DS 请求失败，已复用最近一次 DS 研究结果。",
            "cache_age_seconds": round(age_seconds, 2),
            "reused_from_cached_ds": True,
            "research_source": "deepseek_cache",
            "research_source_zh": "已复用最近一次 DS 研究结果",
            "ds_status": "cached",
            "ds_status_zh": "已复用最近一次 DS 研究",
            "ds_attempted": True,
            "ds_completed": True,
            "ds_error_code": str(failed_payload.get("ds_error_code") or ""),
            "display_status_zh": "本轮 DS 请求失败，已复用最近一次 DS 研究结果。",
            "fallback_reason": live_fallback_reason,
            "runtime_notice_zh": "本轮 DS 请求失败，已复用最近一次成功的 DS 研究结果。",
            "next_step_zh": "当前可先查看缓存研究；如需最新解释，可稍后刷新，若持续失败请检查 Key、额度或网络。",
            "live_attempt": {
                "ds_status": failed_payload.get("ds_status"),
                "ds_status_zh": failed_payload.get("ds_status_zh"),
                "ds_attempted": failed_payload.get("ds_attempted"),
                "ds_completed": failed_payload.get("ds_completed"),
                "ds_error_code": failed_payload.get("ds_error_code"),
                "token_in": failed_payload.get("token_in"),
                "token_out": failed_payload.get("token_out"),
                "token_total": failed_payload.get("token_total"),
                "fallback_reason": live_fallback_reason,
            },
        }
    )
    update_runtime_status(
        provider_requested=str(reused.get("provider_requested") or "auto"),
        provider_target=str(reused.get("provider_target") or "deepseek"),
        provider_resolved="deepseek",
        ds_status="cached",
        ds_status_zh="已复用最近一次 DS 研究",
        ds_attempted=True,
        ds_completed=True,
        ds_error_code=str(failed_payload.get("ds_error_code") or ""),
        fallback_reason=live_fallback_reason,
        token_in=reused.get("token_in"),
        token_out=reused.get("token_out"),
        token_total=reused.get("token_total"),
    )
    return reused


def _run_ai_combo_optimizer_from_query(query: dict[str, str]) -> dict:
    if query.get("date"):
        return _run_optimizer_from_query(query)
    preview = _run_next_available_from_query(query)
    result = _optimizer_result_from_preview(preview, query)
    result["date"] = preview.get("selected_date") or preview.get("date")
    result["selected_date"] = preview.get("selected_date") or preview.get("date")
    result["next_available_locked"] = True
    result["date_lock_zh"] = "AI 研究已锁定到 App 自动选中的 T+1/T+N 日期，避免解释对象与首页不一致。"
    return result


def _optimizer_result_from_preview(preview: dict, query: dict[str, str]) -> dict:
    result = dict(preview.get("optimizer", {}))
    learning_panel = build_home_learning_panel()
    result.update({
        "provider": preview.get("provider", query.get("provider", "auto")),
        "provider_used": preview.get("provider_used"),
        "date": preview.get("date") or preview.get("selected_date") or query.get("date"),
        "selected_date": preview.get("selected_date") or preview.get("date") or query.get("date"),
        "matches_analyzed": preview.get("matches_count", 0),
        "candidate_pool_count": len(preview.get("optimizer_candidates", []) or []),
        "top_total_goals_observations": preview.get("top_total_goals_observations", []),
        "top_score_observations": preview.get("top_score_observations", []),
        "missing_signals": preview.get("missing_signals", []),
        "credibility_gate": preview.get("credibility_gate", {}),
        "credibility_audit": preview.get("credibility_audit", {}),
        "external_signals_status": preview.get("external_signals_status", {}),
        "learning_panel": learning_panel,
        "daily_learning_metrics": learning_panel.get("daily_metrics", []),
        "window_learning_metrics": learning_panel.get("window_metrics", []),
        "latest_daily_summary_zh": learning_panel.get("latest_daily_summary_zh", ""),
        "window_learning_summaries_zh": learning_panel.get("window_summaries_zh", []),
        "daily_learning_digest": learning_panel.get("daily_digest", {}),
        "window_learning_digests": learning_panel.get("window_digests", []),
        "llm_status": llm_status_payload(),
        "warnings": list(dict.fromkeys(list(result.get("warnings", []) or []) + list(preview.get("warnings", []) or []))),
    })
    result["trader_review"] = build_trader_review(preview, result)
    return result


def _run_operation_from_query(query: dict[str, str]) -> dict:
    historical_data = _required(query, "historical_data")
    matches, warnings = load_historical_matches_with_warnings(historical_data)
    if not matches:
        raise ApiError("validation_error", "未能读取可用历史比赛。请检查 CSV 路径、字段和比分信息。")
    report = run_paper_operation_walkforward(
        matches,
        initial_bankroll=_float_param(query, "initial_bankroll", 10000.0),
        start_date=query.get("start_date"),
        end_date=query.get("end_date"),
        strategy_config={
            "max_single_per_day": _int_param(query, "max_single_per_day", 2),
            "max_parlay_2x1_per_day": _int_param(query, "max_parlay_2x1_per_day", 1),
            "max_parlay_3x1_per_day": 1 if _truthy(query.get("enable_3x1")) else 0,
        },
    )
    report["warnings"] = list(dict.fromkeys(list(warnings or []) + list(report.get("warnings", []) or [])))
    return report

def _run_backtest_from_query(query: dict[str, str]) -> dict:
    historical_data = _required(query, "historical_data")
    matches, warnings = load_historical_matches_with_warnings(historical_data)
    data_summary = validate_historical_dataset(matches)
    result = run_backtest(
        matches,
        start_date=query.get("start_date"),
        end_date=query.get("end_date"),
        min_train_matches=_int_param(query, "min_train_matches", 20),
        strategy_config={
            "min_ev": _float_param(query, "min_ev", 0.04),
            "min_edge": _float_param(query, "min_edge", 0.025),
        },
    )
    result["data_summary"] = data_summary
    result["warnings"] = list(dict.fromkeys(warnings + data_summary.get("warnings", []) + result.get("warnings", [])))
    return build_backtest_report(result)


def _reject_write_params(query: dict[str, str], names: set[str]) -> None:
    for name in names:
        if name in query:
            ensure_read_only_operation(name, write_requested=True)


def _validate_calibration_from_query(query: dict[str, str]) -> dict:
    artifact_path = _required(query, "path")
    try:
        artifact = load_calibration_artifact(artifact_path)
        issues = validate_calibration_artifact(artifact)
        return {"path": artifact_path, "valid": not issues, "issues": issues}
    except Exception as exc:
        return {"path": artifact_path, "valid": False, "issues": [str(exc)[:180]]}


def _attach_field_guidance(payload: dict) -> None:
    field_report = build_field_recognition_report(payload.get("preview", {}).get("columns", []), payload.get("mapping", {}))
    payload["field_report"] = field_report
    payload["repair_suggestions"] = build_repair_suggestions(field_report)
    payload["warnings"] = list(dict.fromkeys(list(payload.get("warnings", []) or []) + list(field_report.get("warnings", []) or [])))


def _required(query: dict[str, str], name: str) -> str:
    value = query.get(name)
    if not value:
        raise ApiError("bad_request", f"missing required parameter: {name}")
    return value


def _int_param(query: dict[str, str], name: str, default: int) -> int:
    try:
        return int(query.get(name, default))
    except ValueError as exc:
        raise ApiError("validation_error", f"{name} must be an integer") from exc


def _float_param(query: dict[str, str], name: str, default: float) -> float:
    try:
        return float(query.get(name, default))
    except ValueError as exc:
        raise ApiError("validation_error", f"{name} must be a number") from exc


def _truthy(value: str | None) -> bool:
    return str(value or "").lower() in {"1", "true", "yes", "on"}

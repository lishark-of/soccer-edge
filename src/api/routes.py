from __future__ import annotations

from src.api.errors import ApiError
from src.api.read_only import ensure_read_only_operation
from src.api.schemas import success_response
from src.application import build_analysis_payload, build_matches_payload
from src.backtesting.backtest_engine import run_backtest
from src.backtesting.historical_loader import load_historical_matches_with_warnings
from src.backtesting.report import build_backtest_report
from src.backtesting.schema import validate_historical_dataset
from src.calibration.persistence import load_calibration_artifact
from src.calibration.store import validate_calibration_artifact
from src.explain.deepseek_config import llm_status_payload
from src.explain.deepseek_explainer import explain_with_optional_deepseek
from src.exports.report_exporter import summarize_report
from src.ingestion.importer import import_historical_file
from src.release.metadata import build_release_metadata
from src.version import get_build_info
from src.view_models.analysis_view import build_analysis_view
from src.view_models.backtest_view import build_backtest_view
from src.view_models.calibration_view import build_calibration_view
from src.view_models.import_view import build_import_preview_view
from src.view_models.qa_view import build_qa_view


VERSION = "0.1.0-local"
DISABLED_CAPABILITIES = ["betting", "payment", "order_placement", "proxy_purchase", "automation"]


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
                    "view_import_preview",
                    "view_calibration_validate",
                    "view_qa",
                    "llm_status",
                    "explain_candidate",
                ],
                "disabled_capabilities": DISABLED_CAPABILITIES,
                "version": metadata["version"],
                "release_phase": metadata["release_phase"],
                "disclaimer": "For research and entertainment reference only. No betting, payment, or order placement.",
            }
        )
    if path == "/api/llm/status":
        return success_response(llm_status_payload())
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
        return success_response(payload, payload.get("warnings", []))
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
        view = build_backtest_view(_run_backtest_from_query(query))
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/import/preview":
        _reject_write_params(query, {"output"})
        payload = import_historical_file(
            input_path=_required(query, "input"),
            adapter_name=query.get("adapter", "auto"),
            mapping_path=query.get("mapping"),
            dry_run=True,
        )
        view = build_import_preview_view(payload)
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/calibration/validate":
        view = build_calibration_view(_validate_calibration_from_query(query))
        return success_response(view, view.get("warnings", []))
    if path == "/api/view/qa":
        from src.qa.runner import run_qa

        view = build_qa_view(run_qa(project_root=".", rehearsal=_truthy(query.get("rehearsal"))))
        return success_response(view, view.get("warnings", []))
    raise ApiError("not_found", f"unknown endpoint: {path}", status=404)


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

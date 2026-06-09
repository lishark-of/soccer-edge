from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.backtesting.historical_loader import load_historical_matches_with_warnings
from src.calibration.persistence import load_calibration_artifact
from src.calibration.store import validate_calibration_artifact
from src.domain.analysis_result import DailyAnalysisReport
from src.exports.csv_exporter import export_analysis_csv
from src.exports.report_exporter import export_report_to_markdown
from src.exports.xlsx_exporter import export_analysis_xlsx
from src.providers.base import ProviderError
from src.providers.factory import create_provider
from src.strategy.portfolio_builder import HISTORICAL_FIXTURE_WARNING, MODEL_VERSION, build_daily_analysis


DISCLAIMER_BLOCK = [
    "仅供数据研究与娱乐参考",
    "概率模型不保证结果",
    "串关会显著放大风险",
    "请勿投入无法承受损失的资金",
]
FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "historical_matches_sample.csv"


def default_target_date() -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    return (now + timedelta(days=1)).date().isoformat()


def build_analysis_payload(
    target_date: str | None = None,
    provider_name: str = "auto",
    export_format: str | None = None,
    historical_data_path: str | None = None,
    use_fixture_historical: bool = True,
    calibration_artifact_path: str | None = None,
    report_markdown_path: str | None = None,
) -> dict[str, object]:
    date = target_date or default_target_date()
    provider = create_provider(provider_name)
    calibration_status, calibration_warnings = _resolve_calibration_artifact(calibration_artifact_path)
    historical_matches, historical_status, historical_warnings = _resolve_historical_inputs(
        historical_data_path=historical_data_path,
        use_fixture_historical=use_fixture_historical,
    )
    try:
        report = build_daily_analysis(
            provider,
            date,
            historical_matches=historical_matches,
            historical_data_status=historical_status,
            historical_warnings=historical_warnings,
        )
    except Exception as exc:
        _record_provider_warning(provider, provider_name, exc)
        report = _empty_report(date, historical_status)
        report.warnings.extend(historical_warnings)
    report.warnings.extend(calibration_warnings)
    payload = report.to_dict()
    payload.update(_provider_meta(provider, provider_name))
    payload["calibration_status"] = calibration_status
    if export_format == "csv":
        payload["export_file"] = str(export_analysis_csv(report))
    elif export_format == "xlsx":
        payload["export_file"] = str(export_analysis_xlsx(report))
    if report_markdown_path:
        try:
            payload["report_markdown_path"] = export_report_to_markdown(payload, report_markdown_path)
        except Exception as exc:
            payload.setdefault("warnings", []).append(f"markdown report export failed: {_short_error(exc)}")
    return payload


def build_matches_payload(target_date: str | None = None, provider_name: str = "auto") -> dict[str, object]:
    date = target_date or default_target_date()
    provider = create_provider(provider_name)
    try:
        matches = [match.to_dict() for match in provider.get_matches(date)]
    except Exception as exc:
        _record_provider_warning(provider, provider_name, exc)
        matches = []
    payload = {
        "date": date,
        "matches": matches,
    }
    payload.update(_provider_meta(provider, provider_name))
    return payload


def build_match_odds_payload(
    match_id: str,
    target_date: str | None = None,
    provider_name: str = "auto",
) -> dict[str, object]:
    date = target_date or default_target_date()
    provider = create_provider(provider_name)
    odds_payload = None
    try:
        provider.get_matches(date)
        odds_payload = provider.get_match_odds(match_id).to_dict()
    except Exception as exc:
        _record_provider_warning(provider, provider_name, exc)
    payload = {
        "date": date,
        "match_id": match_id,
        "odds": odds_payload,
    }
    payload.update(_provider_meta(provider, provider_name))
    return payload


def build_odds_history_payload(
    match_id: str,
    target_date: str | None = None,
    provider_name: str = "auto",
) -> dict[str, object]:
    date = target_date or default_target_date()
    provider = create_provider(provider_name)
    history_payload = None
    try:
        provider.get_matches(date)
        history_payload = provider.get_odds_history(match_id).to_dict()
    except Exception as exc:
        _record_provider_warning(provider, provider_name, exc)
    payload = {
        "date": date,
        "match_id": match_id,
        "odds_history": history_payload,
    }
    payload.update(_provider_meta(provider, provider_name))
    return payload


def _resolve_historical_inputs(
    *,
    historical_data_path: str | None,
    use_fixture_historical: bool,
) -> tuple[list, str, list[str]]:
    if historical_data_path:
        matches, warnings = load_historical_matches_with_warnings(historical_data_path)
        if matches:
            return matches, "loaded", warnings
        return [], "unavailable", warnings or [f"historical data unavailable: {historical_data_path}"]
    if not use_fixture_historical:
        return [], "disabled", []
    matches, warnings = load_historical_matches_with_warnings(str(FIXTURE_PATH))
    if matches:
        return matches, "fixture", warnings
    fallback_warnings = [f"fixture historical data unavailable: {FIXTURE_PATH}"]
    fallback_warnings.extend(warnings)
    return [], "unavailable", fallback_warnings


def _resolve_calibration_artifact(path: str | None) -> tuple[str, list[str]]:
    if not path:
        return "not_provided", []
    try:
        artifact = load_calibration_artifact(path)
    except Exception as exc:
        return "invalid", [f"calibration artifact unavailable: {_short_error(exc)}"]
    issues = validate_calibration_artifact(artifact)
    if issues:
        return "invalid", [f"calibration artifact invalid: {'; '.join(issues)}"]
    return "loaded", []


def _provider_meta(provider, requested: str) -> dict[str, object]:
    warnings = list(dict.fromkeys(list(getattr(provider, "warnings", [])) + list(getattr(provider, "messages", []))))
    provider_used = getattr(
        provider,
        "provider_used",
        getattr(provider, "resolved_provider_name", getattr(provider, "provider_name", getattr(provider, "name", requested))),
    )
    return {
        "provider": requested,
        "provider_requested": requested,
        "provider_used": provider_used,
        "fallback_used": bool(getattr(provider, "fallback_used", False)),
        "provider_warnings": warnings,
    }


def _record_provider_warning(provider, requested: str, exc: Exception) -> None:
    existing = getattr(provider, "warnings", None)
    if existing is None:
        existing = []
        setattr(provider, "warnings", existing)
    if getattr(provider, "provider_name", requested) == "auto":
        if not existing:
            existing.append(f"auto provider failed: {_short_error(exc)}")
        return
    provider_name = getattr(provider, "provider_name", getattr(provider, "name", requested))
    message = f"{provider_name} provider failed: {_short_error(exc)}"
    if message not in existing:
        existing.append(message)
    messages = getattr(provider, "messages", None)
    if isinstance(messages, list) and message not in messages:
        messages.append(message)


def _empty_report(date: str, historical_status: str) -> DailyAnalysisReport:
    components = ["market", "poisson", "elo"] if historical_status in {"fixture", "loaded"} else ["market"]
    return DailyAnalysisReport(
        date=date,
        matches_analyzed=0,
        disclaimers=list(DISCLAIMER_BLOCK),
        model_version=MODEL_VERSION,
        model_components_available=components,
        historical_data_status=historical_status,
    )


def _short_error(exc: Exception) -> str:
    if isinstance(exc, ProviderError):
        text = str(exc)
    else:
        text = str(exc)
    text = text.strip().replace("\n", " ")
    return text[:180] or exc.__class__.__name__

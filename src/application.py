from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.domain.analysis_result import DailyAnalysisReport
from src.exports.csv_exporter import export_analysis_csv
from src.exports.xlsx_exporter import export_analysis_xlsx
from src.providers.base import ProviderError
from src.providers.factory import create_provider
from src.strategy.portfolio_builder import build_daily_analysis


DISCLAIMER_BLOCK = [
    "仅供数据研究与娱乐参考",
    "概率模型不保证结果",
    "串关会显著放大风险",
    "请勿投入无法承受损失的资金",
]


def default_target_date() -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    return (now + timedelta(days=1)).date().isoformat()


def build_analysis_payload(
    target_date: str | None = None,
    provider_name: str = "auto",
    export_format: str | None = None,
) -> dict[str, object]:
    date = target_date or default_target_date()
    provider = create_provider(provider_name)
    try:
        report = build_daily_analysis(provider, date)
    except Exception as exc:
        _record_provider_warning(provider, provider_name, exc)
        report = _empty_report(date)
    payload = report.to_dict()
    payload.update(_provider_meta(provider, provider_name))
    if export_format == "csv":
        payload["export_file"] = str(export_analysis_csv(report))
    elif export_format == "xlsx":
        payload["export_file"] = str(export_analysis_xlsx(report))
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


def _empty_report(date: str) -> DailyAnalysisReport:
    return DailyAnalysisReport(
        date=date,
        matches_analyzed=0,
        disclaimers=list(DISCLAIMER_BLOCK),
    )


def _short_error(exc: Exception) -> str:
    if isinstance(exc, ProviderError):
        text = str(exc)
    else:
        text = str(exc)
    text = text.strip().replace("\n", " ")
    return text[:180] or exc.__class__.__name__

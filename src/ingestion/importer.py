from __future__ import annotations

from csv import DictWriter
from pathlib import Path

from src.backtesting.historical_loader import HistoricalMatch, normalize_historical_row
from src.ingestion.adapters.football_data_adapter import FootballDataAdapter
from src.ingestion.adapters.generic_csv_adapter import GenericCsvAdapter
from src.ingestion.adapters.sporttery_export_adapter import SportteryExportAdapter
from src.ingestion.field_mapping import infer_field_mapping, load_field_mapping, normalize_row_with_mapping
from src.ingestion.manifest import build_import_manifest
from src.ingestion.quality import build_quality_report


ADAPTERS = [SportteryExportAdapter(), FootballDataAdapter(), GenericCsvAdapter()]
ADAPTER_BY_NAME = {adapter.name: adapter for adapter in ADAPTERS}


def import_historical_file(
    input_path: str,
    adapter_name: str | None = None,
    mapping_path: str | None = None,
    output_path: str | None = None,
    dry_run: bool = False,
) -> dict:
    warnings: list[str] = []
    adapter = _choose_adapter(input_path, adapter_name)
    rows = adapter.load_rows(input_path)
    preview = adapter.preview(input_path)
    mapping = load_field_mapping(mapping_path) if mapping_path else infer_field_mapping(preview.get("columns", []))
    matches: list[HistoricalMatch] = []
    normalized_rows: list[dict] = []
    skipped_rows: list[dict] = []
    for index, row in enumerate(rows, start=1):
        try:
            normalized_row = normalize_row_with_mapping(row, mapping)
            match = normalize_historical_row(normalized_row)
            matches.append(match)
            normalized_rows.append(_match_to_row(match))
        except ValueError as exc:
            skipped_rows.append({"row": index, "reason": str(exc)})
    quality = build_quality_report(matches, skipped_rows)
    warnings.extend(quality.get("warnings", []))
    final_output = output_path
    if not dry_run:
        if final_output is None:
            final_output = str(Path("data/normalized") / f"{Path(input_path).stem}_normalized.csv")
        _write_normalized_csv(normalized_rows, final_output)
    else:
        final_output = None
    manifest = build_import_manifest(
        input_path=input_path,
        adapter=adapter.name,
        rows_read=len(rows),
        rows_normalized=len(matches),
        rows_skipped=len(skipped_rows),
        output_path=final_output,
        warnings=warnings,
    )
    return {
        "input_path": input_path,
        "adapter": adapter.name,
        "dry_run": dry_run,
        "rows_read": len(rows),
        "rows_normalized": len(matches),
        "rows_skipped": len(skipped_rows),
        "output_path": final_output,
        "quality": quality,
        "manifest": manifest,
        "mapping": mapping,
        "preview": preview,
        "warnings": warnings,
    }


def _choose_adapter(path: str, adapter_name: str | None):
    requested = adapter_name or "auto"
    if requested != "auto":
        if requested not in ADAPTER_BY_NAME:
            raise ValueError(f"unknown adapter: {requested}")
        adapter = ADAPTER_BY_NAME[requested]
        if not adapter.can_handle(path):
            raise ValueError(f"{requested} cannot handle {path}")
        return adapter
    for adapter in ADAPTERS:
        if adapter.can_handle(path):
            return adapter
    raise ValueError(f"no adapter can handle {path}")


def _write_normalized_csv(rows: list[dict], output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "league", "home_team", "away_team", "home_goals", "away_goals", "result_1x2", "half_time_score", "odds_home", "odds_draw", "odds_away"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return str(path)


def _match_to_row(match: HistoricalMatch) -> dict:
    odds = match.odds_had or {}
    return {
        "date": match.date,
        "league": match.league,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "home_goals": match.home_goals,
        "away_goals": match.away_goals,
        "result_1x2": match.result_1x2,
        "half_time_score": match.half_time_score or "",
        "odds_home": odds.get("win", ""),
        "odds_draw": odds.get("draw", ""),
        "odds_away": odds.get("lose", ""),
    }

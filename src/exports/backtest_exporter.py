from __future__ import annotations

from csv import DictWriter
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


def export_backtest_to_csv(report: dict, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bets = report.get("bets", [])
    fields = ["date", "league", "home_team", "away_team", "selection", "actual", "odds", "model_prob", "market_prob", "edge", "ev", "stake", "hit", "profit"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for bet in bets:
            writer.writerow({field: bet.get(field, "") for field in fields})
    return str(path)


def export_backtest_to_xlsx(report: dict, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheets = {
        "Summary": [["field", "value"], ["model_version", report.get("model_version", "")], ["matches_evaluated", report.get("matches_evaluated", 0)], ["bets_total", report.get("bets_total", 0)], ["disclaimer", report.get("disclaimer", "")]],
        "Metrics": [["metric", "value"]] + [[key, value] for key, value in report.get("metrics", {}).items() if key != "warnings"],
        "Bets": _bets_rows(report.get("bets", [])),
        "Calibration": _calibration_rows(report.get("calibration", {})),
    }
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml(len(sheets)))
        archive.writestr("_rels/.rels", RELS_XML)
        archive.writestr("xl/workbook.xml", _workbook_xml(list(sheets)))
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml(len(sheets)))
        for index, rows in enumerate(sheets.values(), start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(rows))
    return str(path)


def _bets_rows(bets: list[dict]) -> list[list[object]]:
    fields = ["date", "league", "home_team", "away_team", "selection", "actual", "odds", "model_prob", "market_prob", "edge", "ev", "stake", "hit", "profit"]
    return [fields] + [[bet.get(field, "") for field in fields] for bet in bets]


def _calibration_rows(calibration: dict) -> list[list[object]]:
    rows = [["outcome", "bin_start", "bin_end", "count", "avg_predicted_prob", "observed_frequency", "gap"]]
    for outcome, bins in calibration.get("bins", {}).items():
        for item in bins:
            rows.append([outcome, item["bin_start"], item["bin_end"], item["count"], item["avg_predicted_prob"], item["observed_frequency"], item["gap"]])
    return rows


def _sheet_xml(rows: list[list[object]]) -> str:
    body = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            ref = f"{_column_name(column_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        body.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(body) + "</sheetData></worksheet>"


def _column_name(index: int) -> str:
    name = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _content_types_xml(sheet_count: int) -> str:
    overrides = "".join(f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for index in range(1, sheet_count + 1))
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' + overrides + "</Types>"


def _workbook_xml(names: list[str]) -> str:
    sheets = "".join(f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>' for index, name in enumerate(names, start=1))
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + sheets + "</sheets></workbook>"


def _workbook_rels_xml(sheet_count: int) -> str:
    rels = "".join(f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>' for index in range(1, sheet_count + 1))
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + rels + "</Relationships>"


RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""

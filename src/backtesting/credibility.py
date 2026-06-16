from __future__ import annotations

import csv
from datetime import date
from pathlib import Path


DISCLAIMER = "回测可信度只评估数据质量，不保证未来表现。"
REQUIRED_RESULT_FIELDS = {"home_goals", "away_goals"}
ODDS_FIELDS = {"odds_home", "odds_draw", "odds_away"}


def build_backtest_credibility_report(
    input_path: str | Path,
    source_type: str = "user_csv",
) -> dict:
    path = Path(input_path)
    if not path.exists():
        return _error("file_missing", f"文件不存在：{path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            fieldnames = list(reader.fieldnames or [])
    except Exception as exc:
        return _error("csv_read_error", f"CSV 读取失败：{str(exc)[:120]}")
    return build_backtest_credibility_from_rows(rows, fieldnames, source_type=source_type, input_path=str(path))


def build_backtest_credibility_from_rows(
    rows: list[dict],
    fieldnames: list[str] | None = None,
    source_type: str = "user_csv",
    input_path: str | None = None,
) -> dict:
    fields = set(fieldnames or _collect_fields(rows))
    row_count = len(rows or [])
    odds_coverage = _coverage(rows, ODDS_FIELDS)
    result_coverage = _coverage(rows, REQUIRED_RESULT_FIELDS)
    date_span = _date_span(rows)
    source_cap = _source_cap(source_type)
    score = 0
    reasons = []
    if row_count >= 1000:
        score += 25
        reasons.append("样本量较充足。")
    elif row_count >= 300:
        score += 18
        reasons.append("样本量中等。")
    elif row_count >= 80:
        score += 10
        reasons.append("样本量偏少，只适合初步复盘。")
    else:
        score += 4
        reasons.append("样本量很少，可信度较低。")
    score += round(25 * odds_coverage)
    score += round(20 * result_coverage)
    if date_span.get("days", 0) >= 180:
        score += 15
        reasons.append("时间跨度较长。")
    elif date_span.get("days", 0) >= 30:
        score += 8
        reasons.append("时间跨度有限。")
    else:
        reasons.append("时间跨度不足，容易受短期波动影响。")
    if {"league", "home_team", "away_team"}.issubset(fields):
        score += 10
    else:
        reasons.append("联赛或球队字段不完整。")
    if odds_coverage < 0.9:
        reasons.append("赔率字段覆盖不足，会影响 EV/CLV/模拟走盘复盘。")
    if result_coverage < 0.95:
        reasons.append("赛果字段覆盖不足，会影响命中率与回测结算。")
    capped = min(score, source_cap)
    return {
        "credibility_version": "phase2r_backtest_data_v0",
        "input_path": input_path,
        "source_type": source_type,
        "row_count": row_count,
        "odds_coverage": round(odds_coverage, 4),
        "result_coverage": round(result_coverage, 4),
        "date_span": date_span,
        "score": capped,
        "grade": _grade(capped),
        "confidence_level_zh": _level(capped),
        "source_cap": source_cap,
        "reasons": reasons,
        "next_steps": _next_steps(row_count, odds_coverage, result_coverage, date_span),
        "disclaimer": DISCLAIMER,
    }


def _collect_fields(rows: list[dict]) -> list[str]:
    fields = set()
    for row in rows or []:
        fields.update(row.keys())
    return sorted(fields)


def _coverage(rows: list[dict], fields: set[str]) -> float:
    if not rows:
        return 0.0
    ok = 0
    for row in rows:
        if all(str(row.get(field, "")).strip() for field in fields):
            ok += 1
    return ok / len(rows)


def _date_span(rows: list[dict]) -> dict:
    parsed = []
    for row in rows or []:
        raw = str(row.get("date") or row.get("比赛日期") or "").strip()
        try:
            parsed.append(date.fromisoformat(raw[:10]))
        except ValueError:
            continue
    if len(parsed) < 2:
        return {"start": None, "end": None, "days": 0}
    start = min(parsed)
    end = max(parsed)
    return {"start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days + 1}


def _source_cap(source_type: str) -> int:
    source = str(source_type or "").lower()
    if source in {"fixture", "mock", "sample"}:
        return 60
    if source in {"user_csv", "user"}:
        return 85
    if source in {"verified_market", "real_historical_odds"}:
        return 95
    return 75


def _grade(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def _level(score: int) -> str:
    if score >= 80:
        return "高"
    if score >= 65:
        return "中高"
    if score >= 50:
        return "中"
    return "低"


def _next_steps(row_count: int, odds_coverage: float, result_coverage: float, span: dict) -> list[str]:
    steps = []
    if row_count < 300:
        steps.append("补充更多历史比赛，至少覆盖多个联赛和更长时间段。")
    if odds_coverage < 0.9:
        steps.append("补齐胜/平/负赔率字段，提升 EV 和模拟走盘可信度。")
    if result_coverage < 0.95:
        steps.append("补齐主客队进球或比分字段，确保回测可结算。")
    if span.get("days", 0) < 180:
        steps.append("尽量覆盖 6 个月以上历史数据，降低短期样本偏差。")
    return steps or ["当前数据可用于较稳健回测，但仍需持续复盘 CLV 和样本外表现。"]


def _error(code: str, message: str) -> dict:
    return {
        "credibility_version": "phase2r_backtest_data_v0",
        "status": "error",
        "error_code": code,
        "message_zh": message,
        "score": 0,
        "grade": "D",
        "confidence_level_zh": "低",
        "disclaimer": DISCLAIMER,
    }


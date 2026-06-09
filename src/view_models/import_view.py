from __future__ import annotations

from src.explain.safety import DISCLAIMER_TEXT


def build_import_preview_view(import_result: dict) -> dict:
    quality = import_result.get("quality", {}) or {}
    manifest = import_result.get("manifest", {}) or {}
    return {
        "title": "数据导入预检",
        "summary_cards": [
            {"label": "Adapter", "value": import_result.get("adapter", "unknown"), "help": "本地文件读取适配器。"},
            {"label": "读取行数", "value": import_result.get("rows_read", 0), "help": "原始文件读取到的记录数。"},
            {"label": "标准化行数", "value": import_result.get("rows_normalized", 0), "help": "可转为统一历史比赛结构的记录数。"},
            {"label": "跳过行数", "value": import_result.get("rows_skipped", 0), "help": "字段缺失或无法解析的记录数。"},
            {"label": "赔率覆盖", "value": _pct((quality.get("odds_coverage") or {}).get("had")), "help": "胜平负赔率可用比例。"},
            {"label": "Dry-run", "value": str(import_result.get("dry_run", True)), "help": "预检模式不会写 normalized 文件。"},
        ],
        "quality": quality,
        "field_report": import_result.get("field_report", {}) or {},
        "repair_suggestions": import_result.get("repair_suggestions", []) or [],
        "manifest_summary": {
            "input_sha256": manifest.get("input_sha256"),
            "created_at": manifest.get("created_at"),
            "output_path": manifest.get("output_path"),
        },
        "preview_rows": list(import_result.get("preview", {}).get("sample_rows", []) or []),
        "warnings": list(import_result.get("warnings", []) or []) + list(quality.get("warnings", []) or []),
        "disclaimer": DISCLAIMER_TEXT,
    }


def _pct(value):
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"

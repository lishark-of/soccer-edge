from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.application import build_analysis_payload, default_target_date
from src.backtesting.backtest_engine import run_backtest
from src.backtesting.historical_loader import load_historical_matches_with_warnings
from src.backtesting.report import build_backtest_report
from src.backtesting.schema import validate_historical_dataset
from src.calibration.persistence import save_calibration_artifact
from src.calibration.store import build_calibration_artifact
from src.exports.report_exporter import export_report_to_markdown
from src.ingestion.field_report import build_field_recognition_report
from src.ingestion.importer import import_historical_file
from src.ingestion.repair_suggestions import build_repair_suggestions
from src.view_models.user_workflow_view import build_user_workflow_view

WORKFLOW_VERSION = "phase2j_user_data_workflow_v0"
DISCLAIMER = "仅供数据研究与娱乐参考。概率模型不保证结果。回测结果不保证未来表现。串关会显著放大风险。不提供投注、下单、支付、代购或任何自动化购彩能力。"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="用户历史 CSV 入门流程：字段识别、标准化、回测、校准、分析")
    parser.add_argument("--input", required=True)
    parser.add_argument("--mapping", default=None)
    parser.add_argument("--output-dir", default="data/normalized/user_workflow")
    parser.add_argument("--date", default=None)
    parser.add_argument("--provider", default="mock", choices=["mock", "auto", "sporttery"])
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--write-report", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_user_data_workflow(
        input_path=args.input,
        mapping_path=args.mapping,
        output_dir=args.output_dir,
        target_date=args.date,
        provider=args.provider,
        write_report=args.write_report,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 0 if result.get("overall_status") != "error" else 1


def run_user_data_workflow(
    input_path: str,
    mapping_path: str | None = None,
    output_dir: str = "data/normalized/user_workflow",
    target_date: str | None = None,
    provider: str = "mock",
    write_report: str | None = None,
) -> dict:
    warnings: list[str] = []
    normalized_path = str(Path(output_dir) / f"{Path(input_path).stem}_normalized.csv")
    calibration_path = str(Path("artifacts/calibration") / f"{Path(input_path).stem}_calibration.json")
    try:
        dry_run = import_historical_file(input_path=input_path, mapping_path=mapping_path, dry_run=True)
        field_report = build_field_recognition_report(dry_run.get("preview", {}).get("columns", []), dry_run.get("mapping", {}))
        repair_suggestions = build_repair_suggestions(field_report)
        warnings.extend(_zh_warnings(dry_run.get("warnings", [])))
        if field_report.get("missing_required_fields"):
            return _finalize(
                input_path,
                mapping_path,
                field_report,
                repair_suggestions,
                normalized_path=None,
                backtest_report={},
                calibration_path=None,
                analysis={},
                warnings=warnings,
                write_report=write_report,
                overall_status="error",
            )
        imported = import_historical_file(input_path=input_path, mapping_path=mapping_path, output_path=normalized_path, dry_run=False)
        warnings.extend(_zh_warnings(imported.get("warnings", [])))
        matches, loader_warnings = load_historical_matches_with_warnings(normalized_path)
        warnings.extend(_zh_warnings(loader_warnings))
        data_summary = validate_historical_dataset(matches)
        backtest_result = run_backtest(matches, min_train_matches=20)
        backtest_result["data_summary"] = data_summary
        backtest_result["warnings"] = list(dict.fromkeys(_zh_warnings(data_summary.get("warnings", [])) + _zh_warnings(backtest_result.get("warnings", []))))
        backtest_report = build_backtest_report(backtest_result)
        artifact = build_calibration_artifact(backtest_report, backtest_report.get("model_version", "unknown"))
        save_calibration_artifact(artifact, calibration_path)
        analysis = build_analysis_payload(
            target_date=target_date or default_target_date(),
            provider_name=provider,
            historical_data_path=normalized_path,
            calibration_artifact_path=calibration_path,
            use_fixture_historical=False,
        )
        return _finalize(
            input_path,
            mapping_path,
            field_report,
            repair_suggestions,
            normalized_path=normalized_path,
            backtest_report=backtest_report,
            calibration_path=calibration_path,
            analysis=analysis,
            warnings=warnings,
            write_report=write_report,
            overall_status="success",
        )
    except Exception as exc:
        field_report = {"recognized_fields": [], "missing_required_fields": [], "warnings": [_friendly_error(exc)], "confidence": "low"}
        return _finalize(
            input_path,
            mapping_path,
            field_report,
            build_repair_suggestions(field_report),
            normalized_path=None,
            backtest_report={},
            calibration_path=None,
            analysis={},
            warnings=[_friendly_error(exc)],
            write_report=write_report,
            overall_status="error",
        )


def preview_user_data_workflow(input_path: str, mapping_path: str | None = None) -> dict:
    try:
        dry_run = import_historical_file(input_path=input_path, mapping_path=mapping_path, dry_run=True)
        field_report = build_field_recognition_report(dry_run.get("preview", {}).get("columns", []), dry_run.get("mapping", {}))
        repair_suggestions = build_repair_suggestions(field_report)
        result = {
            "workflow_version": WORKFLOW_VERSION,
            "overall_status": "preview",
            "input_path": input_path,
            "field_report": field_report,
            "repair_suggestions": repair_suggestions,
            "preflight_quality": _preflight_quality(dry_run, field_report),
            "normalized_output_path": None,
            "backtest": {},
            "calibration_artifact_path": None,
            "analysis": {},
            "workflow_summary": _workflow_summary("preview", None, None, {}, {}),
            "backtest_explanation": _backtest_explanation("preview", {}),
            "calibration_explanation": _calibration_explanation(None),
            "data_quality_notes": _data_quality_notes(field_report, {}),
            "cli_handoff": _cli_handoff(input_path, mapping_path, None, None),
            "next_steps": _next_steps("error" if field_report.get("missing_required_fields") else "preview", field_report, None, None),
            "warnings": list(dict.fromkeys(_zh_warnings(dry_run.get("warnings", [])) + field_report.get("warnings", []))),
            "disclaimer": DISCLAIMER,
        }
        result["user_view"] = build_user_workflow_view(result)
        return result
    except Exception as exc:
        field_report = {"recognized_fields": [], "missing_required_fields": [], "warnings": [_friendly_error(exc)], "confidence": "low"}
        result = {
            "workflow_version": WORKFLOW_VERSION,
            "overall_status": "error",
            "input_path": input_path,
            "field_report": field_report,
            "repair_suggestions": build_repair_suggestions(field_report),
            "preflight_quality": _preflight_quality({}, field_report),
            "normalized_output_path": None,
            "backtest": {},
            "calibration_artifact_path": None,
            "analysis": {},
            "workflow_summary": _workflow_summary("error", None, None, {}, {}),
            "backtest_explanation": _backtest_explanation("error", {}),
            "calibration_explanation": _calibration_explanation(None),
            "data_quality_notes": _data_quality_notes(field_report, {}),
            "cli_handoff": _cli_handoff(input_path, mapping_path, None, None),
            "next_steps": ["请先修复 CSV 路径、字段名或 mapping JSON，然后重新预检。"],
            "warnings": [_friendly_error(exc)],
            "disclaimer": DISCLAIMER,
        }
        result["user_view"] = build_user_workflow_view(result)
        return result


def _finalize(
    input_path: str,
    mapping_path: str | None,
    field_report: dict,
    repair_suggestions: list[dict],
    normalized_path: str | None,
    backtest_report: dict,
    calibration_path: str | None,
    analysis: dict,
    warnings: list[str],
    write_report: str | None,
    overall_status: str,
) -> dict:
    result = {
        "workflow_version": WORKFLOW_VERSION,
        "overall_status": overall_status,
        "input_path": input_path,
        "field_report": field_report,
        "repair_suggestions": repair_suggestions,
        "preflight_quality": _preflight_quality({}, field_report),
        "normalized_output_path": normalized_path,
        "backtest": backtest_report,
        "calibration_artifact_path": calibration_path,
        "analysis": analysis,
        "workflow_summary": _workflow_summary(overall_status, normalized_path, calibration_path, backtest_report, analysis),
        "backtest_explanation": _backtest_explanation(overall_status, backtest_report),
        "calibration_explanation": _calibration_explanation(calibration_path),
        "data_quality_notes": _data_quality_notes(field_report, backtest_report),
        "cli_handoff": _cli_handoff(input_path, mapping_path, normalized_path, calibration_path),
        "next_steps": _next_steps(overall_status, field_report, normalized_path, calibration_path),
        "warnings": list(dict.fromkeys(warnings + field_report.get("warnings", []))),
        "disclaimer": DISCLAIMER,
    }
    result["user_view"] = build_user_workflow_view(result)
    if write_report:
        try:
            result["report_markdown_path"] = _write_workflow_report(result, write_report)
        except Exception as exc:
            result["warnings"].append(f"Markdown 报告生成失败：{_friendly_error(exc)}")
    return result


def _next_steps(status: str, field_report: dict, normalized_path: str | None, calibration_path: str | None) -> list[str]:
    if status == "error":
        return ["先按修复建议补充 CSV 字段或 mapping JSON。", "再次运行 user_data_workflow。"]
    if status == "preview":
        return ["字段预检通过后，使用 CLI 执行完整 workflow 生成标准化数据与校准文件。", "命令示例：python3 -m src.cli.user_data_workflow --input <你的CSV> --format json"]
    return [
        f"在 App 的数据导入页查看字段识别结果：{normalized_path}",
        "进入概率回测页查看命中率、ROI、Brier Score、Log Loss 和最大回撤。",
        f"在校准状态页验证 calibration artifact：{calibration_path}",
        "进入指定日期分析页查看候选信号、EV、风险等级和本地解释。",
    ]


def _cli_handoff(input_path: str, mapping_path: str | None, normalized_path: str | None, calibration_path: str | None) -> dict:
    stem = Path(input_path).stem
    output_dir = "data/normalized/user_workflow"
    expected_normalized = normalized_path or str(Path(output_dir) / f"{stem}_normalized.csv")
    expected_calibration = calibration_path or str(Path("artifacts/calibration") / f"{stem}_calibration.json")
    parts = ["python3", "-m", "src.cli.user_data_workflow", "--input", _shell_quote(input_path)]
    if mapping_path:
        parts.extend(["--mapping", _shell_quote(mapping_path)])
    parts.extend(["--output-dir", output_dir, "--format", "json"])
    return {
        "title": "完整 workflow 交接",
        "mode": "cli_only_write_step",
        "command": " ".join(parts),
        "expected_outputs": [
            {"label": "标准化 CSV", "path": expected_normalized, "git_policy": "ignored"},
            {"label": "校准文件", "path": expected_calibration, "git_policy": "ignored"},
        ],
        "notes": [
            "Dashboard/API 默认只读，只做字段预检和回测准备度解释。",
            "完整 workflow 会生成标准化 CSV 和校准文件，因此保持 CLI-only，避免 App 自动写入用户数据。",
            "生成文件位于 ignored 目录，不应提交到 Git。",
        ],
    }


def _shell_quote(value: str) -> str:
    text = str(value)
    if not text:
        return "''"
    if all(ch.isalnum() or ch in "._/-" for ch in text):
        return text
    return "'" + text.replace("'", "'\"'\"'") + "'"


def _preflight_quality(dry_run: dict, field_report: dict) -> dict:
    quality = dry_run.get("quality", {}) if isinstance(dry_run, dict) else {}
    odds_coverage = quality.get("odds_coverage", {}) if isinstance(quality, dict) else {}
    rows_read = _int_value(dry_run.get("rows_read") if isinstance(dry_run, dict) else None)
    rows_normalized = _int_value(dry_run.get("rows_normalized") if isinstance(dry_run, dict) else None)
    rows_skipped = _int_value(dry_run.get("rows_skipped") if isinstance(dry_run, dict) else None)
    had_coverage = _float_value(odds_coverage.get("had")) if isinstance(odds_coverage, dict) else None
    hhad_coverage = _float_value(odds_coverage.get("hhad")) if isinstance(odds_coverage, dict) else None
    can_normalize = bool(field_report.get("can_normalize")) and not field_report.get("missing_required_fields")
    can_backtest_ev = bool(field_report.get("can_backtest_with_ev")) and (had_coverage is None or had_coverage >= 0.5)
    sample_status = "ready" if rows_normalized >= 30 else "warning" if rows_normalized >= 20 else "blocked"
    backtest_status = "ready" if can_normalize and can_backtest_ev and rows_normalized >= 20 else "pending" if can_normalize else "blocked"
    calibration_status = "ready" if rows_normalized >= 100 else "warning" if rows_normalized >= 30 else "pending"
    checks = [
        {
            "item": "样本行数",
            "status": sample_status,
            "value": rows_normalized,
            "message_zh": "样本量可用于入门回测，但仍建议更多真实历史数据。" if sample_status == "ready" else "样本偏少，回测稳定性有限。",
        },
        {
            "item": "胜平负赔率覆盖",
            "status": "ready" if can_backtest_ev else "warning",
            "value": f"{had_coverage * 100:.1f}%" if had_coverage is not None else "unknown",
            "message_zh": "可支持 EV 回测。" if can_backtest_ev else "赔率覆盖不足，EV 回测可信度会下降。",
        },
        {
            "item": "让球赔率覆盖",
            "status": "ready" if hhad_coverage and hhad_coverage >= 0.5 else "info",
            "value": f"{hhad_coverage * 100:.1f}%" if hhad_coverage is not None else "unknown",
            "message_zh": "可辅助让球玩法回测。" if hhad_coverage and hhad_coverage >= 0.5 else "让球赔率不足，不阻断胜平负 EV 回测。",
        },
        {
            "item": "回测准备度",
            "status": backtest_status,
            "value": backtest_status,
            "message_zh": "字段、样本和赔率已具备回测准备度。" if backtest_status == "ready" else "请先修复字段或补充样本/赔率。",
        },
        {
            "item": "校准准备度",
            "status": calibration_status,
            "value": calibration_status,
            "message_zh": "样本量适合生成更稳定的校准诊断。" if calibration_status == "ready" else "可生成入门校准诊断，但样本越少越不稳定。",
        },
    ]
    return {
        "rows_read": rows_read,
        "rows_normalized": rows_normalized,
        "rows_skipped": rows_skipped,
        "date_min": quality.get("date_min") if isinstance(quality, dict) else None,
        "date_max": quality.get("date_max") if isinstance(quality, dict) else None,
        "teams": quality.get("teams") if isinstance(quality, dict) else None,
        "leagues": quality.get("leagues") if isinstance(quality, dict) else None,
        "had_odds_coverage": had_coverage,
        "hhad_odds_coverage": hhad_coverage,
        "can_normalize": can_normalize,
        "can_backtest_ev": can_backtest_ev,
        "backtest_preflight_status": backtest_status,
        "calibration_preflight_status": calibration_status,
        "checks": checks,
        "warnings": list(quality.get("warnings", []) if isinstance(quality, dict) else []),
    }


def _workflow_summary(status: str, normalized_path: str | None, calibration_path: str | None, backtest_report: dict, analysis: dict) -> dict:
    metrics = backtest_report.get("metrics", {}) or {}
    data_summary = backtest_report.get("data_summary", {}) or {}
    return {
        "overall_status": status,
        "normalized_output_path": normalized_path,
        "calibration_artifact_path": calibration_path,
        "historical_matches": data_summary.get("total_matches") or data_summary.get("matches") or 0,
        "evaluated_matches": backtest_report.get("matches_evaluated") or metrics.get("matches_evaluated") or 0,
        "candidate_triggers": backtest_report.get("bets_total") or metrics.get("bets_total") or metrics.get("bet_count") or 0,
        "roi": metrics.get("roi"),
        "max_drawdown": metrics.get("max_drawdown"),
        "brier_score": metrics.get("brier_score"),
        "analysis_matches": analysis.get("matches_analyzed", 0) if isinstance(analysis, dict) else 0,
        "readable_status_zh": "流程完成，可查看回测、校准和候选信号。" if status == "success" else "流程尚未完成，请先修复字段或数据质量问题。",
    }


def _int_value(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float_value(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _backtest_explanation(status: str, backtest_report: dict) -> list[str]:
    if status != "success" or not backtest_report:
        return ["尚未完成概率回测。请先通过字段预检并执行完整 user_data_workflow。"]
    metrics = backtest_report.get("metrics", {}) or {}
    notes = [
        "概率回测用于诊断历史样本中的模型表现，不代表未来表现。",
        "命中率只说明候选方向在历史样本中的命中比例，不能单独代表收益质量。",
        "ROI 表示纸面模拟收益与纸面投入的比例；样本越少，波动越大。",
        "最大回撤用于观察连续不利结果对纸面本金曲线的影响。",
    ]
    if metrics.get("brier_score") is not None:
        notes.append("Brier Score 衡量概率预测误差，越低越好。")
    if metrics.get("log_loss") is not None:
        notes.append("Log Loss 会重罚过度自信但错误的概率预测，越低越好。")
    return notes


def _calibration_explanation(calibration_path: str | None) -> list[str]:
    if not calibration_path:
        return ["尚未生成校准文件。校准文件只用于后续概率诊断辅助。"]
    return [
        f"校准文件已生成：{calibration_path}",
        "校准文件用于让后续分析读取历史概率分箱诊断，不会保证未来结果。",
        "如果历史 CSV 样本量不足或赔率缺失较多，校准效果也会有限。",
    ]


def _data_quality_notes(field_report: dict, backtest_report: dict) -> list[str]:
    notes = []
    missing = field_report.get("missing_required_fields") or []
    if missing:
        notes.append("缺少必需字段：" + "、".join(missing))
    if field_report.get("warnings"):
        notes.extend(str(item) for item in field_report.get("warnings", []))
    data_summary = backtest_report.get("data_summary", {}) or {}
    notes.extend(str(item) for item in data_summary.get("warnings", []) or [])
    if not notes:
        notes.append("字段识别和基础数据质量未发现阻断问题；仍建议使用更多真实历史样本验证。")
    return list(dict.fromkeys(notes))


def _write_workflow_report(result: dict, output_path: str) -> str:
    report = {
        "model_version": "phase2j_user_data_workflow_v0",
        "data_summary": result.get("backtest", {}).get("data_summary", {}),
        "metrics": result.get("backtest", {}).get("metrics", {}),
        "warnings": result.get("warnings", []),
    }
    return export_report_to_markdown(report, output_path)


def _zh_warnings(items: list[str]) -> list[str]:
    translated = []
    for item in items or []:
        text = str(item)
        text = text.replace("sample size is low", "样本量偏低，回测诊断的稳定性有限。")
        text = text.replace("HAD odds coverage is below 50%", "胜平负赔率覆盖率低于 50%，EV 回测可能不足。")
        text = text.replace("team coverage is narrow", "球队覆盖较窄，模型泛化能力有限。")
        text = text.replace("rows skipped during normalization", "行在标准化时被跳过。")
        translated.append(text)
    return translated


def _friendly_error(exc: Exception) -> str:
    text = str(exc).strip()
    if isinstance(exc, FileNotFoundError) or "No such file" in text:
        return "文件不存在。请检查输入 CSV 路径是否正确。"
    if "field mapping" in text:
        return "字段映射文件无法读取。请检查 mapping JSON 是否是有效 JSON。"
    if "date" in text.lower():
        return "日期无法解析。请使用 YYYY-MM-DD、YYYY/MM/DD 或常见日期格式。"
    if "score" in text.lower() or "比分" in text:
        return "比分无法解析。请使用类似 2-1 或 2:1 的比分格式。"
    if "home" in text.lower() or "主队" in text:
        return "未识别主队字段。请检查 CSV 是否包含 `主队` 列，或提供 mapping JSON。"
    return f"用户数据流程失败：{text[:160]}"


def _print_text(result: dict) -> None:
    print("用户 CSV 入门流程")
    print(f"状态: {result.get('overall_status')}")
    print(f"输入: {result.get('input_path')}")
    print(f"标准化输出: {result.get('normalized_output_path')}")
    print(f"校准文件: {result.get('calibration_artifact_path')}")
    for suggestion in result.get("repair_suggestions", []):
        print(f"- {suggestion.get('severity')}: {suggestion.get('message_zh')} {suggestion.get('suggestion_zh')}")
    for step in result.get("next_steps", []):
        print(f"下一步: {step}")
    for warning in result.get("warnings", []):
        print(f"提醒: {warning}")
    print(result.get("disclaimer", ""))


if __name__ == "__main__":
    raise SystemExit(main())

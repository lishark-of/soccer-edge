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
            "normalized_output_path": None,
            "backtest": {},
            "calibration_artifact_path": None,
            "analysis": {},
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
            "normalized_output_path": None,
            "backtest": {},
            "calibration_artifact_path": None,
            "analysis": {},
            "next_steps": ["请先修复 CSV 路径、字段名或 mapping JSON，然后重新预检。"],
            "warnings": [_friendly_error(exc)],
            "disclaimer": DISCLAIMER,
        }
        result["user_view"] = build_user_workflow_view(result)
        return result


def _finalize(
    input_path: str,
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
        "normalized_output_path": normalized_path,
        "backtest": backtest_report,
        "calibration_artifact_path": calibration_path,
        "analysis": analysis,
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

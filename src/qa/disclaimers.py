from __future__ import annotations

from pathlib import Path

from src.qa.checks import QaCheckResult


REQUIRED_DISCLAIMER_TERMS = [
    "仅供数据研究与娱乐参考",
    "不提供投注、下单、支付、代购或任何自动化购彩能力",
    "概率模型不保证结果",
    "回测结果不保证未来表现",
    "串关会显著放大风险",
]

BANNED_PROMOTIONAL_TERMS = [
    "必中",
    "稳赢",
    "稳赚",
    "杀庄",
    "保本",
    "回血",
    "倍投",
    "追号",
    "自动投注",
    "代下单",
    "代购",
    "支付购彩",
]

ALLOW_CONTEXT = ["禁止", "不得", "不提供", "不要", "不能", "must never", "do not", "does not", "forbidden", "disabled", "banned"]


def check_text_disclaimers(text: str, source: str = "") -> list[QaCheckResult]:
    results = []
    for term in REQUIRED_DISCLAIMER_TERMS:
        results.append(
            QaCheckResult(
                name=f"disclaimer.required.{term}",
                passed=term in text,
                message=f"{source or 'text'} contains required safety language: {term}",
                details={"source": source, "term": term},
            )
        )
    results.extend(_check_banned_terms(text, source))
    return results


def check_file_disclaimers(path: str) -> list[QaCheckResult]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return [QaCheckResult(f"disclaimer.file.{path}", False, message=str(exc))]
    return check_text_disclaimers(text, path)


def scan_project_disclaimers(paths: list[str]) -> list[QaCheckResult]:
    combined = []
    parts = []
    for path in paths:
        try:
            parts.append(Path(path).read_text(encoding="utf-8"))
        except OSError as exc:
            combined.append(QaCheckResult(f"disclaimer.scan.{path}", False, message=str(exc)))
    combined.extend(check_text_disclaimers("\n".join(parts), "project safety text"))
    return combined


def _check_banned_terms(text: str, source: str) -> list[QaCheckResult]:
    lines = text.splitlines()
    results = []
    for term in BANNED_PROMOTIONAL_TERMS:
        bad_lines = []
        for index, line in enumerate(lines):
            if term not in line:
                continue
            context = "\n".join(lines[max(0, index - 8) : index + 3]).lower()
            if any(marker in context for marker in ALLOW_CONTEXT):
                continue
            bad_lines.append(index + 1)
        results.append(
            QaCheckResult(
                name=f"disclaimer.banned.{term}",
                passed=not bad_lines,
                message=f"{source or 'text'} has no promotional use of {term}",
                details={"source": source, "term": term, "lines": bad_lines},
            )
        )
    return results

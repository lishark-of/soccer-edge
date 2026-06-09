from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_SEVERITIES = {"info", "warning", "error"}


@dataclass
class QaCheckResult:
    name: str
    passed: bool
    severity: str = "error"
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            self.severity = "error"


def summarize_checks(checks: list[QaCheckResult]) -> dict:
    failed = [check for check in checks if not check.passed]
    warnings = [check for check in checks if check.severity == "warning"]
    errors = [check for check in checks if check.severity == "error" and not check.passed]
    return {
        "total": len(checks),
        "passed": sum(1 for check in checks if check.passed),
        "failed": len(failed),
        "warnings": len(warnings),
        "errors": len(errors),
        "overall_passed": not errors,
    }


def result_to_dict(result: QaCheckResult) -> dict:
    return {
        "name": result.name,
        "passed": result.passed,
        "severity": result.severity,
        "message": result.message,
        "details": dict(result.details),
    }


def results_to_dicts(results: list[QaCheckResult]) -> list[dict]:
    return [result_to_dict(result) for result in results]

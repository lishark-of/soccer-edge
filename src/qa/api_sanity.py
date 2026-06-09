from __future__ import annotations

from src.qa.checks import QaCheckResult


def check_api_envelope(response: dict, endpoint: str = "") -> list[QaCheckResult]:
    prefix = f"api.{endpoint or 'response'}"
    results = [
        QaCheckResult(f"{prefix}.ok", response.get("ok") is True, message="success envelope has ok=true"),
        QaCheckResult(f"{prefix}.data", "data" in response, message="success envelope has data"),
        QaCheckResult(f"{prefix}.warnings", isinstance(response.get("warnings"), list), message="success envelope has warnings list"),
        QaCheckResult(f"{prefix}.disclaimer", bool(response.get("disclaimer")), message="success envelope has disclaimer"),
        QaCheckResult(f"{prefix}.traceback", "traceback" not in str(response).lower(), message="response hides traceback"),
    ]
    disabled = response.get("data", {}).get("disabled_capabilities", [])
    if disabled:
        for item in ("betting", "payment", "order_placement"):
            results.append(QaCheckResult(f"{prefix}.disabled.{item}", item in disabled, message=f"{item} is disabled"))
    return results


def check_api_error_envelope(response: dict, endpoint: str = "") -> list[QaCheckResult]:
    prefix = f"api.{endpoint or 'error'}"
    error = response.get("error", {})
    return [
        QaCheckResult(f"{prefix}.ok", response.get("ok") is False, message="error envelope has ok=false"),
        QaCheckResult(f"{prefix}.code", bool(error.get("code")), message="error has code"),
        QaCheckResult(f"{prefix}.message", bool(error.get("message")), message="error has message"),
        QaCheckResult(f"{prefix}.warnings", isinstance(response.get("warnings"), list), message="error envelope has warnings list"),
        QaCheckResult(f"{prefix}.disclaimer", bool(response.get("disclaimer")), message="error envelope has disclaimer"),
        QaCheckResult(f"{prefix}.traceback", "traceback" not in str(response).lower(), message="error hides traceback"),
    ]

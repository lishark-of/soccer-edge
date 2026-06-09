from __future__ import annotations

from src.explain.deepseek_explainer import explain_with_optional_deepseek
from src.qa.checks import QaCheckResult


def check_no_default_external_calls() -> list[QaCheckResult]:
    calls = {"count": 0}

    def fake_transport(url, headers, body, timeout):
        calls["count"] += 1
        return {"choices": [{"message": {"content": "should not be called"}}]}

    result = explain_with_optional_deepseek(
        "candidate",
        {"model_prob": 0.52, "fair_prob": 0.45, "edge": 0.07, "ev": 0.08, "risk_level": "medium"},
        {"provider": "deepseek", "transport": fake_transport},
    )
    return [
        QaCheckResult(
            "network.no_default_llm_call",
            calls["count"] == 0 and result.get("provider") == "local",
            message="DeepSeek explain path does not call transport while disabled by default",
            details={"calls": calls["count"], "status": result.get("status")},
        )
    ]

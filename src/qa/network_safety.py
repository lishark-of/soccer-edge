from __future__ import annotations

import os
import tempfile
from pathlib import Path

from src.explain.deepseek_explainer import explain_with_optional_deepseek
from src.qa.checks import QaCheckResult


def check_no_default_external_calls() -> list[QaCheckResult]:
    calls = {"count": 0}
    previous_status_path = os.environ.get("JC_EDGE_RUNTIME_STATUS_PATH")
    isolated_status_path = str(Path(tempfile.mkdtemp(prefix="jc_edge_qa_runtime_")) / "runtime_status.json")

    def fake_transport(url, headers, body, timeout):
        calls["count"] += 1
        return {"choices": [{"message": {"content": "should not be called"}}]}

    os.environ["JC_EDGE_RUNTIME_STATUS_PATH"] = isolated_status_path
    try:
        result = explain_with_optional_deepseek(
            "candidate",
            {"model_prob": 0.52, "fair_prob": 0.45, "edge": 0.07, "ev": 0.08, "risk_level": "medium"},
            {"provider": "local", "transport": fake_transport},
        )
    finally:
        if previous_status_path is None:
            os.environ.pop("JC_EDGE_RUNTIME_STATUS_PATH", None)
        else:
            os.environ["JC_EDGE_RUNTIME_STATUS_PATH"] = previous_status_path
    return [
        QaCheckResult(
            "network.no_default_llm_call",
            calls["count"] == 0 and result.get("provider") == "local" and result.get("ds_attempted") is False,
            message="DeepSeek explain path does not call transport when local mode is explicitly requested",
            details={"calls": calls["count"], "status": result.get("status")},
        )
    ]

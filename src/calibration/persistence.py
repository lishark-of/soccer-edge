from __future__ import annotations

import json
from pathlib import Path


def save_calibration_artifact(artifact: dict, path: str) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, ensure_ascii=False, indent=2)
    return str(target)


def load_calibration_artifact(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("calibration artifact must be a JSON object")
    return payload

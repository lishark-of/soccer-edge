from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def build_import_manifest(
    input_path: str,
    adapter: str,
    rows_read: int,
    rows_normalized: int,
    rows_skipped: int,
    output_path: str | None,
    warnings: list[str],
) -> dict:
    return {
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input_path": input_path,
        "input_sha256": _sha256(input_path),
        "adapter": adapter,
        "rows_read": rows_read,
        "rows_normalized": rows_normalized,
        "rows_skipped": rows_skipped,
        "output_path": output_path,
        "warnings": list(warnings),
    }


def write_manifest(manifest: dict, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    return str(path)


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

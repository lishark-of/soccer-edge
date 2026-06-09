from __future__ import annotations

import subprocess

from src.qa.checks import QaCheckResult


GENERATED_PATHS = ["artifacts", "reports", "data/normalized", "data/raw", "data/imports", "output"]
GENERATED_SUFFIXES = (".xlsx",)


def check_generated_paths_not_tracked(project_root: str) -> list[QaCheckResult]:
    tracked = _git(project_root, ["ls-files"]).splitlines()
    generated = [
        path
        for path in tracked
        if any(path == item or path.startswith(f"{item}/") for item in GENERATED_PATHS) or path.endswith(GENERATED_SUFFIXES)
    ]
    return [QaCheckResult("git.generated_not_tracked", not generated, message="generated paths are not tracked", details={"tracked": generated})]


def check_git_remote_absent(project_root: str) -> list[QaCheckResult]:
    remotes = _git(project_root, ["remote", "-v"]).strip()
    return [QaCheckResult("git.remote_absent", remotes == "", message="git remote is absent", details={"remote": remotes})]


def check_worktree_clean_or_expected(project_root: str) -> list[QaCheckResult]:
    status = _git(project_root, ["status", "--porcelain"]).splitlines()
    generated = [line for line in status if any(part in line for part in GENERATED_PATHS)]
    return [
        QaCheckResult("git.no_staged_generated", not generated, message="no generated files are staged or tracked in status", details={"generated_status": generated}),
        QaCheckResult("git.status_available", True, severity="info", message="git status inspected", details={"entries": len(status)}),
    ]


def _git(project_root: str, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=project_root, check=True, capture_output=True, text=True)
    return result.stdout

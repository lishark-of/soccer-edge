from __future__ import annotations

__version__ = "0.1.0-local"


def get_version() -> str:
    return __version__


def get_build_info() -> dict:
    return {
        "version": __version__,
        "release_phase": "phase2i",
        "mode": "local_read_only",
        "remote": "none",
    }

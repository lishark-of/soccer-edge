from __future__ import annotations


SUPPORTED_PASS_TYPES = {
    "single": 1,
    "1x1": 1,
    "2x1": 2,
    "3x1": 3,
}


def normalize_pass_type(pass_type: str) -> str:
    key = pass_type.strip().lower()
    if key not in SUPPORTED_PASS_TYPES:
        raise ValueError(f"Unsupported pass type: {pass_type}")
    return key


def pass_leg_count(pass_type: str) -> int:
    return SUPPORTED_PASS_TYPES[normalize_pass_type(pass_type)]

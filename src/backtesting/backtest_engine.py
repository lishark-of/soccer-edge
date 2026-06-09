from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ChronologicalSplit:
    train: list[dict[str, Any]]
    test: list[dict[str, Any]]


def chronological_split(rows: list[dict[str, Any]], train_ratio: float = 0.8) -> ChronologicalSplit:
    ordered = sorted(rows, key=lambda item: item["date"])
    cutoff = max(1, int(len(ordered) * train_ratio)) if ordered else 0
    return ChronologicalSplit(train=ordered[:cutoff], test=ordered[cutoff:])


def rolling_feature_shift(values: list[float | None]) -> list[float | None]:
    shifted: list[float | None] = [None]
    shifted.extend(values[:-1])
    return shifted


def features_use_only_past_matches(matches: list[dict[str, Any]]) -> bool:
    ordered = sorted(matches, key=lambda item: item["date"])
    return ordered == matches

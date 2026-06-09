from __future__ import annotations

import math


def brier_score(probability: float, outcome: int) -> float:
    return (probability - float(outcome)) ** 2


def log_loss(probability: float, outcome: int) -> float:
    clipped = min(0.999999, max(0.000001, probability))
    if outcome:
        return -math.log(clipped)
    return -math.log(1 - clipped)

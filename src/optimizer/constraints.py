from __future__ import annotations

DEFAULT_OPTIMIZER_CONFIG = {
    "max_daily_exposure_pct": 0.03,
    "single_stake_cap_pct": 0.01,
    "parlay_2x1_cap_pct": 0.005,
    "parlay_3x1_cap_pct": 0.0025,
    "min_ev": 0.04,
    "min_edge": 0.025,
    "max_risk": "medium",
    "enable_3x1": False,
    "kelly_multiplier": 0.25,
    "max_singles": 3,
    "max_parlay_2x1": 2,
    "max_parlay_3x1": 1,
}

RISK_RANK = {"low": 1, "medium": 2, "high": 3, "very_high": 4}


def merge_config(config: dict | None = None) -> dict:
    merged = {**DEFAULT_OPTIMIZER_CONFIG, **(config or {})}
    merged["daily_exposure_cap"] = float(merged.get("bankroll", 10000.0)) * float(merged["max_daily_exposure_pct"])
    return merged


def risk_allowed(risk_level: str, max_risk: str = "medium") -> bool:
    return RISK_RANK.get(str(risk_level or "medium"), 2) <= RISK_RANK.get(str(max_risk or "medium"), 2)


def stake_cap_for(kind: str, bankroll: float, config: dict) -> float:
    if kind == "single":
        pct = config["single_stake_cap_pct"]
    elif kind == "parlay_3x1":
        pct = config["parlay_3x1_cap_pct"]
    else:
        pct = config["parlay_2x1_cap_pct"]
    return round(float(bankroll) * float(pct), 2)

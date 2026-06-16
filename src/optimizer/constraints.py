from __future__ import annotations

RISK_PROFILES = {
    "conservative": {
        "risk_profile": "conservative",
        "risk_profile_label": "保守",
        "max_daily_exposure_pct": 0.03,
        "single_stake_cap_pct": 0.01,
        "parlay_2x1_cap_pct": 0.005,
        "parlay_3x1_cap_pct": 0.0,
        "min_ev": 0.04,
        "min_edge": 0.025,
        "max_risk": "medium",
        "enable_3x1": False,
        "kelly_multiplier": 0.25,
        "max_singles": 3,
        "max_parlay_2x1": 0,
        "max_parlay_3x1": 0,
        "min_parlay_2x1_prob": 0.25,
        "min_parlay_3x1_prob": 1.0,
        "min_leg_confidence": 0.55,
        "longshot_parlay_confidence_min": 0.75,
    },
    "balanced": {
        "risk_profile": "balanced",
        "risk_profile_label": "均衡",
        "max_daily_exposure_pct": 0.05,
        "single_stake_cap_pct": 0.012,
        "parlay_2x1_cap_pct": 0.008,
        "parlay_3x1_cap_pct": 0.0,
        "min_ev": 0.035,
        "min_edge": 0.02,
        "max_risk": "medium",
        "enable_3x1": False,
        "kelly_multiplier": 0.25,
        "max_singles": 3,
        "max_parlay_2x1": 2,
        "max_parlay_3x1": 0,
        "min_parlay_2x1_prob": 0.22,
        "min_parlay_3x1_prob": 1.0,
        "min_leg_confidence": 0.55,
        "longshot_parlay_confidence_min": 0.75,
    },
    "aggressive": {
        "risk_profile": "aggressive",
        "risk_profile_label": "进取",
        "max_daily_exposure_pct": 0.08,
        "single_stake_cap_pct": 0.015,
        "parlay_2x1_cap_pct": 0.01,
        "parlay_3x1_cap_pct": 0.004,
        "min_ev": 0.025,
        "min_edge": 0.015,
        "max_risk": "high",
        "enable_3x1": True,
        "kelly_multiplier": 0.25,
        "max_singles": 3,
        "max_parlay_2x1": 3,
        "max_parlay_3x1": 1,
        "min_parlay_2x1_prob": 0.20,
        "min_parlay_3x1_prob": 0.12,
        "min_leg_confidence": 0.50,
        "longshot_parlay_confidence_min": 0.75,
    },
}

DEFAULT_OPTIMIZER_CONFIG = dict(RISK_PROFILES["conservative"])
RISK_RANK = {"low": 1, "medium": 2, "high": 3, "very_high": 4}


def merge_config(config: dict | None = None) -> dict:
    incoming = dict(config or {})
    profile = str(incoming.get("risk_profile") or incoming.get("profile") or "conservative").lower()
    if profile not in RISK_PROFILES:
        profile = "conservative"
    merged = {**RISK_PROFILES[profile], **incoming}
    merged["risk_profile"] = profile
    merged["risk_profile_label"] = RISK_PROFILES[profile]["risk_profile_label"]
    if profile != "aggressive" and not incoming.get("enable_3x1"):
        merged["enable_3x1"] = False
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

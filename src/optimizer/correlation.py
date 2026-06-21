from __future__ import annotations


def same_match_forbidden(legs: list[dict]) -> bool:
    ids = [leg.get("match_id") for leg in legs if leg.get("match_id")]
    return len(ids) != len(set(ids))


def correlation_discount(legs: list[dict]) -> float:
    if same_match_forbidden(legs):
        return 0.0
    discount = 1.0
    for i, left in enumerate(legs):
        for right in legs[i + 1 :]:
            if _share_team(left, right):
                discount = min(discount, 0.85)
            elif left.get("league") and left.get("league") == right.get("league"):
                discount = min(discount, 0.95)
    return discount


def correlation_reason(legs: list[dict]) -> str:
    if same_match_forbidden(legs):
        return "同场互斥，禁止组合。"
    if any(_share_team(left, right) for i, left in enumerate(legs) for right in legs[i + 1 :]):
        return "存在同队相关，使用 0.85 相关性折扣。"
    if any(left.get("league") and left.get("league") == right.get("league") for i, left in enumerate(legs) for right in legs[i + 1 :]):
        return "同联赛不同场，使用 0.95 相关性折扣。"
    return "不同联赛或相关性较低，使用 1.00 折扣。"


def correlation_quality(legs: list[dict]) -> dict:
    if same_match_forbidden(legs):
        return {
            "score": 0,
            "level": "blocked",
            "label_zh": "同场互斥",
            "reason_zh": "组合包含同一场比赛的多个方向，结果互相影响，禁止升级为组合观察。",
            "risk_flags": ["same_match"],
        }
    flags = []
    if any(_share_team(left, right) for i, left in enumerate(legs) for right in legs[i + 1 :]):
        flags.append("share_team")
    if any(left.get("league") and left.get("league") == right.get("league") for i, left in enumerate(legs) for right in legs[i + 1 :]):
        flags.append("same_league")
    play_types = [str(leg.get("play_type") or "unknown") for leg in legs]
    if len(set(play_types)) < len(play_types):
        flags.append("same_play_type")
    outcome_groups = [f"{leg.get('play_type') or 'unknown'}:{leg.get('outcome_key') or leg.get('outcome_label') or ''}" for leg in legs]
    if len(set(outcome_groups)) < len(outcome_groups):
        flags.append("same_direction_type")
    score = 92
    if "share_team" in flags:
        score -= 28
    if "same_league" in flags:
        score -= 10
    if "same_play_type" in flags:
        score -= 16
    if "same_direction_type" in flags:
        score -= 12
    score = max(0, min(100, score))
    if score >= 80:
        level, label = "strong", "相关性较低"
    elif score >= 60:
        level, label = "usable", "相关性可控"
    else:
        level, label = "weak", "相关性偏高"
    return {
        "score": score,
        "level": level,
        "label_zh": label,
        "reason_zh": _quality_reason(flags),
        "risk_flags": flags,
    }


def _share_team(left: dict, right: dict) -> bool:
    teams_left = {left.get("home_team"), left.get("away_team")}
    teams_right = {right.get("home_team"), right.get("away_team")}
    teams_left.discard(None)
    teams_left.discard("")
    teams_right.discard(None)
    teams_right.discard("")
    return bool(teams_left & teams_right)


def _quality_reason(flags: list[str]) -> str:
    if not flags:
        return "不同比赛、不同队伍或玩法分散，组合相关性较低。"
    mapping = {
        "share_team": "存在同队相关",
        "same_league": "同联赛环境可能相关",
        "same_play_type": "玩法类型重复",
        "same_direction_type": "玩法与方向过于相似",
    }
    return "；".join(mapping.get(flag, flag) for flag in flags) + "。"

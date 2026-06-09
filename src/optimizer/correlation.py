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


def _share_team(left: dict, right: dict) -> bool:
    teams_left = {left.get("home_team"), left.get("away_team")}
    teams_right = {right.get("home_team"), right.get("away_team")}
    teams_left.discard(None)
    teams_left.discard("")
    teams_right.discard(None)
    teams_right.discard("")
    return bool(teams_left & teams_right)

from __future__ import annotations


def settle_single_observation(observation: dict, actual_result: str) -> dict:
    stake = float(observation.get("paper_stake") or 0.0)
    odds = float(observation.get("odds") or 0.0)
    selected = observation.get("outcome_key") or observation.get("selection")
    if not actual_result:
        return {**observation, "settlement_status": "unsettled", "hit": None, "profit": 0.0, "result_label_zh": "缺少赛果，暂不结算"}
    if odds <= 1 or stake <= 0:
        return {**observation, "settlement_status": "void", "hit": None, "profit": 0.0, "result_label_zh": "赔率或模拟金额不可用，按无效观察处理"}
    hit = selected == actual_result
    profit = stake * (odds - 1.0) if hit else -stake
    return {**observation, "settlement_status": "settled", "actual_result": actual_result, "hit": hit, "profit": round(profit, 2), "result_label_zh": "命中" if hit else "未命中"}


def settle_parlay_observation(observation: dict, actual_results: dict) -> dict:
    stake = float(observation.get("paper_stake") or 0.0)
    odds = float(observation.get("combined_odds") or 0.0)
    legs = list(observation.get("legs", []) or [])
    if not legs or stake <= 0 or odds <= 1:
        return {**observation, "settlement_status": "void", "hit": None, "profit": 0.0, "result_label_zh": "组合信息不足，按无效观察处理"}
    missing = [leg for leg in legs if leg.get("match_id") not in actual_results]
    if missing:
        return {**observation, "settlement_status": "unsettled", "hit": None, "profit": 0.0, "result_label_zh": "存在缺失赛果，暂不结算"}
    hit = all((leg.get("outcome_key") or leg.get("selection")) == actual_results.get(leg.get("match_id")) for leg in legs)
    profit = stake * (odds - 1.0) if hit else -stake
    return {**observation, "settlement_status": "settled", "actual_results": actual_results, "hit": hit, "profit": round(profit, 2), "result_label_zh": "组合命中" if hit else "组合未命中"}


def settle_observations(observations: list[dict], actual_results: dict) -> list[dict]:
    settled = []
    for observation in observations:
        kind = observation.get("observation_type", "single")
        if kind == "single":
            settled.append(settle_single_observation(observation, actual_results.get(observation.get("match_id"))))
        else:
            settled.append(settle_parlay_observation(observation, actual_results))
    return settled

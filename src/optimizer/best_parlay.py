from __future__ import annotations


def build_best_parlay_summary(optimizer_result: dict) -> dict:
    gate = optimizer_result.get("credibility_gate") or {}
    rankings = optimizer_result.get("candidate_rankings") or {}
    selected = optimizer_result.get("selected_portfolio") or {}
    singles = _merge_rows(selected.get("singles", []), rankings.get("singles", []), "single")
    parlay2 = _merge_rows(selected.get("parlay_2x1", []), rankings.get("parlay_2x1", []), "parlay_2x1")
    parlay3 = _merge_rows(selected.get("parlay_3x1", []), rankings.get("parlay_3x1", []), "parlay_3x1")
    combos = parlay2 + parlay3
    rejected = [row for row in combos if not row.get("selected")]
    selected_combos = [row for row in combos if row.get("selected")]
    no_combo = gate.get("combo_gate") == "closed" or not selected_combos
    gate_closed = gate.get("combo_gate") == "closed"
    gate_empty = _gate_empty(gate)
    best_single = _best(singles, key="risk_adjusted_score")
    daily_single = _daily_candidate(best_single, gate, kind="single")
    daily_2x1_base = _best_daily_combo(parlay2, 2)
    daily_2x1 = _daily_candidate(_diversity_substitute_if_needed(daily_2x1_base, singles, 2, gate), gate)
    if not _is_real_candidate(daily_2x1):
        daily_2x1 = _daily_candidate(_synthetic_combo_from_singles(singles, 2, gate), gate)
    daily_3x1_base = _best_daily_combo(parlay3, 3)
    daily_3x1 = _daily_candidate(_diversity_substitute_if_needed(daily_3x1_base, singles, 3, gate), gate)
    if not _is_real_candidate(daily_3x1):
        daily_3x1 = _daily_candidate(_synthetic_combo_from_singles(singles, 3, gate), gate)
    best_2x1 = daily_2x1 if _has_candidate_identity(daily_2x1) else gate_empty
    best_3x1 = daily_3x1 if _has_candidate_identity(daily_3x1) else gate_empty
    safest_combo = _daily_candidate(_best(combos, key="safety_score"), gate, kind="combo") if combos else gate_empty
    highest_ev_combo = _daily_candidate(_best(combos, key="ev"), gate, kind="combo") if combos else gate_empty
    best_risk_adjusted = _daily_candidate(_best(combos, key="risk_adjusted_score"), gate, kind="combo") if combos else gate_empty
    user_board = _user_combo_board(
        gate=gate,
        best_single=best_single,
        best_2x1=best_2x1,
        best_3x1=best_3x1,
        daily_2x1=daily_2x1,
        daily_3x1=daily_3x1,
        best_risk_adjusted=best_risk_adjusted,
        selected_combos=selected_combos,
        rejected=rejected,
        no_combo_reason=optimizer_result.get("no_combo_reason") or gate.get("reason_zh") or "",
    )
    return {
        "summary_version": "phase2p_best_parlay_v0",
        "risk_profile": optimizer_result.get("risk_profile"),
        "risk_profile_label": optimizer_result.get("risk_profile_label"),
        "credibility_gate": gate,
        "status": "paper_candidates" if no_combo and (_has_candidate_identity(daily_2x1) or _has_candidate_identity(daily_3x1)) else ("no_combo" if no_combo else "has_combo"),
        "label_zh": "已输出每日纸面候选" if no_combo and (_has_candidate_identity(daily_2x1) or _has_candidate_identity(daily_3x1)) else ("暂无优秀串联观察" if no_combo else "存在优秀串联观察"),
        "no_combo_reason": optimizer_result.get("no_combo_reason") or gate.get("reason_zh") or "可信度不足、情报缺失较多、组合风险高于模型优势。",
        "best_single": best_single,
        "best_2x1": best_2x1,
        "best_3x1_if_allowed": best_3x1,
        "daily_single_candidate": daily_single,
        "daily_2x1_candidate": daily_2x1,
        "daily_3x1_candidate": daily_3x1,
        "daily_output_lanes": _daily_output_lanes(daily_single, daily_2x1, daily_3x1, gate, optimizer_result.get("no_combo_reason")),
        "safest_combo": safest_combo,
        "highest_ev_combo": highest_ev_combo,
        "best_risk_adjusted_combo": best_risk_adjusted,
        "user_combo_board": user_board,
        "selected_combos": selected_combos[:10],
        "rejected_combos": rejected[:20],
        "conclusion_zh": _daily_output_conclusion(daily_single, daily_2x1, daily_3x1, gate, optimizer_result.get("no_combo_reason")) or _conclusion(singles, parlay2, parlay3),
        "risk_note_zh": "优秀串联只代表纸面观察排序。串关需要多场同时命中，会显著放大波动；不要因为组合赔率高就提高信心。",
        "disclaimer": "仅用于观察信号、纸面模拟和风险诊断，不构成投注建议。",
    }


def _daily_output_lanes(daily_single: dict, daily_2x1: dict, daily_3x1: dict, gate: dict, no_combo_reason: str | None) -> list[dict]:
    return [
        _daily_lane(
            key="daily_single_candidate",
            label="每日单关",
            item=daily_single,
            fallback="暂无可排序单关",
            gate=gate,
            no_combo_reason=no_combo_reason,
        ),
        _daily_lane(
            key="daily_2x1_candidate",
            label="每日2串1",
            item=daily_2x1,
            fallback="暂无可排序2串1",
            gate=gate,
            no_combo_reason=no_combo_reason,
        ),
        _daily_lane(
            key="daily_3x1_candidate",
            label="每日3串1",
            item=daily_3x1,
            fallback="暂无可排序3串1",
            gate=gate,
            no_combo_reason=no_combo_reason,
        ),
    ]


def _daily_lane(*, key: str, label: str, item: dict, fallback: str, gate: dict, no_combo_reason: str | None) -> dict:
    if not _is_real_candidate(item):
        reason = item.get("reject_reason") or item.get("message_zh") or no_combo_reason or gate.get("reason_zh") or "候选池不足。"
        return {
            "key": key,
            "label_zh": label,
            "status": "empty",
            "status_zh": fallback,
            "target_zh": fallback,
            "odds_zh": "N/A",
            "model_prob_zh": "N/A",
            "market_prob_zh": "N/A",
            "ev_zh": "N/A",
            "edge_zh": "N/A",
            "risk_zh": "N/A",
            "action_zh": "等待更多比赛或完整候选池",
            "why_zh": reason,
            "next_review_zh": "刷新赛前优化后再复核。",
        }
    selected = _is_pass_status(item.get("status"), selected=bool(item.get("selected")))
    is_combo = key != "daily_single_candidate"
    reason = item.get("selected_reason_zh") or item.get("reject_reason") or item.get("hit_rate_discipline_zh") or "进入每日纸面候选。"
    action = (
        "可进入观察清单，仍需临场复核"
        if selected and not is_combo
        else "组合通过门控，逐腿复核后保留观察"
        if selected
        else "仅纸面观察，赛后复盘验证"
    )
    if item.get("risk_level") in {"high", "very_high"}:
        action = "高波动纸面候选，不作为串联核心"
    verdict = _lane_verdict(key, selected, item)
    checklist = _lane_checklist(key, selected, item)
    return {
        "key": key,
        "label_zh": label,
        "status": "selected" if selected else "paper_candidate",
        "status_zh": "通过门控" if selected else "纸面候选",
        "verdict_zh": verdict,
        "target_zh": item.get("legs") or item.get("match") or label,
        "odds_zh": _fmt_num(item.get("odds")),
        "model_prob_zh": _fmt_pct(item.get("model_prob")),
        "market_prob_zh": _fmt_pct(item.get("market_prob")),
        "ev_zh": _fmt_signed_pct(item.get("ev")),
        "edge_zh": _fmt_signed_pct(item.get("edge")),
        "risk_zh": str(item.get("risk_level") or "待评估"),
        "action_zh": action,
        "why_zh": reason,
        "next_review_zh": _lane_next_review(key, selected, item),
        "review_checklist_zh": checklist,
        "quality_zh": (item.get("best_parlay_quality") or {}).get("reason_zh", ""),
        "paper_candidate_warning_zh": item.get("paper_candidate_warning_zh", ""),
    }


def _lane_verdict(key: str, selected: bool, item: dict) -> str:
    if selected:
        return "可观察，仍需临场复核"
    risk = str(item.get("risk_level") or "")
    ev = _float(item.get("ev"))
    edge = _float(item.get("edge"))
    odds = _float(item.get("odds"))
    if key != "daily_single_candidate":
        return "纸面组合候选，未过完整门控"
    if odds >= 6 or risk in {"high", "very_high"}:
        return "冷门观察，不适合作串联核心"
    if ev > 0 and edge > 0:
        return "弱观察，等待终盘确认"
    if odds > 1.01 and _float(item.get("model_prob")) > 0:
        return "纸面单关候选，等终盘确认"
    return "只做复盘候选"


def _lane_checklist(key: str, selected: bool, item: dict) -> list[str]:
    checks = []
    if key == "daily_single_candidate":
        checks.append("看终盘赔率是否反向漂移")
        checks.append("看首发/伤停是否新增反对因素")
        checks.append("看模型概率是否仍覆盖市场概率")
    else:
        checks.append("逐腿确认不是同一大方向拥挤")
        checks.append("检查组合命中概率是否覆盖组合赔率")
        checks.append("检查相关性折扣和单腿弱点")
    if item.get("risk_level") in {"high", "very_high"}:
        checks.append("高波动候选，只进赛后学习")
    if item.get("reject_reason"):
        checks.append("先读未过门控原因")
    return checks[:4]


def _lane_next_review(key: str, selected: bool, item: dict) -> str:
    if key == "daily_single_candidate":
        return "赛前重点复核终盘赔率、首发和伤停；赔率反向漂移则降级。"
    if selected:
        return "逐腿复核赔率覆盖、相关性和缺失情报，不能只看组合赔率。"
    return item.get("reject_reason") or "保留为赛后学习样本，验证是否被规则过度拒绝。"


def _is_pass_status(status: object, selected: bool = False) -> bool:
    if selected:
        return True
    raw = str(status or "").strip()
    return raw in {"selected", "pass", "通过门控", "selected_after_gate"}


def _row_status(status: object, selected: bool = False) -> str:
    return "通过门控" if _is_pass_status(status, selected=selected) else "未过门控"


def _merge_rows(selected_rows: list[dict], ranking_rows: list[dict], kind: str) -> list[dict]:
    rows = []
    for row in selected_rows or []:
        rows.append(_normalize_row(row, kind, selected=True))
    seen = {_row_key(row) for row in rows}
    for row in ranking_rows or []:
        normalized = _normalize_row(row, kind, selected=bool(row.get("selected")))
        key = _row_key(normalized)
        if key not in seen:
            rows.append(normalized)
            seen.add(key)
    return sorted(rows, key=lambda item: item.get("risk_adjusted_score", -999), reverse=True)


def _normalize_row(row: dict, kind: str, selected: bool) -> dict:
    odds = _float(row.get("odds") or row.get("combo_odds"))
    model_prob = _float(row.get("model_prob") or row.get("combo_prob"))
    market_prob = _float(row.get("market_prob"))
    ev = _float(row.get("ev"))
    edge = _float(row.get("edge"))
    confidence = _float(row.get("observation_confidence") or row.get("confidence_score"), default=0.45)
    correlation_discount = _float(row.get("correlation_discount"), default=1.0)
    risk = str(row.get("risk_level") or "medium")
    status = _row_status(row.get("status"), selected=selected)
    reject_reason = row.get("reject_reason") or row.get("reason") or ("通过门控" if status == "通过门控" else "未通过组合纪律。")
    hard_invalid = odds <= 1.01 or "同场互斥" in str(reject_reason)
    risk_penalty = {"low": 0.0, "medium": 0.08, "high": 0.18, "very_high": 0.32}.get(risk, 0.10)
    agreement = max(0.0, 1.0 - min(1.0, abs(model_prob - market_prob) * 4)) if model_prob and market_prob else 0.35
    odds_quality = min(1.0, odds / 5.0) if odds else 0.0
    normalized_ev = max(-1.0, min(1.0, ev / 0.25)) if ev is not None else -0.2
    low_correlation = max(0.0, min(1.0, correlation_discount))
    drawdown_safety = max(0.0, 1.0 - risk_penalty)
    combo_score = 0.35 * normalized_ev + 0.20 * confidence + 0.15 * agreement + 0.10 * odds_quality + 0.10 * low_correlation + 0.10 * drawdown_safety
    risk_adjusted = combo_score - risk_penalty
    hit_rate_floor = _hit_rate_floor(kind)
    hit_rate_pass = model_prob >= hit_rate_floor
    if hard_invalid:
        combo_score = -999.0
        risk_adjusted = -999.0
    return {
        "type": row.get("type") or row.get("candidate_type") or kind,
        "label_zh": _type_label(kind),
        "match": row.get("match") or _match_label(row),
        "legs": _legs_label(row),
        "play_type": row.get("play_type", ""),
        "play_type_zh": row.get("play_type_zh") or row.get("play_type_mix_zh") or "",
        "direction": row.get("direction", ""),
        "direction_family_zh": row.get("direction_family_zh") or "",
        "leg_play_types": row.get("leg_play_types", []),
        "leg_directions": row.get("leg_directions", []),
        "odds": odds,
        "model_prob": model_prob,
        "market_prob": market_prob,
        "ev": ev,
        "edge": edge,
        "confidence_score": round(confidence, 4),
        "market_model_agreement": round(agreement, 4),
        "odds_quality": round(odds_quality, 4),
        "correlation_discount": round(correlation_discount, 4),
        "drawdown_safety": round(drawdown_safety, 4),
        "combo_score": round(combo_score, 4),
        "risk_adjusted_score": round(risk_adjusted, 4),
        "daily_diversity_score": round(risk_adjusted + _diversity_bonus(row, risk), 4),
        "leg_quality_score": _float(row.get("leg_quality_score"), default=round(combo_score, 4)),
        "information_score": _float(row.get("information_score"), default=confidence),
        "hit_rate_pass": hit_rate_pass,
        "hit_rate_floor": hit_rate_floor,
        "hit_rate_discipline_zh": row.get("hit_rate_discipline_zh") or _hit_rate_message(kind, model_prob, hit_rate_floor),
        "safety_score": round(drawdown_safety + low_correlation - max(0, odds_quality - 0.6) * 0.2, 4),
        "paper_stake": _float(row.get("paper_stake") or row.get("suggested_paper_stake"), default=0.0),
        "risk_level": risk,
        "selected": status == "通过门控",
        "status": status,
        "selected_reason_zh": "该组合暂不建议作为优秀串联。" if hard_invalid else _selected_reason(ev, edge, confidence, correlation_discount, risk),
        "opposing_factors_zh": _opposing_factors(row, model_prob, market_prob, confidence, risk),
        "missing_intelligence_zh": row.get("missing_signals") or row.get("missing_intelligence") or "查看数据可靠性页。",
        "reject_reason": reject_reason,
        "parlay_risk_note_zh": "串关需要所有腿同时命中，组合概率会低于单腿概率。",
        "best_parlay_quality": _quality(ev, edge, confidence, correlation_discount, risk, status, hard_invalid, hit_rate_pass),
    }


def _best(rows: list[dict], key: str) -> dict:
    if not rows:
        return {"status": "empty", "message_zh": "当前没有可排序候选。"}
    valid = [item for item in rows if _float(item.get(key), default=-999) > -900 and _float(item.get("odds"), default=0) > 1.01]
    if not valid:
        nearest = rows[0]
        return {
            "status": "empty",
            "message_zh": f"当前没有合格候选；最近被拒原因：{nearest.get('reject_reason', '未通过组合纪律。')}",
            "reject_reason": nearest.get("reject_reason", "未通过组合纪律。"),
            "best_parlay_quality": {"final_status": "no_combo", "reason_zh": nearest.get("reject_reason", "未通过组合纪律。")},
        }
    selected = sorted(valid, key=lambda item: _float(item.get(key), default=-999), reverse=True)[0]
    return selected


def _best_daily_combo(rows: list[dict], leg_count: int) -> dict:
    if not rows:
        return {"status": "empty", "message_zh": "当前没有可排序候选。"}
    valid = [item for item in rows if _float(item.get("odds"), default=0) > 1.01 and _float(item.get("risk_adjusted_score"), default=-999) > -900]
    if not valid:
        return _best(rows, key="risk_adjusted_score")
    selected = sorted(valid, key=lambda item: _float(item.get("daily_diversity_score"), default=-999), reverse=True)[0]
    if selected.get("daily_diversity_score") != selected.get("risk_adjusted_score"):
        selected = dict(selected)
        selected["selected_reason_zh"] = (
            selected.get("selected_reason_zh", "")
            + " 每日候选已按玩法/方向分散重排，避免只输出同质化主胜或让胜组合。"
        ).strip()
    return selected


def _diversity_substitute_if_needed(candidate: dict, singles: list[dict], leg_count: int, gate: dict) -> dict:
    if not _is_real_candidate(candidate):
        return candidate
    if not _is_homogeneous_combo(candidate):
        return candidate
    synthetic = _synthetic_combo_from_singles(singles, leg_count, gate)
    if not _is_real_candidate(synthetic) or _is_homogeneous_combo(synthetic):
        return candidate
    upgraded = dict(synthetic)
    upgraded["selected_reason_zh"] = (
        "原始组合候选过于同玩法/同方向，系统改用 Top 单关合成的分散纸面组合，用于 T+1 赛后验证。"
    )
    upgraded["reject_reason"] = (
        upgraded.get("reject_reason", "")
        + " 原始最佳组合存在同质化，本条用于检验分散组合是否更适合短赛会。"
    ).strip()
    return upgraded


def _is_homogeneous_combo(item: dict) -> bool:
    if not item.get("legs"):
        return False
    plays = _split_mix(item.get("play_type_zh") or item.get("play_type_mix_zh"))
    directions = _split_mix(item.get("direction_family_zh"))
    if len(plays) <= 1 and len(directions) <= 1:
        return True
    text = str(item.get("combo_homogeneity_reason_zh") or item.get("reject_reason") or "")
    return "同玩法" in text and "同方向" in text


def _synthetic_combo_from_singles(singles: list[dict], leg_count: int, gate: dict) -> dict:
    pool = [
        row
        for row in singles
        if _float(row.get("odds")) > 1.01 and _float(row.get("model_prob")) > 0 and _float(row.get("market_prob")) > 0
    ]
    if len(pool) < leg_count:
        return {
            "status": "empty",
            "message_zh": f"单关候选不足 {leg_count} 条，无法生成每日{leg_count}串1纸面候选。",
            "reject_reason": gate.get("reason_zh") or "候选池不足。",
        }
    legs = _diverse_singles_for_combo(pool, leg_count)
    odds = 1.0
    model_prob = 1.0
    market_prob = 1.0
    confidences = []
    risks = []
    for leg in legs:
        odds *= _float(leg.get("odds"))
        model_prob *= _float(leg.get("model_prob"))
        market_prob *= _float(leg.get("market_prob"))
        confidences.append(_float(leg.get("confidence_score"), 0.45))
        risks.append(str(leg.get("risk_level") or "medium"))
    correlation_discount = 0.94 if leg_count == 2 else 0.88
    model_prob *= correlation_discount
    ev = model_prob * odds - 1.0
    edge = model_prob - market_prob
    risk = "very_high" if leg_count == 3 or any(row in {"high", "very_high"} for row in risks) else "high"
    play_mix = _unique_join([str(leg.get("play_type_zh") or "") for leg in legs])
    direction_mix = _unique_join([str(leg.get("direction_family_zh") or _broad_direction(leg)) for leg in legs])
    label = f"{leg_count}串1"
    reason = (
        f"每日{label}纸面候选由 Top 单关临时合成：用于 T+1 复盘和赛后学习，"
        "不是通过门控的强组合。请重点检查同方向、相关性、临场赔率和缺失情报；赛后用于验证系统是否过度拒绝组合。"
    )
    if gate.get("combo_gate") == "closed":
        reason += " 当前可信度门控关闭，因此只保留纸面候选。"
    return {
        "type": f"parlay_{leg_count}x1",
        "candidate_type": f"parlay_{leg_count}x1",
        "label_zh": f"每日{label}纸面候选",
        "match": "",
        "legs": "；".join(str(leg.get("match") or leg.get("legs") or "").strip() for leg in legs if str(leg.get("match") or leg.get("legs") or "").strip()),
        "play_type_zh": play_mix,
        "play_type_mix_zh": play_mix,
        "direction_family_zh": direction_mix,
        "leg_play_types": [str(leg.get("play_type_zh") or "") for leg in legs],
        "leg_directions": [str(leg.get("direction_family_zh") or _broad_direction(leg)) for leg in legs],
        "odds": round(odds, 4),
        "model_prob": round(model_prob, 6),
        "market_prob": round(market_prob, 6),
        "ev": round(ev, 6),
        "edge": round(edge, 6),
        "confidence_score": min(confidences) if confidences else 0.45,
        "correlation_discount": correlation_discount,
        "risk_level": risk,
        "risk_adjusted_score": round(ev - (0.18 if leg_count == 2 else 0.32), 6),
        "combo_score": round(ev, 6),
        "safety_score": round(correlation_discount - (0.18 if risk == "high" else 0.32), 6),
        "paper_stake": 0.0,
        "selected": False,
        "status": "纸面候选",
        "reject_reason": reason,
        "selected_reason_zh": reason,
        "hit_rate_discipline_zh": f"{label}需要 {leg_count} 条同时命中；当前只作纸面候选。",
        "best_parlay_quality": {
            "ev_pass": ev > 0,
            "confidence_pass": False,
            "correlation_pass": correlation_discount >= 0.95,
            "risk_pass": False,
            "information_pass": False,
            "final_status": "daily_candidate",
            "reason_zh": "由单关合成的每日纸面候选，未通过完整组合纪律。",
        },
        "paper_candidate_warning_zh": "这是强制输出的纸面候选，用于赛后验证，不代表强观察。",
    }


def _diverse_singles_for_combo(rows: list[dict], count: int) -> list[dict]:
    picked = []
    seen_direction = set()
    ordered = sorted(rows, key=lambda item: _float(item.get("risk_adjusted_score"), -999), reverse=True)
    # Prefer broad-direction diversity first. If the slate is full of the same
    # 主胜/让胜 direction, we still fill the daily paper lane in the second pass,
    # but we do not pretend that the combo is diversified.
    for row in ordered:
        direction = _broad_direction(row)
        if direction in seen_direction:
            continue
        picked.append(row)
        seen_direction.add(direction)
        if len(picked) >= count:
            return picked
    for row in ordered:
        if row not in picked:
            picked.append(row)
        if len(picked) >= count:
            return picked
    return picked


def _diversity_bonus(row: dict, risk: str) -> float:
    if not row.get("legs"):
        return 0.0
    play_mix = str(row.get("play_type_zh") or row.get("play_type_mix_zh") or "")
    direction_mix = str(row.get("direction_family_zh") or "")
    leg_play_types = [x for x in (row.get("leg_play_types") or []) if str(x).strip()]
    leg_directions = [x for x in (row.get("leg_directions") or []) if str(x).strip()]
    play_unique = len(set(leg_play_types)) if leg_play_types else len([x for x in play_mix.split("+") if x.strip()])
    direction_unique = len(set(leg_directions)) if leg_directions else len([x for x in direction_mix.split("+") if x.strip()])
    bonus = 0.0
    if play_unique >= 2:
        bonus += 0.16
    if direction_unique >= 2:
        bonus += 0.14
    if play_unique <= 1 and direction_unique <= 1:
        bonus -= 0.18
    if risk in {"high", "very_high"}:
        bonus -= 0.04
    text = " ".join([play_mix, direction_mix, str(row.get("combo_homogeneity_reason_zh") or "")])
    if "同玩法" in text or "同方向" in text or "同质化" in text:
        bonus -= 0.08
    return bonus


def _unique_join(values: list[str]) -> str:
    out = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return " + ".join(out)


def _split_mix(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split("+") if part.strip()]


def _broad_direction(row: dict) -> str:
    text = str(row.get("match") or row.get("legs") or "").lower()
    if "让胜" in text or "主胜" in text or "home" in text:
        return "home"
    if "让负" in text or "客胜" in text or "away" in text:
        return "away"
    if "让平" in text or "平" in text or "draw" in text:
        return "draw"
    if "大" in text or "over" in text:
        return "over"
    if "小" in text or "under" in text:
        return "under"
    return text[:16]


def _user_combo_board(
    *,
    gate: dict,
    best_single: dict,
    best_2x1: dict,
    best_3x1: dict,
    daily_2x1: dict,
    daily_3x1: dict,
    best_risk_adjusted: dict,
    selected_combos: list[dict],
    rejected: list[dict],
    no_combo_reason: str,
) -> dict:
    has_selected_combo = bool(selected_combos)
    gate_label = gate.get("label_zh") or ("允许组合" if has_selected_combo else "不建议串联")
    if has_selected_combo:
        headline = "今日存在可研究组合"
        verdict = "先看风险调整最佳组合，再复核每条腿的赔率、情报和相关性。"
        action = "查看强观察组合"
    else:
        headline = "今日不强行组合"
        verdict = no_combo_reason or "当前组合风险高于模型优势，先看单关和最接近但未通过的 2串1。"
        action = "先看单关，等待情报或赔率变化"
    nearest_combo = best_risk_adjusted if _is_real_candidate(best_risk_adjusted) else daily_2x1
    return {
        "headline_zh": headline,
        "gate_label_zh": gate_label,
        "user_verdict_zh": verdict,
        "primary_action_zh": action,
        "best_single_card": _combo_user_card("当前优先单关", best_single),
        "best_2x1_card": _combo_user_card("每日 2串1候选", daily_2x1),
        "best_3x1_card": _combo_user_card("每日 3串1候选", daily_3x1),
        "best_risk_adjusted_card": _combo_user_card("风险调整最佳组合", nearest_combo),
        "nearest_rejected_reason_zh": _nearest_rejected_reason(rejected),
        "ai_research_prompt_zh": _ai_research_prompt(best_single, nearest_combo, has_selected_combo),
        "what_to_check_next": _what_to_check_next(has_selected_combo, nearest_combo),
        "closing_line_review": _closing_line_review(has_selected_combo, best_single, nearest_combo),
    }


def _combo_user_card(title: str, item: dict) -> dict:
    if not _is_real_candidate(item):
        return {
            "title": title,
            "status_zh": "暂无合格候选",
            "main_zh": item.get("message_zh") or item.get("reject_reason") or "没有可排序候选。",
            "odds_zh": "N/A",
            "probability_zh": "N/A",
            "value_zh": "等待更可靠数据",
            "reason_zh": item.get("reject_reason") or item.get("message_zh") or "未通过纪律筛选。",
        }
    odds = _float(item.get("odds"))
    model_prob = _float(item.get("model_prob"))
    break_even = 1.0 / odds if odds > 1 else 0.0
    margin = model_prob - break_even if odds > 1 else None
    status = "通过门控" if _is_pass_status(item.get("status"), selected=bool(item.get("selected"))) else "未过门控"
    value = "覆盖赔率" if margin is not None and margin > 0 else "未覆盖赔率"
    if item.get("risk_level") in {"high", "very_high"}:
        value += "，风险偏高"
    return {
        "title": title,
        "status_zh": status,
        "main_zh": item.get("legs") or item.get("match") or "观察候选",
        "odds_zh": f"{odds:.2f}" if odds else "N/A",
        "probability_zh": f"{model_prob:.1%}" if model_prob else "N/A",
        "break_even_zh": f"{break_even:.1%}" if break_even else "N/A",
        "margin_zh": f"{margin:+.1%}" if margin is not None else "N/A",
        "value_zh": value,
        "reason_zh": item.get("selected_reason_zh") or item.get("reject_reason") or item.get("hit_rate_discipline_zh") or "查看纪律拆解。",
    }


def _is_real_candidate(item: dict) -> bool:
    return bool(item) and item.get("status") != "empty" and _float(item.get("odds")) > 1.01


def _has_candidate_identity(item: dict) -> bool:
    return bool(item) and item.get("status") != "empty" and bool(item.get("legs") or item.get("match") or item.get("message_zh"))


def _daily_candidate(item: dict, gate: dict, kind: str = "combo") -> dict:
    if not _is_real_candidate(item):
        return item
    candidate = dict(item)
    combo_gate = gate.get("combo_gate")
    if candidate.get("status") != "通过门控":
        candidate["daily_candidate"] = True
        candidate["status"] = "纸面候选" if kind != "single" else candidate.get("status", "纸面候选")
        candidate["label_zh"] = candidate.get("label_zh") or ("每日单关候选" if kind == "single" else "每日纸面候选")
        if not candidate.get("selected_reason_zh"):
            candidate["selected_reason_zh"] = (
                "每日必须输出的纸面候选：用于复盘赔率、联合概率、相关性和缺失情报，不代表通过纪律门控。"
                if kind != "single"
                else "每日必须输出的单关候选：先看赔率价值、模型概率和情报缺口，再决定是否进入后续观察。"
            )
        candidate["reject_reason"] = candidate.get("reject_reason") or gate.get("reason_zh") or "未通过可信度门控。"
        quality = dict(candidate.get("best_parlay_quality") or {})
        quality["final_status"] = "daily_candidate" if kind != "single" else "single_candidate"
        quality["reason_zh"] = candidate["reject_reason"]
        candidate["best_parlay_quality"] = quality
        candidate["paper_candidate_warning_zh"] = (
            "这是每日强制输出的纸面组合候选，不等于已通过纪律门控。"
            if kind != "single"
            else "这是每日强制输出的单关候选，仍需看情报完整度与临场赔率。"
        )
    return candidate


def _daily_output_conclusion(daily_single: dict, daily_2x1: dict, daily_3x1: dict, gate: dict, no_combo_reason: str | None) -> str:
    bits = []
    if _is_real_candidate(daily_single):
        bits.append("已输出最推荐单关")
    if _is_real_candidate(daily_2x1):
        bits.append("已输出最推荐2串1纸面候选")
    if _is_real_candidate(daily_3x1):
        bits.append("已输出最推荐3串1纸面候选")
    if not bits:
        return ""
    gate_label = gate.get("label_zh") or "纪律门控"
    reason = no_combo_reason or gate.get("reason_zh") or "仍需复核可信度、情报和组合风险。"
    return "；".join(bits) + f"。当前{gate_label}，这些候选用于 T+1 分析和赛后学习；{reason}"


def _nearest_rejected_reason(rejected: list[dict]) -> str:
    if not rejected:
        return "当前没有被拒候选可展示。"
    item = sorted(rejected, key=lambda row: _float(row.get("risk_adjusted_score"), default=-999), reverse=True)[0]
    return item.get("reject_reason") or item.get("opposing_factors_zh") or "未通过组合纪律。"


def _ai_research_prompt(best_single: dict, nearest_combo: dict, has_selected_combo: bool) -> str:
    combo_text = nearest_combo.get("legs") or nearest_combo.get("match") or "暂无组合"
    single_text = best_single.get("match") or best_single.get("legs") or "暂无单关"
    mode = "复核通过门控组合是否真的值得纸面观察" if has_selected_combo else "解释为什么当前不应强行串联"
    return (
        f"DeepSeek 可选研究层应{mode}：先检查 {single_text}，再检查 {combo_text}，"
        "重点看赔率是否覆盖概率、是否有情报缺口、是否被冷门或相关性误导。"
    )


def _what_to_check_next(has_selected_combo: bool, nearest_combo: dict) -> list[str]:
    checks = [
        "复核每条腿是否都有有效赔率和正安全边际。",
        "确认伤停、首发、天气、新闻面是否仍缺失或只是兜底估算。",
        "观察临近开赛赔率是否继续支持该方向，而不是反向漂移。",
    ]
    if has_selected_combo:
        checks.insert(0, "先看风险调整最佳组合，不要只看最高组合赔率。")
    else:
        checks.insert(0, "没有合格组合时，不要为了组合赔率强行拼串。")
        if _is_real_candidate(nearest_combo):
            checks.append("最接近组合只能作为被拒复盘对象，不能升级为强观察。")
    return checks


def _closing_line_review(has_selected_combo: bool, best_single: dict, nearest_combo: dict) -> dict:
    target = nearest_combo if _is_real_candidate(nearest_combo) else best_single
    target_label = target.get("legs") or target.get("match") or "当前 Top 观察"
    odds = _float(target.get("odds"))
    model_prob = _float(target.get("model_prob"))
    break_even = 1.0 / odds if odds > 1 else 0.0
    margin = model_prob - break_even if odds > 1 else None
    return {
        "title_zh": "临场赔率复核",
        "target_zh": target_label,
        "current_value_zh": f"当前赔率 {odds:.2f}，盈亏线 {break_even:.1%}，模型概率 {model_prob:.1%}，安全边际 {margin:+.1%}。" if margin is not None else "当前缺少可计算赔率或概率。",
        "why_zh": "赛前预观察不能只看当前赔率。临近开赛如果赔率明显反向漂移，说明市场后来不再支持该方向，需要降级。",
        "green_light_zh": "如果临近开赛赔率没有明显反向漂移，且伤停/首发/天气没有新增反对因素，可以继续保留纸面观察。",
        "downgrade_zh": "如果赔率上升但模型没有新信息支持，或关键情报转差，应从强观察降为弱观察或跳过。",
        "combo_note_zh": "组合比单关更依赖终盘确认；即使当前有组合，也要逐腿复核，不要只看组合赔率。",
        "status_zh": "组合复核" if has_selected_combo else "单关优先复核",
    }


def _gate_empty(gate: dict) -> dict:
    return {
        "status": "no_combo",
        "message_zh": "暂无优秀串联观察",
        "reject_reason": gate.get("reason_zh", "可信度不足、情报缺失较多、组合风险高于模型优势。"),
        "best_parlay_quality": {"final_status": "no_combo", "reason_zh": gate.get("reason_zh", "未通过可信度门控。")},
    }


def _quality(
    ev: float,
    edge: float,
    confidence: float,
    correlation: float,
    risk: str,
    status: str,
    hard_invalid: bool,
    hit_rate_pass: bool = True,
) -> dict:
    ev_pass = ev >= 0.025 and edge >= 0.015
    confidence_pass = confidence >= 0.55
    correlation_pass = correlation >= 0.95
    risk_pass = risk not in {"high", "very_high"}
    information_pass = confidence >= 0.50
    final_status = "selected" if status == "通过门控" and all([ev_pass, confidence_pass, correlation_pass, risk_pass, information_pass, hit_rate_pass]) and not hard_invalid else "rejected"
    if hard_invalid:
        final_status = "rejected"
    return {
        "ev_pass": ev_pass,
        "confidence_pass": confidence_pass,
        "correlation_pass": correlation_pass,
        "risk_pass": risk_pass,
        "information_pass": information_pass,
        "hit_rate_pass": hit_rate_pass,
        "final_status": final_status,
        "reason_zh": _quality_reason(ev_pass, confidence_pass, correlation_pass, risk_pass, information_pass, hit_rate_pass, hard_invalid),
    }


def _quality_reason(
    ev_pass: bool,
    confidence_pass: bool,
    correlation_pass: bool,
    risk_pass: bool,
    information_pass: bool,
    hit_rate_pass: bool,
    hard_invalid: bool,
) -> str:
    if hard_invalid:
        return "该组合赔率/结构无效或同场互斥，不能作为优秀串联。"
    failed = []
    if not ev_pass:
        failed.append("EV/Edge 不足")
    if not confidence_pass:
        failed.append("可信度不足")
    if not correlation_pass:
        failed.append("相关性折扣不通过")
    if not risk_pass:
        failed.append("风险过高")
    if not information_pass:
        failed.append("情报不足")
    if not hit_rate_pass:
        failed.append("组合命中率纪律不通过")
    return "通过优秀串联质量检查。" if not failed else "不是赔率不够，而是" + "、".join(failed) + "。"


def _hit_rate_floor(kind: str) -> float:
    if kind == "parlay_2x1":
        return 0.20
    if kind == "parlay_3x1":
        return 0.12
    return 0.0


def _hit_rate_message(kind: str, probability: float, floor: float) -> str:
    if kind == "single":
        return "单关优先观察概率、赔率价值和情报完整度。"
    if probability < floor:
        return f"组合命中概率 {probability:.1%} 低于纪律门槛 {floor:.0%}，不应强行串联。"
    return f"组合命中概率 {probability:.1%} 通过最低纪律门槛 {floor:.0%}，仍需结合可信度和相关性。"


def _conclusion(singles: list[dict], parlay2: list[dict], parlay3: list[dict]) -> str:
    best2 = _best(parlay2, "risk_adjusted_score")
    best3 = _best(parlay3, "risk_adjusted_score")
    if best2.get("status") == "通过门控":
        return "当前存在 2串1 纸面观察，但仍需重点查看相关性折扣、缺失情报和回撤风险。"
    if best2.get("status") == "未过门控":
        return f"当前最优2串1组合未通过纪律门控，首要原因：{best2.get('reject_reason', '未通过组合纪律')}"
    if singles:
        return "当前最优观察主要来自单关，不宜为了组合赔率强行串联。"
    if best3.get("status") == "未过门控":
        return f"3串1 风险更高，当前不建议启用；原因：{best3.get('reject_reason', '未通过组合纪律')}"
    return "当前候选不足，严格交易者结论为等待更可靠数据。"


def _selected_reason(ev, edge, confidence, correlation, risk) -> str:
    return f"EV {ev:.1%}、Edge {edge:.1%}、可信度 {confidence:.1%}、相关性折扣 {correlation:.2f}、风险 {risk}。"


def _opposing_factors(row: dict, model_prob: float, market_prob: float, confidence: float, risk: str) -> str:
    factors = []
    if model_prob and market_prob and abs(model_prob - market_prob) < 0.02:
        factors.append("模型与市场差距较薄")
    if confidence < 0.55:
        factors.append("外部情报不足导致信心不高")
    if risk in {"high", "very_high"}:
        factors.append("风险等级偏高")
    if row.get("reject_reason"):
        factors.append(str(row.get("reject_reason")))
    return "；".join(dict.fromkeys(factors)) or "暂无明显反对因素，但仍需遵守纸面观察纪律。"


def _row_key(row: dict) -> str:
    return "|".join(str(row.get(key, "")) for key in ("type", "match", "legs", "odds", "model_prob"))


def _type_label(kind: str) -> str:
    return {"single": "单关", "parlay_2x1": "2串1", "parlay_3x1": "3串1"}.get(kind, kind)


def _match_label(row: dict) -> str:
    return f"{row.get('home_team', '')} vs {row.get('away_team', '')} {row.get('outcome_label', '')}".strip()


def _legs_label(row: dict) -> str:
    legs = row.get("legs") or []
    if isinstance(legs, str):
        return legs
    return "；".join(_match_label(leg) for leg in legs)


def _float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fmt_num(value) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_pct(value) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_signed_pct(value) -> str:
    try:
        return f"{float(value):+.1%}"
    except (TypeError, ValueError):
        return "N/A"

from __future__ import annotations

from collections import Counter


PLAY_LABELS = {
    "had": "胜平负",
    "hhad": "让球胜平负",
    "total_goals": "总进球",
    "correct_score": "比分",
}


def diagnose_play_bias(candidate_rankings: dict | None) -> dict:
    rankings = candidate_rankings or {}
    singles = list(rankings.get("singles") or [])
    parlay_2x1 = list(rankings.get("parlay_2x1") or [])
    parlay_3x1 = list(rankings.get("parlay_3x1") or [])
    single_diag = _diagnose_rows(singles, "单关候选")
    parlay2_diag = _diagnose_combo_rows(parlay_2x1, "2串1候选")
    parlay3_diag = _diagnose_combo_rows(parlay_3x1, "3串1候选")
    issues = [item for item in (single_diag, parlay2_diag, parlay3_diag) if item.get("status") in {"concentrated", "very_concentrated"}]
    return {
        "status": "biased" if issues else "balanced",
        "label_zh": "存在玩法偏置" if issues else "玩法分布暂未明显偏置",
        "summary_zh": _summary(issues),
        "sections": [single_diag, parlay2_diag, parlay3_diag],
        "issues": issues,
        "next_step_zh": "如果让球胜平负或同方向长期扎堆，需要提高玩法分散惩罚，并用赛后样本验证该玩法是否真的更有效。",
    }


def _diagnose_rows(rows: list[dict], label: str) -> dict:
    plays = Counter(_play(row) for row in rows)
    directions = Counter(_direction_key(row) for row in rows)
    return _diagnosis(label, len(rows), plays, directions)


def _diagnose_combo_rows(rows: list[dict], label: str) -> dict:
    plays = Counter()
    directions = Counter()
    legs_count = 0
    for row in rows:
        legs = row.get("legs") or []
        if isinstance(legs, str):
            play_mix = str(row.get("play_type_mix_zh") or "")
            for part in [text.strip() for text in play_mix.split("+") if text.strip()]:
                plays[part] += 1
                legs_count += 1
            continue
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            plays[_play(leg)] += 1
            directions[_direction_key(leg)] += 1
            legs_count += 1
    return _diagnosis(label, legs_count, plays, directions)


def _diagnosis(label: str, total: int, plays: Counter, directions: Counter) -> dict:
    top_play, top_play_count = _top_count(plays)
    top_direction, top_direction_count = _top_count(directions)
    play_share = top_play_count / total if total else 0.0
    direction_share = top_direction_count / total if total else 0.0
    status = "very_concentrated" if play_share >= 0.80 and total >= 3 else "concentrated" if play_share >= 0.62 and total >= 3 else "balanced"
    if status == "very_concentrated":
        message = f"{label}高度集中在{top_play}（{play_share:.0%}），需要警惕玩法偏置。"
    elif status == "concentrated":
        message = f"{label}偏向{top_play}（{play_share:.0%}），建议检查是否只是赔率结构导致。"
    elif total:
        message = f"{label}玩法分布暂可接受，最高占比 {play_share:.0%}。"
    else:
        message = f"{label}暂无足够样本判断玩法偏置。"
    return {
        "label_zh": label,
        "status": status,
        "total_count": total,
        "top_play_type": top_play,
        "top_play_share": round(play_share, 6),
        "top_direction": top_direction,
        "top_direction_share": round(direction_share, 6),
        "play_counts": dict(plays),
        "direction_counts": dict(directions),
        "message_zh": message,
        "suggestion_zh": _suggestion(status, top_play, top_direction),
    }


def _summary(issues: list[dict]) -> str:
    if not issues:
        return "候选暂未明显集中在单一玩法；仍需赛后验证各玩法命中率。"
    first = issues[0]
    return f"{first.get('label_zh')} 出现偏置：{first.get('message_zh')} 这可能解释为什么页面经常出现同类方向。"


def _suggestion(status: str, top_play: str, top_direction: str) -> str:
    if status == "very_concentrated":
        return f"提高 {top_play} 同类腿惩罚，要求组合至少混入不同玩法；赛后按玩法统计命中率再决定是否放宽。"
    if status == "concentrated":
        return f"保留 {top_play} 候选，但降低同方向扎堆排序权重，优先展示玩法分散组合。"
    return "继续按玩法、方向和赔率段保存赛后样本，避免凭单日直觉调权重。"


def _play(row: dict) -> str:
    raw = str(row.get("play_type") or row.get("play_type_zh") or row.get("type") or "unknown")
    return PLAY_LABELS.get(raw, raw)


def _direction_key(row: dict) -> str:
    play = _play(row)
    direction = str(row.get("direction_family_zh") or row.get("direction") or row.get("outcome_label") or row.get("outcome_key") or "")
    return f"{play}·{direction}".strip("·")


def _top_count(counter: Counter) -> tuple[str, int]:
    if not counter:
        return "暂无", 0
    return counter.most_common(1)[0]

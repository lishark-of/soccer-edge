from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

from src.learning.competition_segments import classify_competition_segment
from src.market.clv import load_observations_json
from src.learning.result_feedback import build_feedback_report


def load_results_csv(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            home_goals = _int(raw.get("home_goals"))
            away_goals = _int(raw.get("away_goals"))
            if home_goals is None or away_goals is None:
                continue
            home = _first(raw, "home_team", "home", "主队")
            away = _first(raw, "away_team", "away", "客队")
            outcome = "home" if home_goals > away_goals else "away" if away_goals > home_goals else "draw"
            rows.append({
                "date": _first(raw, "date", "match_date", "日期"),
                "league": _first(raw, "league", "competition", "赛事", "联赛"),
                "match_id": _first(raw, "match_id", "id"),
                "match_no": _first(raw, "match_no", "num", "编号"),
                "match": _first(raw, "match") or f"{home} vs {away}".strip(),
                "home_team": home,
                "away_team": away,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "result": {
                    "score": f"{home_goals}-{away_goals}",
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "actual_outcome": outcome,
                    "actual_outcome_zh": {"home": "主胜", "draw": "平", "away": "客胜"}[outcome],
                    "actual_handicap_outcome_zh": _first(raw, "actual_handicap_outcome_zh", "handicap_result", "让球结果") or "未知",
                    "total_goals": home_goals + away_goals,
                },
            })
    return rows


def build_feedback_from_files(observations_json: str | Path, results_csv: str | Path, date: str | None = None) -> dict:
    observations = load_observations_json(observations_json)
    results = load_results_csv(results_csv)
    return build_feedback_from_observations_and_results(observations, results, date=date)


def save_feedback_from_files(
    observations_json: str | Path,
    results_csv: str | Path,
    date: str | None = None,
    output_dir: str | Path = "data/learning_feedback",
) -> dict:
    feedback = build_feedback_from_files(observations_json, results_csv, date=date)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_date = str(feedback.get("date") or date or datetime.now().strftime("%Y%m%d")).replace("/", "-").replace(" ", "_")
    path = directory / f"feedback_{safe_date}_{datetime.now().strftime('%H%M%S')}.json"
    path.write_text(json.dumps(feedback, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": "saved",
        "path": str(path),
        "feedback": feedback,
        "summary_zh": "已保存到本地学习库；下次刷新累计学习时会参与赔率段和概率段校准。",
        "privacy_zh": "文件只保存在本机 data/learning_feedback/，该目录已加入 gitignore。",
        "disclaimer": "赛后学习只用于模型校准和纸面复盘，不构成任何真实投注建议。",
    }


def build_feedback_from_observations_and_results(observations: list[dict], results: list[dict], date: str | None = None) -> dict:
    matches: list[dict] = []
    unmatched_observations: list[dict] = []
    rejected_combo_reviews: list[dict] = []
    grouped: dict[int, list[dict]] = {idx: [] for idx, _ in enumerate(results)}
    match_quality: dict[int, list[float]] = {idx: [] for idx, _ in enumerate(results)}
    for obs in observations or []:
        if obs.get("learning_track") == "rejected_combo" and obs.get("legs"):
            rejected_combo_reviews.append(_build_rejected_combo_review(obs, results))
            continue
        idx, score = _best_result_match(obs, results)
        if idx is None or score < 0.58:
            unmatched_observations.append(_compact_observation(obs, match_score=score))
            continue
        grouped[idx].append(_compact_observation(obs, match_score=score))
        match_quality[idx].append(score)
    for idx, result in enumerate(results):
        if not grouped.get(idx):
            continue
        matches.append({
            "match": result.get("match") or f"{result.get('home_team','')} vs {result.get('away_team','')}",
            "date": result.get("date") or date,
            "league": result.get("league"),
            "match_id": result.get("match_id"),
            "match_no": result.get("match_no"),
            "home_team": result.get("home_team"),
            "away_team": result.get("away_team"),
            "match_confidence": round(sum(match_quality[idx]) / len(match_quality[idx]), 4) if match_quality[idx] else None,
            "result": result.get("result", {}),
            "observations": grouped[idx],
        })
    feedback = {
        "date": date or _first_non_empty([row.get("date") for row in results]),
        "source": "built_from_observations_and_results",
        "matches": matches,
        "unmatched_observations": unmatched_observations,
        "rejected_combo_reviews": rejected_combo_reviews,
        "results_without_observations": [
            {
                "match": row.get("match"),
                "score": (row.get("result") or {}).get("score"),
            }
            for idx, row in enumerate(results)
            if not grouped.get(idx)
        ],
        "builder_summary": {
            "observations_loaded": len(observations or []),
            "results_loaded": len(results or []),
            "matched_observations": sum(len(value) for value in grouped.values()),
            "unmatched_observations": len(unmatched_observations),
            "rejected_combo_reviews": len(rejected_combo_reviews),
            "matches_with_observations": len(matches),
            "message_zh": "已把赛前观察和赛果匹配成学习反馈；未匹配项不会被强行归因。",
        },
        "disclaimer": "自动匹配只用于赛后学习和模型校准，不构成任何真实投注建议。",
    }
    feedback["report"] = build_feedback_report(feedback)
    return feedback


def _build_rejected_combo_review(obs: dict, results: list[dict]) -> dict:
    leg_reviews: list[dict] = []
    for leg in obs.get("legs") or []:
        idx, score = _best_result_match(leg, results)
        result = results[idx] if idx is not None and score >= 0.58 else {}
        hit = None
        if result:
            from src.learning.result_feedback import evaluate_observation_hit

            hit = evaluate_observation_hit(leg, result.get("result", {}) or {})
        leg_reviews.append({
            "match": leg.get("match") or f"{leg.get('home_team','')} vs {leg.get('away_team','')}".strip(),
            "play_type": leg.get("play_type"),
            "direction": leg.get("direction") or leg.get("outcome_label"),
            "match_score": round(float(score or 0.0), 4),
            "matched": bool(result),
            "hit": hit,
            "score": (result.get("result") or {}).get("score") if result else "",
        })
    settled = [row for row in leg_reviews if row.get("hit") is not None]
    combo_hit = bool(settled) and len(settled) == len(leg_reviews) and all(row.get("hit") for row in settled)
    combo_miss = bool(settled) and any(row.get("hit") is False for row in settled)
    return {
        "learning_track": "rejected_combo",
        "type": obs.get("type") or obs.get("candidate_type"),
        "match": obs.get("match"),
        "odds": obs.get("odds"),
        "model_prob": obs.get("model_prob"),
        "risk_level": obs.get("risk_level"),
        "reject_reason": obs.get("reject_reason"),
        "legs_count": len(leg_reviews),
        "settled_legs_count": len(settled),
        "combo_hit": combo_hit if len(settled) == len(leg_reviews) else None,
        "combo_miss": combo_miss if len(settled) == len(leg_reviews) else None,
        "leg_reviews": leg_reviews,
        "discipline_verdict_zh": _rejected_combo_verdict(combo_hit, combo_miss, len(settled), len(leg_reviews)),
        "rule_adjustment_suggestions": _rule_adjustment_suggestions(obs, combo_hit, combo_miss, len(settled), len(leg_reviews)),
    }


def _rejected_combo_verdict(combo_hit: bool, combo_miss: bool, settled_count: int, legs_count: int) -> str:
    if settled_count < legs_count:
        return "部分腿未匹配赛果，暂不能判断拒绝规则是否过严。"
    if combo_hit:
        return "该被拒组合赛后全部命中，需要复查当时的拒绝原因是否过严。"
    if combo_miss:
        return "该被拒组合赛后未全部命中，当前拒绝纪律得到一次支持。"
    return "赛后结果中性，继续累计样本。"


def _rule_adjustment_suggestions(obs: dict, combo_hit: bool, combo_miss: bool, settled_count: int, legs_count: int) -> list[dict]:
    if settled_count < legs_count or not combo_hit:
        return []
    reason = str(obs.get("reject_reason") or "")
    suggestions: list[dict] = []
    if "Edge 不足" in reason or "EV 不足" in reason or "安全边际" in reason:
        suggestions.append({
            "rule": "edge_ev_threshold",
            "label_zh": "Edge / EV 门槛可能偏紧",
            "suggestion_zh": "不要直接降低门槛；先观察同类被拒组合是否连续全中，再考虑按赔率段微调阈值。",
        })
    if "相关性" in reason:
        suggestions.append({
            "rule": "correlation_discount",
            "label_zh": "相关性折扣可能偏重",
            "suggestion_zh": "检查两腿是否真的高度相关；若来自不同赛事/不同球队风格，可考虑降低相关性折扣。",
        })
    if "风险" in reason or str(obs.get("risk_level") or "").lower() in {"high", "very_high"}:
        suggestions.append({
            "rule": "risk_penalty",
            "label_zh": "风险惩罚可能偏重",
            "suggestion_zh": "高风险组合即使赛后全中也不能立刻放宽；需要更多样本确认不是偶然。",
        })
    if "可信度" in reason or "情报" in reason:
        suggestions.append({
            "rule": "credibility_gate",
            "label_zh": "可信度门控可能过严",
            "suggestion_zh": "优先补伤停、首发、天气、新闻和终盘赔率；若补齐后同类组合仍被拒且长期全中，再调整门控。",
        })
    if not suggestions:
        suggestions.append({
            "rule": "unknown_reject_reason",
            "label_zh": "拒绝原因需要更细分",
            "suggestion_zh": "该组合赛后全中，但拒绝原因不够结构化；后续应把拒绝原因拆成 Edge、相关性、风险、可信度等标签。",
        })
    return suggestions


def _best_result_match(obs: dict, results: list[dict]) -> tuple[int | None, float]:
    best_idx: int | None = None
    best_score = 0.0
    obs_id = str(obs.get("match_id") or "").strip()
    obs_no = str(obs.get("match_no") or "").strip()
    obs_home = str(obs.get("home_team") or "")
    obs_away = str(obs.get("away_team") or "")
    obs_match = str(obs.get("match") or "")
    for idx, result in enumerate(results):
        if obs_id and obs_id == str(result.get("match_id") or "").strip():
            return idx, 1.0
        if obs_no and obs_no == str(result.get("match_no") or "").strip():
            return idx, 0.98
        home_score = _name_score(obs_home, str(result.get("home_team") or ""))
        away_score = _name_score(obs_away, str(result.get("away_team") or ""))
        direct_score = (home_score + away_score) / 2.0 if obs_home or obs_away else 0.0
        match_score = _name_score(obs_match, str(result.get("match") or "")) if obs_match else 0.0
        score = max(direct_score, match_score)
        if score > best_score:
            best_score = score
            best_idx = idx
    return best_idx, best_score


def _compact_observation(obs: dict, match_score: float | None = None) -> dict:
    segment = classify_competition_segment(obs)
    return {
        "date": obs.get("date"),
        "league": obs.get("league") or obs.get("competition") or obs.get("tournament"),
        "match_id": obs.get("match_id"),
        "match_no": obs.get("match_no"),
        "home_team": obs.get("home_team"),
        "away_team": obs.get("away_team"),
        "match": obs.get("match") or _match_label(obs),
        "play_type": obs.get("play_type") or obs.get("type"),
        "direction": obs.get("direction") or obs.get("outcome_label"),
        "outcome_label": obs.get("outcome_label") or obs.get("direction"),
        "odds": obs.get("odds") or obs.get("official_odds") or obs.get("combo_odds"),
        "model_prob": obs.get("model_prob") or obs.get("combo_prob"),
        "market_prob": obs.get("market_prob"),
        "ev": obs.get("ev"),
        "edge": obs.get("edge"),
        "confidence_score": obs.get("confidence_score") or obs.get("observation_confidence"),
        "paper_stake": obs.get("paper_stake") or obs.get("suggested_paper_stake"),
        "learning_track": obs.get("learning_track"),
        "status": obs.get("status"),
        "reject_reason": obs.get("reject_reason"),
        "risk_level": obs.get("risk_level"),
        "candidate_type": obs.get("candidate_type") or obs.get("type"),
        "legs": obs.get("legs") or [],
        "match_score": round(float(match_score or 0.0), 4),
        **segment,
    }


def _match_label(obs: dict) -> str:
    home = obs.get("home_team") or ""
    away = obs.get("away_team") or ""
    return f"{home} vs {away}".strip()


def _name_score(a: str, b: str) -> float:
    left = _normalize_name(a)
    right = _normalize_name(b)
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right).ratio()


def _normalize_name(value: str) -> str:
    return "".join(str(value or "").lower().replace("队", "").split())


def _first(row: dict, *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _first_non_empty(values: list[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _int(value) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None

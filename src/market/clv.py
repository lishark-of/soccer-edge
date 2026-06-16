from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from statistics import mean


DISCLAIMER = "CLV/收盘赔率跟踪仅用于赛前研究复盘，不构成投注建议。"


def observation_key(observation: dict) -> str:
    parts = [
        observation.get("match_id") or observation.get("match_no") or observation.get("match") or "",
        observation.get("play_type") or observation.get("type") or "",
        observation.get("outcome_key") or observation.get("direction") or observation.get("outcome_label") or "",
    ]
    return "|".join(str(part).strip() for part in parts)


def implied_probability(decimal_odds: float | int | str | None) -> float | None:
    odds = _float(decimal_odds)
    if odds is None or odds <= 1.0:
        return None
    return round(1.0 / odds, 6)


def calculate_clv(entry_odds: float | int | str | None, closing_odds: float | int | str | None) -> dict:
    entry = _float(entry_odds)
    closing = _float(closing_odds)
    if entry is None or entry <= 1.0:
        return {
            "status": "missing_entry_odds",
            "label_zh": "缺少入场赔率",
            "clv_pct": None,
            "message_zh": "该观察项没有可比较的官方赔率，暂不能跟踪收盘赔率。",
        }
    if closing is None or closing <= 1.0:
        return {
            "status": "pending_closing_odds",
            "label_zh": "等待收盘赔率",
            "entry_odds": entry,
            "closing_odds": None,
            "entry_implied_prob": implied_probability(entry),
            "closing_implied_prob": None,
            "clv_pct": None,
            "message_zh": "已记录赛前赔率，等待临近开赛或赛后补充收盘赔率后评估 CLV。",
        }
    clv_pct = entry / closing - 1.0
    return {
        "status": "positive_clv" if clv_pct > 0 else ("negative_clv" if clv_pct < 0 else "flat_clv"),
        "label_zh": "跑赢收盘赔率" if clv_pct > 0 else ("弱于收盘赔率" if clv_pct < 0 else "与收盘赔率持平"),
        "entry_odds": round(entry, 4),
        "closing_odds": round(closing, 4),
        "entry_implied_prob": implied_probability(entry),
        "closing_implied_prob": implied_probability(closing),
        "clv_pct": round(clv_pct, 6),
        "message_zh": _clv_message(clv_pct),
    }


def build_clv_tracking(observations: list[dict], closing_odds_by_key: dict | None = None) -> dict:
    closing_map = closing_odds_by_key or {}
    rows = []
    for observation in observations or []:
        key = observation_key(observation)
        entry_odds = observation.get("odds") or observation.get("official_odds") or observation.get("combo_odds")
        closing_odds = closing_map.get(key)
        clv = calculate_clv(entry_odds, closing_odds)
        rows.append(
            {
                "key": key,
                "date": observation.get("date") or observation.get("selected_date"),
                "match": observation.get("match") or _match_label(observation),
                "play": observation.get("play_type") or observation.get("type") or "",
                "direction": observation.get("outcome_label") or observation.get("direction") or "",
                **clv,
            }
        )
    settled = [row for row in rows if isinstance(row.get("clv_pct"), float)]
    return {
        "tracking_version": "phase2r_clv_v0",
        "tracked_count": len(rows),
        "settled_count": len(settled),
        "pending_count": len([row for row in rows if row.get("status") == "pending_closing_odds"]),
        "positive_clv_count": len([row for row in settled if row.get("clv_pct", 0) > 0]),
        "negative_clv_count": len([row for row in settled if row.get("clv_pct", 0) < 0]),
        "average_clv_pct": round(mean([row["clv_pct"] for row in settled]), 6) if settled else None,
        "rows": rows,
        "summary_zh": _summary(rows, settled),
        "disclaimer": DISCLAIMER,
    }


def save_clv_review(
    observations_json: str | Path,
    closing_odds_csv: str | Path,
    output_dir: str | Path = "data/learning_clv",
) -> dict:
    payload = build_clv_tracking(load_observations_json(observations_json), load_closing_odds_csv(closing_odds_csv))
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"clv_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": "saved",
        "path": str(path),
        "review": payload,
        "summary_zh": "已保存 CLV 复盘样本；累计 CLV 会用于判断模型是否长期早于市场。",
        "privacy_zh": "文件只保存在本机 data/learning_clv/，该目录已加入 gitignore。",
        "disclaimer": DISCLAIMER,
    }


def build_clv_history(feedback_dir: str | Path = "data/learning_clv") -> dict:
    directory = Path(feedback_dir)
    files = sorted(directory.glob("*.json")) if directory.exists() else []
    reviews = []
    errors = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["source_path"] = str(path)
            reviews.append(payload)
        except Exception as exc:
            errors.append({"path": str(path), "message_zh": f"读取失败：{str(exc).splitlines()[0]}"})
    rows = [row for review in reviews for row in review.get("rows", []) or []]
    settled = [row for row in rows if isinstance(row.get("clv_pct"), float)]
    positive = [row for row in settled if row.get("clv_pct", 0) > 0]
    negative = [row for row in settled if row.get("clv_pct", 0) < 0]
    avg = round(mean([row["clv_pct"] for row in settled]), 6) if settled else None
    bucket_rows = _clv_bucket_rows(settled)
    return {
        "history_version": "phase2_clv_learning_history_v0",
        "files_loaded": len(reviews),
        "errors": errors,
        "tracked_count": len(rows),
        "settled_count": len(settled),
        "positive_clv_count": len(positive),
        "negative_clv_count": len(negative),
        "average_clv_pct": avg,
        "positive_clv_rate": round(len(positive) / len(settled), 6) if settled else None,
        "bucket_rows": bucket_rows,
        "bucket_stats": {row["bucket"]: row for row in bucket_rows},
        "rows": rows[-30:],
        "summary_zh": _history_summary(len(reviews), settled, positive, avg),
        "next_action_zh": _history_next_action(avg, len(settled)),
        "disclaimer": DISCLAIMER,
    }


def load_observations_json(path: str | Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    portfolio = payload.get("selected_portfolio") or payload.get("recommended_observation_portfolio") or {}
    rows: list[dict] = []
    if isinstance(portfolio, dict):
        for key in ("singles", "parlay_2x1", "parlay_3x1"):
            rows.extend(portfolio.get(key, []) or [])
    if rows:
        return rows
    for key in ("observations", "candidates", "rows"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def load_closing_odds_csv(path: str | Path) -> dict[str, float]:
    closing: dict[str, float] = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            key = str(row.get("key") or "").strip()
            if not key:
                key = observation_key(row)
            odds = _float(row.get("closing_odds") or row.get("close_odds") or row.get("odds"))
            if key and odds and odds > 1:
                closing[key] = odds
    return closing


def _float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _match_label(observation: dict) -> str:
    home = observation.get("home_team", "")
    away = observation.get("away_team", "")
    return f"{home} vs {away}".strip()


def _clv_message(clv_pct: float) -> str:
    if clv_pct > 0:
        return "入场赔率高于收盘赔率，说明赛前观察方向得到后续市场一定程度确认。"
    if clv_pct < 0:
        return "入场赔率低于收盘赔率，说明后续市场没有支持该方向，需复盘信号质量。"
    return "入场赔率与收盘赔率基本一致，市场没有给出明显二次确认。"


def _summary(rows: list[dict], settled: list[dict]) -> str:
    if not rows:
        return "当前没有可跟踪的赛前观察项。"
    if not settled:
        return "当前已记录赛前赔率，但尚未补充收盘赔率；CLV 用于赛后复盘，不用于赛前承诺。"
    positive = len([row for row in settled if row.get("clv_pct", 0) > 0])
    return f"已有 {len(settled)} 项完成 CLV 复盘，其中 {positive} 项跑赢收盘赔率。"


def _history_summary(files_count: int, settled: list[dict], positive: list[dict], avg: float | None) -> str:
    if files_count <= 0:
        return "还没有保存过 CLV 样本；先生成赔率模板，填写收盘赔率后保存 CLV 复盘。"
    if not settled:
        return f"已读取 {files_count} 个 CLV 文件，但尚无可结算收盘赔率。"
    return f"累计 {len(settled)} 项 CLV 复盘，{len(positive)} 项跑赢收盘赔率，平均 CLV {_pct(avg)}。"


def _history_next_action(avg: float | None, settled_count: int) -> str:
    if settled_count < 20:
        return "CLV 样本仍少，只作为价格方向提示，不提高模型权重。"
    if avg is not None and avg > 0:
        return "平均 CLV 为正，可继续观察哪些玩法/赔率段稳定跑赢市场。"
    return "平均 CLV 未转正，应降低对应信号自信并复盘赔率入口质量。"


def _clv_bucket_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        bucket = _clv_odds_bucket(row.get("entry_odds"))
        grouped.setdefault(bucket, {"bucket": bucket, "attempts": 0, "positive": 0, "clv_sum": 0.0})
        grouped[bucket]["attempts"] += 1
        grouped[bucket]["positive"] += 1 if float(row.get("clv_pct") or 0.0) > 0 else 0
        grouped[bucket]["clv_sum"] += float(row.get("clv_pct") or 0.0)
    out = []
    for item in sorted(grouped.values(), key=lambda row: row["bucket"]):
        attempts = int(item["attempts"])
        positive = int(item["positive"])
        avg = item["clv_sum"] / attempts if attempts else None
        out.append({
            "bucket": item["bucket"],
            "attempts": attempts,
            "positive_clv_count": positive,
            "positive_clv_rate": round(positive / attempts, 6) if attempts else None,
            "average_clv_pct": round(avg, 6) if avg is not None else None,
            "message_zh": _clv_bucket_message(attempts, avg),
        })
    return out


def _clv_odds_bucket(value) -> str:
    odds = _float(value)
    if odds is None:
        return "unknown"
    if odds < 1.5:
        return "lt_1_50"
    if odds < 2.0:
        return "1_50_1_99"
    if odds < 3.0:
        return "2_00_2_99"
    if odds < 5.0:
        return "3_00_4_99"
    if odds < 8.0:
        return "5_00_7_99"
    return "gte_8_00"


def _clv_bucket_message(attempts: int, avg: float | None) -> str:
    if attempts < 8:
        return "CLV 样本很少，只作提示，不提高权重。"
    if avg is not None and avg > 0.015:
        return "该赔率段平均 CLV 为正，可继续观察是否稳定。"
    if avg is not None and avg < -0.015:
        return "该赔率段平均 CLV 为负，后续应降低信号自信。"
    return "该赔率段 CLV 接近中性，继续累计样本。"


def _pct(value) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "N/A"

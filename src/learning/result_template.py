from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from src.market.clv import load_observations_json


def save_result_template_from_observations(
    observations_json: str | Path,
    output_dir: str | Path = "data/learning_results",
) -> dict:
    observations = load_observations_json(observations_json)
    matches = _unique_matches(observations)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"result_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "date",
                "match_id",
                "match_no",
                "home_team",
                "away_team",
                "home_goals",
                "away_goals",
                "actual_handicap_outcome_zh",
            ],
        )
        writer.writeheader()
        for row in matches:
            writer.writerow(row)
    return {
        "status": "saved",
        "path": str(path),
        "matches_count": len(matches),
        "summary_zh": "已生成赛果 CSV 模板；赛后只需要填写 home_goals 和 away_goals。",
        "how_to_use_zh": "填写比分后，回到赛后学习页点击保存学习样本，模型会把命中率、赔率段和概率段纳入本地学习。",
        "privacy_zh": "模板只保存在本机 data/learning_results/，该目录已加入 gitignore。",
        "disclaimer": "赛果模板只用于模型校准和纸面复盘，不构成任何真实投注建议。",
    }


def _unique_matches(observations: list[dict]) -> list[dict]:
    seen: set[str] = set()
    rows: list[dict] = []
    for obs in observations or []:
        candidates = []
        if obs.get("legs"):
            candidates.extend(obs.get("legs") or [])
        else:
            candidates.append(obs)
        for item in candidates:
            home = str(item.get("home_team") or "").strip()
            away = str(item.get("away_team") or "").strip()
            match_no = str(item.get("match_no") or "").strip()
            match_id = str(item.get("match_id") or "").strip()
            match_label = str(item.get("match") or "").strip()
            key = match_id or match_no or f"{home}|{away}" or match_label
            if not key or key in seen:
                continue
            seen.add(key)
            rows.append({
                "date": item.get("date") or "",
                "match_id": match_id,
                "match_no": match_no,
                "home_team": home,
                "away_team": away,
                "home_goals": "",
                "away_goals": "",
                "actual_handicap_outcome_zh": "",
            })
    return rows

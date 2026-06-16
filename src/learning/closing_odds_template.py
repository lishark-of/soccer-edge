from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from src.market.clv import load_observations_json, observation_key


def save_closing_odds_template_from_observations(
    observations_json: str | Path,
    output_dir: str | Path = "data/learning_closing_odds",
) -> dict:
    observations = load_observations_json(observations_json)
    rows = _template_rows(observations)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"closing_odds_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "key",
                "match",
                "play_type",
                "direction",
                "entry_odds",
                "closing_odds",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return {
        "status": "saved",
        "path": str(path),
        "rows_count": len(rows),
        "summary_zh": "已生成收盘赔率模板；临近开赛或赛后填写 closing_odds 后可复盘 CLV。",
        "how_to_use_zh": "如果 entry_odds 高于 closing_odds，通常说明赛前观察方向得到了后续市场确认；如果低于 closing_odds，需要复盘信号质量。",
        "privacy_zh": "模板只保存在本机 data/learning_closing_odds/，该目录已加入 gitignore。",
        "disclaimer": "CLV 只用于赔率学习和纸面复盘，不构成任何真实投注建议。",
    }


def _template_rows(observations: list[dict]) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for obs in observations or []:
        if obs.get("legs"):
            continue
        key = observation_key(obs)
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append({
            "key": key,
            "match": obs.get("match") or f"{obs.get('home_team','')} vs {obs.get('away_team','')}".strip(),
            "play_type": obs.get("play_type") or obs.get("type") or "",
            "direction": obs.get("direction") or obs.get("outcome_label") or "",
            "entry_odds": obs.get("odds") or obs.get("official_odds") or "",
            "closing_odds": "",
        })
    return rows

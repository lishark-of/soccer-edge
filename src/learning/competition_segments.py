from __future__ import annotations


SEGMENT_LABELS = {
    "national_team": "国家队/国际赛",
    "friendly": "友谊赛",
    "cup": "杯赛/淘汰赛",
    "club_league": "俱乐部联赛",
    "unknown": "未知赛事类型",
}


def classify_competition_segment(row: dict | None) -> dict:
    row = row or {}
    explicit = str(row.get("competition_segment") or "").strip()
    if explicit in SEGMENT_LABELS:
        key = explicit
        reason = "已使用上游提供的赛事语境标签。"
    else:
        league = _norm(row.get("league") or row.get("competition") or row.get("tournament") or "")
        match = _norm(row.get("match") or "")
        teams = _norm(f"{row.get('home_team','')} {row.get('away_team','')}")
        text = " ".join([league, match, teams])
        if any(word in text for word in ("friendly", "友谊", "热身")):
            key = "friendly"
            reason = "赛事名称包含友谊/热身特征，按高不确定性友谊赛处理。"
        elif any(word in text for word in ("world cup", "euro", "nations league", "afc", "concacaf", "copa", "国家队", "世界杯", "欧洲杯", "美洲杯", "世预赛", "欧国联")):
            key = "national_team"
            reason = "赛事或球队名称呈现国家队/国际赛特征。"
        elif any(word in text for word in ("cup", "杯", "knockout", "playoff", "淘汰", "决赛")):
            key = "cup"
            reason = "赛事名称呈现杯赛/淘汰赛特征。"
        elif league:
            key = "club_league"
            reason = "存在明确联赛名称，默认按俱乐部联赛或常规赛处理。"
        else:
            key = "unknown"
            reason = "缺少赛事名称，暂不能判断语境。"
    return {
        "competition_segment": key,
        "competition_segment_zh": SEGMENT_LABELS.get(key, key),
        "competition_segment_reason_zh": reason,
    }


def _norm(value) -> str:
    return str(value or "").strip().lower()

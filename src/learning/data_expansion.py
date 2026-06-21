from __future__ import annotations

import json
from datetime import date as date_type, datetime
from pathlib import Path
from typing import Any

DEFAULT_CACHE_ROOT = Path("data/cache")
DISCLAIMER = "数据拓展摘要只读取本地缓存和公开结构化字段，用于赛前研究，不构成任何真实投注建议。"


def build_data_expansion_summary(date: str | None = None, *, cache_root: str | Path = DEFAULT_CACHE_ROOT) -> dict:
    """Summarize locally cached real-data coverage without exposing raw keys or user files."""
    target_date = _normalize_date(date)
    root = Path(cache_root)
    api_football = _api_football_summary(root, target_date)
    odds = _the_odds_summary(root, target_date)
    weather = _weather_summary(root, target_date)
    enrichment = _api_football_enrichment_summary(root)
    sources = [api_football, odds, weather, enrichment]
    available_sources = [item for item in sources if item.get("status") in {"available", "partial"}]
    score = min(100, sum(int(item.get("coverage_points", 0) or 0) for item in sources))
    if score >= 70:
        grade = "B"
        status_zh = "数据拓展较完整"
    elif score >= 45:
        grade = "C"
        status_zh = "数据拓展中等"
    else:
        grade = "D"
        status_zh = "数据拓展不足"
    gaps = []
    for item in sources:
        gaps.extend(item.get("gaps", []) or [])
    return {
        "status": "available" if available_sources else "missing",
        "status_zh": status_zh if available_sources else "暂无可用拓展缓存",
        "target_date": target_date,
        "coverage_score": score,
        "coverage_grade": grade,
        "available_source_count": len(available_sources),
        "sources": {
            "api_football": api_football,
            "the_odds_api": odds,
            "weather": weather,
            "api_football_enrichment": enrichment,
        },
        "summary_cards": [
            {"label": "赛程拓展", "value": api_football.get("display_value", "0"), "help": api_football.get("message_zh", "")},
            {"label": "海外赔率", "value": odds.get("display_value", "0"), "help": odds.get("message_zh", "")},
            {"label": "天气缓存", "value": weather.get("display_value", "0"), "help": weather.get("message_zh", "")},
            {"label": "伤停/首发缓存", "value": enrichment.get("display_value", "0"), "help": enrichment.get("message_zh", "")},
        ],
        "gaps": gaps,
        "used_for_zh": [
            "交叉核对赛程和队名",
            "比较海外赔率方向是否支持本地模型",
            "标记天气、伤停、首发是否只是缺失或兜底",
            "给每日快照和赛后学习提供数据来源说明",
        ],
        "safety_zh": "不会输出或保存 API Key；不会自动生成真实投注动作。",
        "disclaimer": DISCLAIMER,
    }


def _normalize_date(value: str | None) -> str:
    if value:
        return str(value)[:10]
    return date_type.today().isoformat()


def _safe_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def _count_rows(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("response", "data", "matches", "events", "fixtures", "bookmakers", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
        if payload:
            return 1
    return 0


def _file_age_zh(path: Path | None) -> str:
    if not path or not path.exists():
        return "未知"
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return "未知"
    return mtime.isoformat(timespec="minutes")


def _api_football_summary(root: Path, target_date: str) -> dict:
    path = root / "api_football" / f"fixtures_{target_date}.json"
    payload = _safe_json(path) if path.exists() else None
    rows = _count_rows(payload)
    if rows:
        return {
            "status": "available",
            "status_zh": "已读取本地 API-Football 赛程缓存",
            "source": "api_football_cache",
            "display_value": f"{rows} 场",
            "fixture_count": rows,
            "cache_path": str(path),
            "updated_at": _file_age_zh(path),
            "coverage_points": 25,
            "message_zh": "可用于赛程、队名和跨源匹配参考。",
            "gaps": [],
        }
    return {
        "status": "missing",
        "status_zh": "未找到当天 API-Football 赛程缓存",
        "source": "api_football_cache",
        "display_value": "0 场",
        "fixture_count": 0,
        "cache_path": str(path),
        "coverage_points": 0,
        "message_zh": "缺少赛程拓展缓存，队名匹配和赛程校验会偏弱。",
        "gaps": ["API-Football 当日赛程缓存缺失"],
    }


def _the_odds_summary(root: Path, target_date: str) -> dict:
    base = root / "the_odds_api"
    date_files = sorted(base.glob(f"*{target_date}.json")) if base.exists() else []
    all_file = base / "odds_soccer_fifa_world_cup_all.json"
    selected = date_files[0] if date_files else (all_file if all_file.exists() else None)
    payload = _safe_json(selected) if selected else None
    rows = _count_rows(payload)
    if rows:
        status = "available" if date_files else "partial"
        return {
            "status": status,
            "status_zh": "已读取当天海外赔率缓存" if date_files else "已读取海外赔率总缓存",
            "source": "the_odds_api_cache",
            "display_value": f"{rows} 条",
            "odds_event_count": rows,
            "cache_path": str(selected),
            "updated_at": _file_age_zh(selected),
            "coverage_points": 25 if date_files else 15,
            "message_zh": "用于核对赔率方向和市场分歧；不是中国竞彩官方赔率。",
            "gaps": [] if date_files else ["缺少当天专属海外赔率缓存，使用总缓存参考"],
        }
    return {
        "status": "missing",
        "status_zh": "未找到海外赔率缓存",
        "source": "the_odds_api_cache",
        "display_value": "0 条",
        "odds_event_count": 0,
        "coverage_points": 0,
        "message_zh": "缺少海外赔率参考，市场交叉验证会偏弱。",
        "gaps": ["The Odds API 缓存缺失"],
    }


def _weather_summary(root: Path, target_date: str) -> dict:
    base = root / "weather"
    files = sorted(base.glob(f"forecast_*_{target_date}.json")) if base.exists() else []
    count = len(files)
    if count:
        return {
            "status": "available",
            "status_zh": "已读取天气缓存",
            "source": "open_meteo_cache",
            "display_value": f"{count} 城市",
            "city_count": count,
            "cache_paths": [str(path) for path in files[:8]],
            "updated_at": _file_age_zh(files[0]),
            "coverage_points": min(20, 5 + count * 3),
            "message_zh": "天气只在城市/球场匹配可靠时才提高信心；兜底城市会降低权重。",
            "gaps": [],
        }
    return {
        "status": "missing",
        "status_zh": "未找到当天天气缓存",
        "source": "open_meteo_cache",
        "display_value": "0 城市",
        "city_count": 0,
        "coverage_points": 0,
        "message_zh": "缺少天气缓存，天气影响保持未知。",
        "gaps": ["天气缓存缺失"],
    }


def _api_football_enrichment_summary(root: Path) -> dict:
    base = root / "api_football_enrichment"
    injuries = sorted(base.glob("injuries_fixture_*.json")) if base.exists() else []
    lineups = sorted(base.glob("fixtures_lineups_fixture_*.json")) if base.exists() else []
    count = len(injuries) + len(lineups)
    if count:
        return {
            "status": "partial",
            "status_zh": "已读取部分伤停/首发缓存",
            "source": "api_football_enrichment_cache",
            "display_value": f"伤停 {len(injuries)} / 首发 {len(lineups)}",
            "injury_cache_count": len(injuries),
            "lineup_cache_count": len(lineups),
            "coverage_points": min(30, count * 4),
            "message_zh": "有缓存不等于已确认无伤停；空结果应显示为已检查但未返回。",
            "gaps": ["伤停/首发覆盖仍需按比赛匹配确认"],
        }
    return {
        "status": "missing",
        "status_zh": "未找到伤停/首发缓存",
        "source": "api_football_enrichment_cache",
        "display_value": "0",
        "injury_cache_count": 0,
        "lineup_cache_count": 0,
        "coverage_points": 0,
        "message_zh": "缺少伤停/首发缓存，组合信心必须扣分。",
        "gaps": ["伤停缓存缺失", "首发缓存缺失"],
    }

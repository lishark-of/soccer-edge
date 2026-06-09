from __future__ import annotations

from src.explain.safety import DISCLAIMER_TEXT


def build_matches_view(matches_payload: dict) -> dict:
    matches = list(matches_payload.get("matches", []) or [])
    provider = matches_payload.get("provider") or matches_payload.get("provider_requested") or "auto"
    provider_used = matches_payload.get("provider_used") or provider
    warnings = _localized_warnings(matches_payload)
    return {
        "title": "竞彩足球比赛",
        "summary_cards": [
            {"label": "请求数据源", "value": provider, "help": "auto / sporttery / mock。"},
            {"label": "实际数据源", "value": provider_used, "help": "如果 Sporttery 不可用，auto 会回退 mock。"},
            {"label": "比赛数量", "value": len(matches), "help": "当前日期返回的比赛数量。"},
            {"label": "Fallback", "value": "是" if matches_payload.get("fallback_used") else "否", "help": "是否发生数据源回退。"},
        ],
        "matches_table": [_match_row(item, provider_used) for item in matches],
        "data_source_notes": warnings,
        "warnings": warnings,
        "explanations": [
            "Sporttery / 中国体育彩票竞彩足球公开数据可能因为网络、证书或接口变更不可用。",
            "如果读取失败，系统会明确显示 provider_used，并可用 mock 示例继续体验完整流程。",
            "本项目不代表官方合作，不提供购彩平台入口。",
        ],
        "disclaimer": DISCLAIMER_TEXT,
    }


def build_sporttery_status_view(matches_payload: dict) -> dict:
    view = build_matches_view(matches_payload)
    provider_used = matches_payload.get("provider_used") or "unknown"
    fallback = bool(matches_payload.get("fallback_used"))
    status = "fallback_mock" if fallback else ("loaded" if provider_used == "sporttery" else "loaded_mock")
    view.update(
        {
            "title": "Sporttery 数据源状态",
            "status": status,
            "status_label_zh": {
                "loaded": "Sporttery 数据已读取",
                "fallback_mock": "Sporttery 未读取成功，已回退 mock 示例",
                "loaded_mock": "当前使用 mock 示例数据",
            }.get(status, "状态未知"),
        }
    )
    return view


def _match_row(item: dict, provider_used: str) -> dict:
    had = item.get("had_odds") or {}
    hhad = item.get("hhad_odds") or {}
    return {
        "match_no": item.get("match_no") or item.get("match_num") or "",
        "league": item.get("league", ""),
        "kickoff_at": item.get("kickoff_at") or item.get("kickoff_time") or "",
        "home_team": item.get("home_team", ""),
        "away_team": item.get("away_team", ""),
        "had_win": _odds(had.get("win")),
        "had_draw": _odds(had.get("draw")),
        "had_lose": _odds(had.get("lose")),
        "handicap": hhad.get("handicap", ""),
        "hhad_win": _odds(hhad.get("win")),
        "hhad_draw": _odds(hhad.get("draw")),
        "hhad_lose": _odds(hhad.get("lose")),
        "source": item.get("source") or provider_used,
        "status": item.get("status", ""),
    }


def _localized_warnings(payload: dict) -> list[str]:
    warnings = list(payload.get("provider_warnings", []) or []) + list(payload.get("warnings", []) or [])
    localized: list[str] = []
    for item in warnings:
        text = str(item)
        if "fallback" in text.lower() or "sporttery" in text.lower():
            localized.append("当前未能读取 Sporttery 数据，已回退到本地 mock 示例。常见原因包括网络、证书、接口变更。")
        else:
            localized.append(text)
    return list(dict.fromkeys(localized))


def _odds(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{number:.2f}"

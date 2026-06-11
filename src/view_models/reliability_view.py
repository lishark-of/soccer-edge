from __future__ import annotations


def build_reliability_view(preview: dict) -> dict:
    reliability = preview.get("reliability_summary", {}) or {}
    coverage = preview.get("source_coverage", {}) or {}
    return {
        "title": "数据可靠性",
        "selected_date": preview.get("selected_date") or preview.get("date"),
        "matches_count": preview.get("matches_count", 0),
        "summary_cards": [
            {"label": "情报完整度", "value": f"{reliability.get('overall_score', 0)}/100", "help": reliability.get("summary_zh", "")},
            {"label": "完整度评级", "value": reliability.get("overall_label_zh", "unknown"), "help": "由赔率、赛程、球队、伤停、首发、天气等组成。"},
            {"label": "主要缺口", "value": "、".join(reliability.get("main_gaps_zh", [])[:4]) or "暂无", "help": "缺失项不会被模型编造。"},
            {"label": "部分覆盖", "value": "、".join(reliability.get("partial_gaps_zh", [])[:4]) or "暂无", "help": "已尝试读取，但源头暂未给出完整信息。"},
            {"label": "数据源数量", "value": len(coverage.get("source_cards", []) or []), "help": "Sporttery / API-Football / The Odds API / Open-Meteo。"},
        ],
        "source_cards": _source_rows(coverage),
        "match_coverage_table": _match_rows(coverage),
        "api_football_status": coverage.get("api_football_status", {}),
        "the_odds_api_status": coverage.get("the_odds_api_status", {}),
        "decision_guide_zh": reliability.get("decision_guide_zh", "先看 Sporttery 主数据，再看第三方匹配和缺失情报。"),
        "warnings": list(preview.get("warnings", []) or []),
        "disclaimer": preview.get("disclaimer", "仅用于观察信号、纸面模拟和风险诊断。"),
    }


def _source_rows(coverage: dict) -> list[dict]:
    return [
        {
            "source": row.get("source"),
            "role": row.get("label_zh"),
            "status": _status_zh(row.get("status")),
            "coverage": row.get("coverage"),
            "score": row.get("score"),
            "message_zh": row.get("message_zh"),
        }
        for row in coverage.get("source_cards", []) or []
    ]


def _match_rows(coverage: dict) -> list[dict]:
    rows = []
    for row in coverage.get("match_coverage", []) or []:
        identity = row.get("identity") or {}
        rows.append(
            {
                "match": row.get("match"),
                "api_football": (row.get("api_football") or {}).get("label_zh"),
                "the_odds_api": (row.get("the_odds_api") or {}).get("label_zh"),
                "injuries": (row.get("injuries") or {}).get("label_zh"),
                "lineup": (row.get("lineup") or {}).get("label_zh"),
                "weather": (row.get("weather") or {}).get("label_zh"),
                "news": (row.get("news") or {}).get("label_zh"),
                "match_confidence": _pct(identity.get("match_confidence")),
                "message_zh": row.get("message_zh"),
            }
        )
    return rows


def _status_zh(value) -> str:
    return {
        "available": "可用",
        "ok": "可用",
        "matched": "已匹配",
        "not_connected": "未接入",
        "not_configured": "未配置",
        "covered_empty": "已检查无公开条目",
        "not_available": "未公布/未覆盖",
        "not_found": "未发现",
        "timeout": "暂未返回",
        "empty": "空结果",
        "error": "异常",
    }.get(str(value), str(value or "未知"))


def _pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"

from __future__ import annotations

DISCLAIMER = "本工具只做本地概率分析、纸面模拟和回测诊断。不提供投注、下单、支付、代购或任何自动化购彩能力。模拟走盘不代表未来表现。"


def build_paper_operation_report(simulation: dict) -> dict:
    return {
        **simulation,
        "walk_log_table": build_walk_log_table(simulation),
        "equity_curve": build_daily_equity_curve(simulation),
        "disclaimer": simulation.get("disclaimer") or DISCLAIMER,
    }


def build_walk_log_table(simulation: dict) -> list[dict]:
    rows = []
    for item in simulation.get("walk_log", []) or []:
        rows.append(
            {
                "date": item.get("date"),
                "type": _kind_zh(item.get("observation_type")),
                "match": item.get("match") or _legs_label(item),
                "direction": item.get("direction") or item.get("pass_type", ""),
                "paper_stake": item.get("paper_stake", 0.0),
                "odds": item.get("odds") or item.get("combined_odds"),
                "hit": item.get("result_label_zh"),
                "profit": item.get("profit", 0.0),
                "bankroll_after": item.get("bankroll_after"),
            }
        )
    return rows


def build_daily_equity_curve(simulation: dict) -> list[dict]:
    return [
        {
            "date": day.get("date"),
            "bankroll": day.get("ending_bankroll"),
            "daily_profit": day.get("daily_profit"),
            "observations": day.get("observation_count"),
        }
        for day in simulation.get("daily_ledger", []) or []
    ]


def _kind_zh(kind: str | None) -> str:
    return {"single": "单关观察", "parlay_2x1": "2串1 组合观察", "parlay_3x1": "3串1 组合观察"}.get(str(kind), "观察项")


def _legs_label(item: dict) -> str:
    labels = []
    for leg in item.get("legs", []) or []:
        labels.append(f"{leg.get('home_team', '')} vs {leg.get('away_team', '')} {leg.get('outcome_label', '')}".strip())
    return "；".join(labels)

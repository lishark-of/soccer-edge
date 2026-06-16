from __future__ import annotations

from pathlib import Path

from src.learning.history import build_learning_history
from src.learning.odds_education import build_odds_learning_view
from src.learning.result_feedback import build_feedback_report, load_feedback
from src.market.clv import build_clv_history

DEFAULT_FEEDBACK = Path("data/fixtures/result_feedback_20260611.json")
LEARNING_OBSERVATIONS_DIR = Path("data/learning_observations")
LEARNING_RESULTS_DIR = Path("data/learning_results")
LEARNING_CLOSING_ODDS_DIR = Path("data/learning_closing_odds")


def build_home_learning_panel(feedback_path: str | None = None) -> dict:
    history = build_learning_history()
    clv_history = build_clv_history()
    odds_learning = build_odds_learning_view(history)
    path = Path(feedback_path) if feedback_path else DEFAULT_FEEDBACK
    if not path.exists():
        return {
            "status": "missing",
            "summary_cards": [{"label": "昨日复盘", "value": "暂无", "help": "尚未提供赛果反馈文件。"}],
            "model_health_cards": _model_health_cards(history, clv_history),
            "model_health_zh": _model_health_message(history, clv_history),
            "combo_discipline_learning": history.get("combo_discipline_learning", {}),
            "history_cards": _history_cards(history),
            "clv_cards": _clv_cards(clv_history),
            "clv_history": clv_history,
            "latest_daily_summary_zh": history.get("latest_daily_summary_zh", ""),
            "window_summaries_zh": history.get("window_summaries_zh", []),
            "daily_digest": history.get("daily_digest", {}),
            "window_digests": history.get("window_digests", []),
            "daily_report": history.get("daily_report", {}),
            "window_reports": history.get("window_reports", []),
            "daily_metrics": history.get("daily_metrics", []),
            "window_metrics": history.get("window_metrics", []),
            "learning_todo": _learning_todo(history, clv_history),
            "learning_brief": _learning_brief(history),
            "model_actions": _model_actions(history),
            "odds_learning": odds_learning,
            "rows": [],
            "lessons": ["没有赛果反馈时，模型不会假装已经学习。"],
        }
    report = build_feedback_report(load_feedback(path))
    return {
        "status": "ok",
        "report": report,
        "summary_cards": [
            {"label": "昨日观察", "value": report.get("observation_count", 0), "help": "进入赛后反馈的观察项数量。"},
            {"label": "命中率", "value": _pct(report.get("hit_rate")), "help": "只统计已结算观察，不代表未来表现。"},
            {"label": "Brier", "value": _num(report.get("brier_score")), "help": "越低越好，用来评估概率是否校准。"},
            {"label": "Log Loss", "value": _num(report.get("log_loss")), "help": "越低越好，对过度自信惩罚更重。"},
            {"label": "冷门命中", "value": _pct(report.get("longshot_hit_rate")), "help": "高赔率冷门单独统计，防止 EV 误导。"},
            {"label": "模型动作", "value": "冷门降权", "help": report.get("next_model_action_zh", "")},
        ],
        "model_health_cards": _model_health_cards(history, clv_history),
        "model_health_zh": _model_health_message(history, clv_history),
        "combo_discipline_learning": history.get("combo_discipline_learning", {}),
        "history_cards": _history_cards(history),
        "clv_cards": _clv_cards(clv_history),
        "clv_history": clv_history,
        "latest_daily_summary_zh": history.get("latest_daily_summary_zh", ""),
        "window_summaries_zh": history.get("window_summaries_zh", []),
        "daily_digest": history.get("daily_digest", {}),
        "window_digests": history.get("window_digests", []),
        "daily_report": history.get("daily_report", {}),
        "window_reports": history.get("window_reports", []),
        "daily_metrics": history.get("daily_metrics", []),
        "window_metrics": history.get("window_metrics", []),
        "learning_todo": _learning_todo(history, clv_history),
        "learning_brief": _learning_brief(history),
        "model_actions": _model_actions(history),
        "odds_learning": odds_learning,
        "rows": report.get("rows", []),
        "lessons": [report.get("main_lesson_zh", "继续累计样本。"), report.get("next_model_action_zh", "")],
    }


def _pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _history_cards(history: dict) -> list[dict]:
    quality = history.get("probability_quality") or {}
    return [
        {"label": "累计样本", "value": history.get("settled_count", 0), "help": "只统计已结算的赛前观察，样本少时不会过度拟合。"},
        {"label": "累计命中率", "value": _pct(history.get("hit_rate")), "help": "用于校准赔率段和信号类型，不代表未来表现。"},
        {"label": "累计 Brier", "value": _num(history.get("brier_score")), "help": quality.get("message_zh", "越低越好，评估概率校准。")},
        {"label": "累计 Log Loss", "value": _num(history.get("log_loss")), "help": "越低越好，对过度自信惩罚更重。"},
        {"label": "学习文件", "value": history.get("files_loaded", 0), "help": "fixture + data/learning_feedback 中的本地反馈 JSON。"},
        {"label": "学习模式", "value": "小样本校准", "help": "先用保守贝叶斯更新，等样本变多再提高历史权重。"},
    ]


def _clv_cards(history: dict) -> list[dict]:
    return [
        {"label": "CLV 文件", "value": history.get("files_loaded", 0), "help": "本地 data/learning_clv 中已保存的赔率复盘文件。"},
        {"label": "CLV 复盘项", "value": history.get("settled_count", 0), "help": "已填写收盘赔率并完成复盘的观察项。"},
        {"label": "跑赢收盘", "value": history.get("positive_clv_count", 0), "help": "赛前赔率高于收盘赔率的观察项。"},
        {"label": "平均 CLV", "value": _pct(history.get("average_clv_pct")), "help": history.get("summary_zh", "用于判断是否早于市场。")},
    ]


def _model_health_cards(history: dict, clv_history: dict) -> list[dict]:
    settled = int(history.get("settled_count") or 0)
    clv_settled = int(clv_history.get("settled_count") or 0)
    quality = history.get("probability_quality") or {}
    return [
        {"label": "学习样本", "value": settled, "help": "已结算观察样本。低于 30 时仍按小样本处理。"},
        {"label": "概率质量", "value": quality.get("grade_zh") or "样本不足", "help": quality.get("message_zh", "用 Brier / Log Loss 检查概率是否过度自信。")},
        {"label": "CLV 方向", "value": _clv_direction(clv_history), "help": clv_history.get("summary_zh", "CLV 用于判断是否早于市场。")},
        {"label": "模型姿态", "value": _model_posture(history, clv_history), "help": "决定 Top 排序是更保守，还是允许轻微信号加分。"},
    ]


def _model_health_message(history: dict, clv_history: dict) -> str:
    settled = int(history.get("settled_count") or 0)
    clv_settled = int(clv_history.get("settled_count") or 0)
    if settled < 30 and clv_settled < 20:
        return "模型健康：仍处于小样本阶段。Top 信号会更靠近市场概率和保守先验，不会因为短期 EV 或冷门赔率而大幅加权。"
    avg_clv = _float_or_none(clv_history.get("average_clv_pct"))
    if avg_clv is not None and avg_clv > 0:
        return "模型健康：已有一定样本且 CLV 偏正，可以继续观察哪些赔率段稳定跑赢市场，但仍需控制串联风险。"
    if avg_clv is not None and avg_clv < 0:
        return "模型健康：CLV 偏弱，说明赛前价格判断还没有跑赢市场，应降低对应信号自信。"
    return "模型健康：样本开始累计，但还不足以显著改变模型权重。"


def _learning_todo(history: dict, clv_history: dict) -> dict:
    settled = int(history.get("settled_count") or 0)
    clv_settled = int(clv_history.get("settled_count") or 0)
    pack_state = _learning_pack_state()
    pack_ready = bool(pack_state.get("observations_ready") and pack_state.get("results_ready") and pack_state.get("closing_ready"))
    current_score = 88 if settled >= 30 and clv_settled >= 20 else 72 if settled >= 6 else 65 if pack_ready else 58
    if int(history.get("files_loaded") or 0) > 1 or settled > 0:
        current_score = max(current_score, 72)
    if clv_settled > 0:
        current_score = max(current_score, 78)
    target_score = 92 if settled >= 30 and clv_settled >= 20 else 78 if settled >= 6 else 65
    sample_gap = max(0, 30 - settled)
    clv_gap = max(0, 20 - clv_settled)
    items = [
        {
            "label": "赛前固定观察快照",
            "status": "done" if pack_state.get("observations_ready") else "todo",
            "impact_zh": "把 T+1 的 Top 单关、候选组合和被拒原因锁住，避免赛后按结果倒推。",
        },
        {
            "label": "赛后填写真实比分",
            "status": "done" if settled > 0 else "todo",
            "impact_zh": "用于更新命中率、Brier、Log Loss 和赔率段校准。",
        },
        {
            "label": "收盘赔率模板已生成",
            "status": "done" if pack_state.get("closing_ready") else "todo",
            "impact_zh": "模板准备好不等于已学习；赛后仍需填写 closing_odds。",
        },
        {
            "label": "赛后填写收盘赔率并保存 CLV",
            "status": "done" if clv_settled > 0 else "todo",
            "impact_zh": "用于判断赛前价格是否跑赢市场，帮助过滤表面高 EV。",
        },
        {
            "label": "累计 30 条已结算样本",
            "status": "done" if sample_gap == 0 else "todo",
            "impact_zh": f"还差 {sample_gap} 条；达到后才能更有证据地调整冷门和串联权重。",
        },
    ]
    if clv_gap > 0:
        items.append(
            {
                "label": "累计 20 条 CLV 样本",
                "status": "todo",
                "impact_zh": f"还差 {clv_gap} 条；CLV 能帮助判断模型是否早于市场，而不是只看赛果。",
            }
        )
    next_action = (
        "学习包已准备好；赛后只需要填写比分和收盘赔率，再保存学习样本。"
        if pack_ready and settled < 30
        else "先在赛前保存观察快照，赛后补比分和收盘赔率；这是提升长期分的最短路径。"
        if settled < 30
        else "继续补 CLV 和不同赔率段样本，观察模型是否稳定跑赢收盘价格。"
    )
    return {
        "title_zh": "本轮最低分怎么补",
        "current_score": current_score,
        "target_score_after_next_loop": target_score,
        "settled_count": settled,
        "clv_count": clv_settled,
        "pack_ready": pack_ready,
        "pack_state": pack_state,
        "sample_gap_to_stable": sample_gap,
        "next_action_zh": next_action,
        "items": items,
        "why_it_matters_zh": "赛后学习不是为了解释昨天，而是让下一次 Top 排序、冷门降权和串联门控更有证据。",
        "score_persistence_zh": "这些分数来自本机 data/learning_feedback 与 data/learning_clv；重新打开 App 后仍会读取，不只是页面临时加分。",
    }


def _learning_pack_state() -> dict:
    observation_files = sorted(LEARNING_OBSERVATIONS_DIR.glob("observations_*.json")) if LEARNING_OBSERVATIONS_DIR.exists() else []
    result_files = sorted(LEARNING_RESULTS_DIR.glob("result_template_*.csv")) if LEARNING_RESULTS_DIR.exists() else []
    closing_files = sorted(LEARNING_CLOSING_ODDS_DIR.glob("closing_odds_template_*.csv")) if LEARNING_CLOSING_ODDS_DIR.exists() else []
    return {
        "observations_ready": bool(observation_files),
        "results_ready": bool(result_files),
        "closing_ready": bool(closing_files),
        "latest_observations_path": str(observation_files[-1]) if observation_files else "",
        "latest_results_path": str(result_files[-1]) if result_files else "",
        "latest_closing_odds_path": str(closing_files[-1]) if closing_files else "",
    }


def _clv_direction(history: dict) -> str:
    settled = int(history.get("settled_count") or 0)
    avg = _float_or_none(history.get("average_clv_pct"))
    if settled <= 0:
        return "待学习"
    if avg is not None and avg > 0.005:
        return "偏正"
    if avg is not None and avg < -0.005:
        return "偏负"
    return "中性"


def _model_posture(history: dict, clv_history: dict) -> str:
    settled = int(history.get("settled_count") or 0)
    clv_settled = int(clv_history.get("settled_count") or 0)
    avg_clv = _float_or_none(clv_history.get("average_clv_pct"))
    if settled < 30 or clv_settled < 20:
        return "保守学习"
    if avg_clv is not None and avg_clv > 0:
        return "轻微加权"
    if avg_clv is not None and avg_clv < 0:
        return "降低自信"
    return "继续观察"


def _learning_brief(history: dict) -> list[str]:
    settled = int(history.get("settled_count") or 0)
    if settled <= 0:
        return [
            "当前没有可结算样本，模型不会假装已经学会。",
            "下一步：每天赛后导入观察快照和真实赛果，先建立赔率段命中率。",
        ]
    lines = [
        f"当前累计 {settled} 条已结算观察，仍属于小样本；排序会更靠近市场概率和保守先验。",
        "赔率越高，模型越容易被表面 EV 吸引；冷门会被单独降权，不进入串联核心。",
    ]
    if history.get("hit_rate") is not None:
        lines.append(f"当前累计命中率 {_pct(history.get('hit_rate'))}，只用于调整模型自信，不作为未来保证。")
    quality = history.get("probability_quality") or {}
    if quality.get("message_zh"):
        lines.append(quality["message_zh"])
    return lines


def _model_actions(history: dict) -> list[str]:
    actions = [
        "赔率段学习：按 1.50、2.00、3.00、5.00、8.00+ 分桶累计命中率。",
        "冷门纪律：赔率 >= 6 默认视为冷门观察，除非长期样本和情报完整度都支持，否则不做串联腿。",
        "串联纪律：2串1/3串1 不看赔率诱惑，优先看每一腿校准概率、相关性、情报缺口和历史回撤。",
        "赛后闭环：每次赛果反馈都会更新本地 bucket prior，下次 Top 排序自动读取累计样本。",
        "概率质量：用 Brier Score 和 Log Loss 检查模型是否过度自信，而不是只看命中/未命中。",
    ]
    if history.get("errors"):
        actions.append("有反馈文件读取失败，失败样本不会进入学习，避免污染模型。")
    return actions


def _num(value) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "N/A"


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

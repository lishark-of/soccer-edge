from __future__ import annotations

from src.view_models.intelligence_view import _obs


def build_signal_explanation_view(preview: dict) -> dict:
    observations = [_obs(row) for row in preview.get("observations", []) or []]
    strong = [row for row in observations if row.get("recommended_action_zh", "").startswith("可观察")]
    weak = [row for row in observations if row.get("recommended_action_zh", "").startswith("弱观察")]
    waiting = [row for row in observations if row.get("recommended_action_zh", "").startswith("等待")]
    rejected = [row for row in observations if row.get("recommended_action_zh", "").startswith("放弃")]
    return {
        "title": "信号解释",
        "selected_date": preview.get("selected_date") or preview.get("date"),
        "summary_cards": [
            {"label": "可观察", "value": len(strong), "help": "赔率和模型存在一定差异，但仍需看缺失情报。"},
            {"label": "弱观察", "value": len(weak), "help": "有倾向，但可信度不足。"},
            {"label": "等待赔率/情报", "value": len(waiting), "help": "当前暂不能判断价值。"},
            {"label": "放弃", "value": len(rejected), "help": "当前无观察价值。"},
        ],
        "strong_observations": strong[:8],
        "weak_observations": weak[:8],
        "waiting_observations": waiting[:8],
        "rejected_observations": rejected[:8],
        "method_notes": [
            "观察可信度由市场赔率、模型概率、情报完整度、回测支撑和数据源可靠性组合而来。",
            "比分和总进球如果没有官方赔率，只展示模型倾向，暂不计算 EV。",
            "缺少伤停、首发、天气、新闻时不会编造，只会降低信心。",
        ],
        "warnings": list(preview.get("warnings", []) or []),
        "disclaimer": preview.get("disclaimer", "仅用于观察信号、纸面模拟和风险诊断。"),
    }

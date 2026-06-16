from __future__ import annotations

from src.learning.history import build_learning_history
from src.learning.odds_bucket_calibrator import bayesian_bucket_rate


def build_odds_learning_view(history: dict | None = None) -> dict:
    learned = history or build_learning_history()
    return {
        "view_version": "phase2t_odds_learning_v0",
        "summary_cards": _summary_cards(learned),
        "plain_language_rules": _plain_language_rules(),
        "lightweight_learning_path": _lightweight_learning_path(),
        "parlay_examples": _parlay_examples(),
        "bucket_explanations": _bucket_explanations(learned),
        "model_upgrade_actions": _model_upgrade_actions(learned),
        "research_notes": [
            "足球比分模型常用 Poisson / Dixon-Coles 来处理进球数和低比分相关性。",
            "赔率市场本身是强基准；模型必须先和市场隐含概率比较，再谈 Edge。",
            "Brier Score、Log Loss、校准曲线和 CLV 比单场命中更适合评估概率模型。",
        ],
        "disclaimer": "本页只解释赔率和概率学习逻辑，用于纸面研究，不构成投注建议。",
    }


def _summary_cards(history: dict) -> list[dict]:
    settled = int(history.get("settled_count") or 0)
    return [
        {
            "label": "当前学习阶段",
            "value": "小样本",
            "help": "样本少时只做保守校准，不会把一次命中/失手当作真规律。",
        },
        {
            "label": "可学习样本",
            "value": settled,
            "help": "来自赛后反馈 JSON 的已结算观察项。",
        },
        {
            "label": "赔率学习重点",
            "value": "盈亏平衡概率",
            "help": "赔率 10.0 至少要超过 10% 的真实概率才有价值，还要扣情报和冷门风险。",
        },
        {
            "label": "串联学习重点",
            "value": "概率相乘",
            "help": "2串1/3串1 命中概率会快速下降，不能只看组合赔率高。",
        },
    ]


def _plain_language_rules() -> list[str]:
    return [
        "赔率先转成盈亏平衡概率：2.00 约等于 50%，5.00 约等于 20%，10.00 约等于 10%。",
        "只有当校准后模型概率明显高于盈亏平衡概率，才可能有观察价值。",
        "高赔率冷门即使 EV 为正，也需要更大的安全边际；否则容易被单次模型偏差误导。",
        "2串1 不是两个优势相加，而是两腿概率相乘，再扣相关性、情报缺口和波动风险。",
        "如果临近开赛的收盘赔率更低，说明市场后来更支持该方向；如果更高，需要复盘信号质量。",
    ]


def _lightweight_learning_path() -> list[dict]:
    return [
        {
            "step": "1. 记录每条观察",
            "what_zh": "保存赔率、市场概率、模型概率、校准概率、信号类型和赛果。",
            "why_zh": "没有这一步，模型只能凭当天数字判断，无法知道自己哪里经常高估。",
        },
        {
            "step": "2. 按赔率段学习",
            "what_zh": "把 1.50-2.00、2.00-3.00、5.00-8.00、8.00+ 分开统计。",
            "why_zh": "冷门和低赔率热门不是同一种风险，不能混成一个命中率。",
        },
        {
            "step": "3. 按概率段校准",
            "what_zh": "检查 0-10%、10-20%、20-30% 等概率段是否长期高估或低估。",
            "why_zh": "这比单场对错更接近真正的概率模型训练。",
        },
        {
            "step": "4. 约束串联",
            "what_zh": "串联必须同时通过校准概率、情报可信度、相关性和组合命中率。",
            "why_zh": "组合赔率高不等于组合质量高，机器学习要优先降低误判和波动。",
        },
    ]


def _parlay_examples() -> list[dict]:
    examples = [
        ("两腿各 55%", 0.55, 0.55, 0.92),
        ("一腿 55% + 一腿 40%", 0.55, 0.40, 0.90),
        ("三腿各 55%", 0.55, 0.55 * 0.55, 0.86),
    ]
    rows = []
    for label, p1, p2, discount in examples:
        raw = p1 * p2
        adjusted = raw * discount
        rows.append(
            {
                "case_zh": label,
                "raw_hit_prob": round(raw, 6),
                "after_discount_prob": round(adjusted, 6),
                "message_zh": _parlay_message(label, raw, adjusted),
            }
        )
    return rows


def _parlay_message(label: str, raw: float, adjusted: float) -> str:
    return f"{label} 原始同时命中约 {raw:.1%}，扣相关性/情报风险后约 {adjusted:.1%}。"


def _bucket_explanations(history: dict) -> list[dict]:
    rows = history.get("bucket_rows") or []
    if not rows:
        rows = [
            bayesian_bucket_rate("1.50-2.00"),
            bayesian_bucket_rate("2.00-3.00"),
            bayesian_bucket_rate("5.00-8.00"),
            bayesian_bucket_rate("8.00+"),
        ]
    out = []
    for row in rows:
        bucket = row.get("bucket")
        attempts = int(row.get("attempts") or 0)
        hits = int(row.get("hits") or 0)
        rate = row.get("bayesian_hit_rate") or row.get("posterior_hit_rate")
        out.append(
            {
                "bucket": bucket,
                "bucket_label_zh": row.get("bucket_label_zh", bucket),
                "attempts": attempts,
                "hits": hits,
                "bayesian_hit_rate": rate,
                "use_zh": _bucket_use(bucket, attempts, hits),
            }
        )
    return out


def _bucket_use(bucket: str | None, attempts: int, hits: int) -> str:
    if attempts <= 0:
        return "暂无本地样本，使用保守先验。"
    if bucket in {"8.00+", "5.00-8.00"} and hits == 0:
        return "高赔率段暂未兑现，下一次排序会继续冷门降权。"
    if hits == 0:
        return "该赔率段未命中，先降低模型自信。"
    return "已有命中样本，但仍需继续累计后再提高权重。"


def _model_upgrade_actions(history: dict) -> list[str]:
    settled = int(history.get("settled_count") or 0)
    actions = [
        "把每条观察都记录为：官方赔率、市场概率、融合概率、校准概率、信号类型、赛果。",
        "用赔率段贝叶斯命中率修正 raw model probability，减少高 EV 偶然噪声。",
        "串联先过可信度门控，再过每腿质量、相关性折扣和组合命中概率门槛。",
        "用 CLV 复盘市场是否在临场前支持该方向，避免只看赛果对错。",
    ]
    if settled < 100:
        actions.append("当前样本远少于 100 条，模型应继续保守，优先积累真实赛果反馈。")
    return actions

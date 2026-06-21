from __future__ import annotations

from functools import lru_cache

from src.learning.ai_hypothesis_review import build_ai_hypothesis_review_history
from src.learning.history import build_learning_history
from src.learning.market_benchmark import build_market_benchmark_from_learning
from src.market.clv import build_clv_history
from src.audit.source_reliability import build_source_reliability


def build_professional_model_score(preview: dict, optimizer_result: dict, credibility: dict) -> dict:
    """Score the stack against professional forecasting practice without overstating certainty."""
    preview = preview or {}
    optimizer_result = optimizer_result or {}
    credibility = credibility or {}
    learning_history = _learning_history(preview, optimizer_result)
    clv_history = _clv_history(preview, optimizer_result)
    ai_review_history = _ai_review_history(preview, optimizer_result)
    components = [
        _market_component(preview),
        _odds_conversion_component(preview),
        _ensemble_component(preview),
        _coverage_component(preview),
        _calibration_component(preview, optimizer_result, learning_history),
        _clv_component(optimizer_result, clv_history),
        _longshot_bias_component(optimizer_result),
        _play_bias_component(optimizer_result),
        _portfolio_component(optimizer_result),
        _learning_component(preview, optimizer_result, learning_history, clv_history, ai_review_history),
    ]
    score = round(sum(item["score"] * item["weight"] for item in components))
    ceiling = _score_ceiling(preview, components)
    score = min(score, ceiling)
    grade = "A" if score >= 85 else "B" if score >= 72 else "C" if score >= 55 else "D"
    return {
        "score": score,
        "ceiling_score": ceiling,
        "grade": grade,
        "label_zh": _label(score),
        "summary_zh": _summary(score, ceiling, components),
        "components": components,
        "score_gap_radar": _score_gap_radar(components),
        "missing_to_95": _missing_to_95(components, ceiling),
        "learning_evidence": _learning_evidence(learning_history, clv_history, ai_review_history),
        "roadmap_to_95": _roadmap_to_95(score, ceiling, components, learning_history, clv_history),
        "evidence_requirements": _evidence_requirements(score, ceiling, components, learning_history, clv_history),
        "score_trend": _score_trend(score, ceiling, components, learning_history),
        "ai_research_quality": _ai_research_quality(preview, optimizer_result, ai_review_history),
        "industry_benchmark_zh": _industry_benchmark(components),
        "research_sources_zh": [
            "市场校准模型研究显示，预赛前市场赔率校准通常是足球预测精度的核心驱动。",
            "2026 年足球预测研究继续强调：把球队强度校准到赛前市场赔率，往往比单独堆复杂模型更能提升准确性。",
            "体育概率模型选择应优先看校准质量，而不是只看方向准确率。",
            "xG 能描述进攻质量，但短样本和模型偏差会影响稳定性，必须和市场/赛果校准结合。",
            "串联组合需要所有腿同时命中，且组合价格常放大水位和波动，因此必须检查联合概率与相关性。",
            "近期 Parlay / joint-contract 研究强调：串联不是简单相乘，必须显式建模腿之间的依赖结构和相关性折扣。",
            "Kelly/资金曲线框架可用作概率模型评估信号，但在本项目中只用于纸面复盘和模型可信度，不做实盘仓位建议。",
            "LLM/DS 更适合把置信度、反对因素和赛后学习点讲清楚；概率主体仍应由赔率市场、Poisson/xG/Elo、校准和回测驱动。",
            "世界杯/杯赛短周期应采用市场校准、概率区间、CLV 快速闭环和玩法分散，而不是盲目追求高赔率。",
        ],
        "principles_zh": [
            "市场赔率是强基准，模型必须先证明自己能改善市场概率。",
            "如果模型与市场强烈分歧，默认先降权而不是直接相信模型；除非有伤停、首发、天气、战意或 CLV 证据支持。",
            "短赛会阶段样本少，优先采用市场校准概率、稳健概率区间和玩法分散，而不是追逐单次高 EV。",
            "优先看校准、CLV 和长期复盘，不只看单日命中。",
            "长赔冷门需要 favourite-longshot bias 控制；高赔率不自动等于高价值。",
            "xG/Poisson/Elo/Dixon-Coles 要与市场方向一致，分歧大时降权。",
            "组合需要玩法分散、低相关性和足够联合概率，不能只追高赔率。",
            "2串1/3串1 的每日输出应优先作为可复盘样本：如果原始组合同玩法同方向扎堆，就用分散纸面组合替代并记录赛后结果。",
            "每日 2串1/3串1 可以输出纸面候选，但未通过门控时只进入赛后学习，不包装成强观察。",
            "如果候选长期集中在同一玩法，例如让球胜平负，必须降权并用赛后样本证明它真的有效。",
            "短周期世界杯模式下，模型要每天锁定 T+1 候选、记录赔率和解释、赛后回填结果，快速检查是否跑赢市场基准。",
        ],
    }


def _market_component(preview: dict) -> dict:
    reliability = build_source_reliability(preview)
    provider = str(reliability.get("provider_used") or preview.get("provider_used") or preview.get("provider") or "unknown")
    score = _safe_int(reliability.get("reliability_score"))
    if provider in {"mock", "fallback", "fixture"}:
        score = min(score, 45)
    elif reliability.get("health") == "stable":
        score = max(score, 90)
    elif reliability.get("health") == "degraded":
        score = min(max(score, 62), 82)
    elif reliability.get("health") in {"empty", "unknown"}:
        score = min(score, 58)
    detail = reliability.get("component_detail_zh") or "数据源状态不够清晰，市场基准可信度有限。"
    return _component(
        "market_baseline",
        "市场赔率基准",
        score,
        0.14,
        detail,
        "先保证 Sporttery 可售比赛稳定读取，再用海外赔率和收盘赔率验证市场基准。",
    )


def _odds_conversion_component(preview: dict) -> dict:
    reports = []
    for ctx in preview.get("contexts") or []:
        report = ctx.get("market_probability_report") or {}
        for key in ("had", "hhad"):
            item = report.get(key)
            if isinstance(item, dict) and item.get("score") is not None:
                reports.append(item)
    if not reports:
        return _component(
            "odds_conversion_quality",
            "赔率转概率",
            52,
            0.08,
            "当前没有赔率转换报告，可能只使用简单 no-vig 概率。",
            "用 Power no-vig 和 Shin-style 交叉检查比例去水，并记录 overround、方法差异与冷门偏差。",
        )
    avg_score = sum(float(item.get("score") or 0) for item in reports) / len(reports)
    max_shift = max(float(item.get("max_method_shift") or 0.0) for item in reports)
    overrounds = [item.get("overround") for item in reports if item.get("overround") is not None]
    avg_overround = sum(float(x) for x in overrounds) / len(overrounds) if overrounds else None
    bias_reports = [item.get("favorite_longshot_bias") or {} for item in reports]
    unstable_bias = len([item for item in bias_reports if item.get("status") == "unstable"])
    longshot_watch = len([item for item in bias_reports if item.get("status") == "longshot_watch"])
    detail = (
        f"已用共识 no-vig、proportional no-vig、Power no-vig 与 Shin-style 交叉检查 {len(reports)} 组赔率；"
        f"最大方法差异 {max_shift:.2%}"
        + (f"，平均 overround {avg_overround:.2%}" if avg_overround is not None else "")
        + (f"，冷门偏差观察 {longshot_watch} 组，方法不稳定 {unstable_bias} 组。" if bias_reports else "。")
    )
    return _component(
        "odds_conversion_quality",
        "赔率转概率",
        avg_score,
        0.08,
        detail,
        "继续评估 Shin/Power/比例去水差异，尤其关注冷门和高水位比赛。",
    )


def _ensemble_component(preview: dict) -> dict:
    contexts = preview.get("contexts") or []
    has_contexts = bool(contexts)
    has_scores = any((ctx.get("top_scores") or []) for ctx in contexts)
    has_hhad = any((ctx.get("hhad_probs") or {}) for ctx in contexts)
    score = 45 + (18 if has_contexts else 0) + (12 if has_scores else 0) + (10 if has_hhad else 0)
    score = min(90, score)
    detail = "已融合市场、Poisson/xG proxy、Elo、Dixon-Coles 与让球概率。" if has_contexts else "尚未拿到完整模型上下文。"
    return _component("model_ensemble", "模型融合", score, 0.13, detail, "继续用赛果回填校准各模型权重。")


def _coverage_component(preview: dict) -> dict:
    completeness = preview.get("intelligence_completeness") or {}
    base = float(completeness.get("score") or 0)
    workflow = preview.get("prematch_workflow") or {}
    is_t_plus = str(workflow.get("stage") or "").startswith("t_plus_")
    score = min(88, base + (12 if is_t_plus else 0))
    if not score:
        score = 35
    detail = (
        f"情报完整度 {base:.0f}/100；T+1 阶段首发、临场天气和终盘赔率缺口按待确认处理。"
        if is_t_plus
        else f"情报完整度 {base:.0f}/100。"
    )
    return _component("intelligence_coverage", "情报覆盖", score, 0.13, detail, "补伤停、首发、天气、新闻事实和战意来源。")


def _calibration_component(preview: dict, optimizer_result: dict, learning_history: dict) -> dict:
    rankings = optimizer_result.get("candidate_rankings") or {}
    rows = list(rankings.get("singles") or []) + list(rankings.get("parlay_2x1") or [])
    sample_count = 0
    for row in rows:
        try:
            sample_count += int(row.get("probability_sample_count") or 0)
        except (TypeError, ValueError):
            pass
    daily = preview.get("daily_learning_metrics") or optimizer_result.get("daily_learning_metrics") or []
    settled = _safe_int(learning_history.get("settled_count"))
    quality = learning_history.get("probability_quality") or {}
    quality_samples = _safe_int(quality.get("sample_count"))
    evidence_count = max(sample_count, settled, quality_samples, len(daily))
    brier = _safe_float(learning_history.get("brier_score"))
    log_loss = _safe_float(learning_history.get("log_loss"))
    if evidence_count >= 100 and brier is not None and log_loss is not None:
        score = 92 if brier <= 0.20 and log_loss <= 0.62 else 78
        detail = f"已有 {evidence_count} 条概率校准样本，Brier {brier:.3f}，Log Loss {log_loss:.3f}。"
    elif evidence_count >= 30 and brier is not None and log_loss is not None:
        score = 84 if brier <= 0.24 and log_loss <= 0.70 else 68
        detail = f"已有 {evidence_count} 条已结算概率样本，可开始校准；Brier {brier:.3f}，Log Loss {log_loss:.3f}。"
    elif evidence_count >= 7:
        score = 64
        detail = f"已有 {evidence_count} 条学习样本，仍属小样本；校准只轻微影响排序。"
    elif evidence_count > 0:
        score = 54
        detail = f"已有 {evidence_count} 条学习样本，但不足以证明长期优势。"
    else:
        score = 42
        detail = "Brier/Log Loss 样本不足，当前校准主要依赖保守先验。"
    return _component("probability_calibration", "概率校准", score, 0.14, detail, "累计赛后结果，按玩法和赔率段看 Brier / Log Loss。")


def _clv_component(optimizer_result: dict, clv_history: dict) -> dict:
    clv = optimizer_result.get("clv_tracking") or {}
    current_settled = _safe_int(clv.get("settled_count") or 0)
    history_settled = _safe_int(clv_history.get("settled_count") or 0)
    settled = max(current_settled, history_settled)
    avg = clv.get("average_clv_pct")
    if avg is None:
        avg = clv_history.get("average_clv_pct")
    avg_float = _safe_float(avg)
    if avg_float is not None and settled >= 30:
        score = 90 if avg_float > 0.005 else 72 if avg_float >= -0.005 else 58
        detail = f"已有 {settled} 条 CLV 样本，平均 CLV {avg_float:+.2%}。"
    elif avg_float is not None and settled >= 10:
        score = 76 if avg_float > 0 else 60
        detail = f"已有 {settled} 条 CLV 样本，平均 CLV {avg_float:+.2%}，仍需扩大样本。"
    elif settled:
        score = 58
        detail = f"已有 {settled} 条 CLV 跟踪项，但样本仍少。"
    else:
        score = 34
        detail = "缺少收盘赔率样本，暂不能验证是否跑赢市场价格。"
    return _component("clv_market_test", "CLV 市场检验", score, 0.13, detail, "赛后补收盘赔率，验证赛前价格是否优于市场终盘。")


def _longshot_bias_component(optimizer_result: dict) -> dict:
    rankings = optimizer_result.get("candidate_rankings") or {}
    rows = []
    for key in ("singles", "parlay_2x1", "parlay_3x1"):
        rows.extend(rankings.get(key) or [])
    longshots = [row for row in rows if _safe_float(row.get("odds") or row.get("combo_odds")) and _safe_float(row.get("odds") or row.get("combo_odds")) >= 6]
    if not rows:
        return _component(
            "favorite_longshot_bias_control",
            "冷门偏差控制",
            52,
            0.10,
            "当前候选池不足，暂不能判断高赔率冷门是否被充分降权。",
            "继续保存候选与赛后结果，按赔率段校准冷门命中率。",
        )
    if not longshots:
        return _component(
            "favorite_longshot_bias_control",
            "冷门偏差控制",
            76,
            0.10,
            "当前候选池没有明显高赔率冷门，冷门偏差风险较低。",
            "继续按赔率段保存赛后命中率和 CLV。",
        )
    warned = sum(1 for row in longshots if row.get("longshot_warning") or row.get("longshot_parlay_blocked"))
    calibrated = sum(1 for row in longshots if row.get("calibrated_prob") is not None or row.get("calibrated_ev") is not None)
    blocked = sum(1 for row in longshots if row.get("parlay_eligible") is False or row.get("longshot_parlay_blocked"))
    discipline_rate = (warned + calibrated + blocked) / max(1, len(longshots) * 3)
    score = 45 + discipline_rate * 45
    detail = (
        f"发现 {len(longshots)} 个高赔率冷门；其中 {warned} 个有风险提示，"
        f"{calibrated} 个经过赔率段校准，{blocked} 个被阻止进入串联核心。"
    )
    return _component(
        "favorite_longshot_bias_control",
        "冷门偏差控制",
        score,
        0.10,
        detail,
        "继续按赔率段和概率段统计冷门实际命中、Brier、Log Loss 与 CLV。",
    )


def _portfolio_component(optimizer_result: dict) -> dict:
    rankings = optimizer_result.get("candidate_rankings") or {}
    combos = list(rankings.get("parlay_2x1") or []) + list(rankings.get("parlay_3x1") or [])
    if not combos:
        score, detail = 50, "当前组合候选不足。"
    else:
        diversity_hits = sum(1 for row in combos if (row.get("play_diversity") or {}).get("hard_block") is False and row.get("play_type_mix_zh"))
        blocked = sum(1 for row in combos if (row.get("play_diversity") or {}).get("hard_block"))
        homogeneity_rows = [row.get("combo_homogeneity") or {} for row in combos]
        homogeneity_blocked = sum(1 for row in homogeneity_rows if row.get("hard_block"))
        homogeneity_penalized = sum(1 for row in homogeneity_rows if float(row.get("penalty") or 0.0) > 0 and not row.get("hard_block"))
        homogeneity_clean = sum(1 for row in homogeneity_rows if row and float(row.get("penalty") or 0.0) <= 0)
        quality_scores = [
            int((row.get("correlation_quality") or {}).get("score") or 0)
            for row in combos
            if isinstance(row.get("correlation_quality"), dict)
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        score = min(88, 50 + diversity_hits * 4 + avg_quality * 0.25 + homogeneity_clean * 3 - blocked * 3 - homogeneity_blocked * 4 - homogeneity_penalized * 2)
        detail = (
            f"组合纪律已检查玩法分散、相关性质量与同质化风险；分散候选 {diversity_hits} 个，"
            f"玩法集中拦截 {blocked} 个，同质化拦截 {homogeneity_blocked} 个，同质化降权 {homogeneity_penalized} 个，"
            f"平均相关性质量 {avg_quality:.0f}/100。"
        )
    return _component("portfolio_discipline", "组合纪律", score, 0.07, detail, "继续限制同玩法扎堆、同方向同质化、同场互斥和低联合概率组合。")


def _play_bias_component(optimizer_result: dict) -> dict:
    diag = optimizer_result.get("play_bias_diagnostics") or {}
    sections = diag.get("sections") or []
    issues = diag.get("issues") or []
    if not diag:
        return _component(
            "play_bias_control",
            "玩法偏置纠偏",
            52,
            0.05,
            "当前没有玩法偏置诊断，无法判断候选是否过度集中在让球胜平负、胜平负、总进球或比分。",
            "输出单关、2串1、3串1时同步记录玩法分布，避免同一玩法刷屏。",
        )
    if not issues:
        score = 78
        detail = diag.get("summary_zh") or "玩法分布暂未明显偏置。"
    else:
        worst = max(sections, key=lambda row: float(row.get("top_play_share") or 0.0)) if sections else {}
        share = float(worst.get("top_play_share") or 0.0)
        if share >= 0.85:
            score = 42
        elif share >= 0.70:
            score = 52
        else:
            score = 62
        detail = (
            f"{diag.get('summary_zh') or '存在玩法偏置'} "
            f"最高集中项：{worst.get('label_zh', '候选')} / {worst.get('top_play_type', '未知')} {share:.0%}。"
        )
    return _component(
        "play_bias_control",
        "玩法偏置纠偏",
        score,
        0.05,
        detail,
        diag.get("next_step_zh") or "提高同玩法/同方向惩罚，并按玩法统计赛后命中率、ROI、Brier 和 CLV。",
    )


def _learning_component(preview: dict, optimizer_result: dict, learning_history: dict, clv_history: dict, ai_review_history: dict) -> dict:
    archive = preview.get("research_archive") or optimizer_result.get("research_archive") or {}
    ai = preview.get("ai_combo_research") or optimizer_result.get("ai_combo_research") or {}
    saved = bool(archive.get("latest_path") or archive.get("saved") or optimizer_result.get("learning_snapshot_path"))
    ds = bool(ai.get("ds_completed") or ai.get("provider") == "deepseek")
    settled = _safe_int(learning_history.get("settled_count"))
    clv_settled = _safe_int(clv_history.get("settled_count"))
    ai_reviewed = _safe_int(ai_review_history.get("reviewed_count"))
    ai_supported = _safe_int(ai_review_history.get("supported_count"))
    play_summary = _play_type_learning_summary(learning_history)
    score = 45 + (14 if saved else 0) + (9 if ds else 0)
    if settled >= 30 and clv_settled >= 20:
        score = max(score, 90)
    elif settled >= 7 or clv_settled >= 5:
        score = max(score, 74)
    elif settled > 0 or clv_settled > 0:
        score = max(score, 64)
    if ai_reviewed >= 10 and ai_supported >= max(1, int(ai_reviewed * 0.55)):
        score = min(92, score + 5)
    score = max(0, min(92, score + int(play_summary.get("score_adjustment", 0))))
    detail = (
        f"赛后学习样本 {settled} 条，CLV 样本 {clv_settled} 条，AI 假设复盘 {ai_reviewed} 条；"
        f"玩法复盘：{play_summary.get('summary_zh') or '暂无玩法证据'}；研究档案{'已' if saved else '未'}稳定保存。"
        if settled or clv_settled or saved or ai_reviewed
        else "研究档案/AI 摘要尚未形成稳定赛后学习闭环。"
    )
    return _component("learning_loop", "赛后学习闭环", min(92, score), 0.03, detail, "固定保存 T+1 快照，赛后回填比分和收盘赔率。")


def _score_ceiling(preview: dict, components: list[dict]) -> int:
    provider = str(preview.get("provider_used") or "")
    source_cap = _safe_int(build_source_reliability(preview).get("professional_score_cap"))
    if provider in {"mock", "fallback", "fixture"}:
        return 64
    if source_cap and source_cap < 95:
        return source_cap
    weak = [item for item in components if item["score"] < 55]
    if len(weak) >= 3:
        return 78
    if any(item["key"] == "clv_market_test" and item["score"] < 55 for item in components):
        return 86
    return 95


def _missing_to_95(components: list[dict], ceiling: int) -> list[str]:
    actions = [item["next_step_zh"] for item in sorted(components, key=lambda row: row["score"]) if item["score"] < 82]
    if ceiling < 95:
        actions.insert(0, "先解除当前评分上限：真实数据、情报覆盖、CLV 或校准样本仍不足。")
    return list(dict.fromkeys(actions))[:6]


def _score_gap_radar(components: list[dict]) -> list[dict]:
    rows = []
    for item in components:
        score = _safe_int(item.get("score"))
        target = _component_target(item.get("key"))
        gap = max(0, target - score)
        rows.append(
            {
                "key": item.get("key"),
                "label_zh": item.get("label_zh"),
                "score": score,
                "target_score": target,
                "gap_to_target": gap,
                "weight": item.get("weight", 0),
                "weighted_gap": round(gap * float(item.get("weight") or 0.0), 2),
                "impact_level": _gap_impact_level(gap, float(item.get("weight") or 0.0)),
                "impact_zh": _gap_impact_zh(gap, float(item.get("weight") or 0.0)),
                "detail_zh": item.get("detail_zh", ""),
                "next_step_zh": item.get("next_step_zh", ""),
            }
        )
    return sorted(rows, key=lambda row: (row["weighted_gap"], row["gap_to_target"]), reverse=True)


def _component_target(key: str | None) -> int:
    return {
        "market_baseline": 88,
        "odds_conversion_quality": 84,
        "model_ensemble": 86,
        "intelligence_coverage": 82,
        "probability_calibration": 88,
        "clv_market_test": 88,
        "favorite_longshot_bias_control": 84,
        "play_bias_control": 84,
        "portfolio_discipline": 84,
        "learning_loop": 86,
    }.get(str(key or ""), 82)


def _gap_impact_level(gap: int, weight: float) -> str:
    weighted = gap * weight
    if weighted >= 5:
        return "critical"
    if weighted >= 3:
        return "high"
    if weighted >= 1:
        return "medium"
    return "low"


def _gap_impact_zh(gap: int, weight: float) -> str:
    weighted = gap * weight
    if gap <= 0:
        return "已接近目标，保持跟踪。"
    if weighted >= 5:
        return "最大拖分项，优先处理。"
    if weighted >= 3:
        return "明显拖分项，建议排进下一轮。"
    if weighted >= 1:
        return "中等缺口，持续补样本。"
    return "轻微缺口，观察即可。"


def _learning_evidence(learning_history: dict, clv_history: dict, ai_review_history: dict) -> dict:
    quality = learning_history.get("probability_quality") or {}
    play_summary = _play_type_learning_summary(learning_history)
    market_benchmark = build_market_benchmark_from_learning(learning_history)
    return {
        "settled_count": learning_history.get("settled_count", 0),
        "hit_rate": learning_history.get("hit_rate"),
        "brier_score": learning_history.get("brier_score"),
        "log_loss": learning_history.get("log_loss"),
        "probability_quality_zh": quality.get("message_zh", ""),
        "clv_settled_count": clv_history.get("settled_count", 0),
        "average_clv_pct": clv_history.get("average_clv_pct"),
        "clv_summary_zh": clv_history.get("summary_zh", ""),
        "ai_hypothesis_reviewed_count": ai_review_history.get("reviewed_count", 0),
        "ai_hypothesis_supported_count": ai_review_history.get("supported_count", 0),
        "ai_hypothesis_failed_count": ai_review_history.get("failed_count", 0),
        "ai_hypothesis_supported_rate": ai_review_history.get("supported_rate"),
        "ai_hypothesis_summary_zh": ai_review_history.get("summary_zh", ""),
        "ai_factor_rows": ai_review_history.get("factor_rows", []),
        "ai_factor_summary_zh": _ai_factor_summary(ai_review_history.get("factor_rows", [])),
        "market_benchmark": market_benchmark,
        "market_benchmark_summary_zh": market_benchmark.get("summary_zh", ""),
        "play_type_rows": learning_history.get("play_type_rows", []),
        "play_type_sample_count": play_summary.get("sample_count", 0),
        "play_type_reliable_count": play_summary.get("reliable_count", 0),
        "play_type_weak_count": play_summary.get("weak_count", 0),
        "play_type_best": play_summary.get("best", {}),
        "play_type_weakest": play_summary.get("weakest", {}),
        "play_type_summary_zh": play_summary.get("summary_zh", ""),
        "evidence_zh": "分数会读取本机 data/learning_feedback、data/learning_clv 与 data/learning_ai_hypotheses；没有样本时不会假装接近 95。",
    }


def _play_type_learning_summary(learning_history: dict) -> dict:
    rows = [row for row in learning_history.get("play_type_rows", []) or [] if isinstance(row, dict)]
    if not rows:
        return {
            "sample_count": 0,
            "reliable_count": 0,
            "weak_count": 0,
            "score_adjustment": -3,
            "summary_zh": "暂无按玩法复盘样本，无法判断让球/胜平负/总进球哪类更可靠。",
        }
    reliable = [row for row in rows if _safe_int(row.get("attempts")) >= 10]
    weak = [
        row
        for row in reliable
        if (_safe_float(row.get("paper_roi")) is not None and _safe_float(row.get("paper_roi")) < -0.02)
        or (_safe_float(row.get("brier_score")) is not None and _safe_float(row.get("brier_score")) > 0.28)
    ]
    best = _best_play_type_row(reliable or rows)
    weakest = _weakest_play_type_row(reliable or rows)
    if not reliable:
        adjustment = -2
        summary = f"已有 {len(rows)} 类玩法记录，但单类样本不足 10 条，只能提示偏置，不能调大权重。"
    elif weak:
        adjustment = -4
        summary = f"发现 {len(weak)} 类玩法历史表现偏弱，模型体检扣分并要求优化器降权。"
    elif len(reliable) >= 3:
        adjustment = 4
        summary = "至少 3 类玩法已有可参考样本，玩法偏置开始有赛后证据约束。"
    else:
        adjustment = 1
        summary = "已有部分玩法可参考样本，但覆盖还不够广，暂只轻微加分。"
    return {
        "sample_count": len(rows),
        "reliable_count": len(reliable),
        "weak_count": len(weak),
        "best": best,
        "weakest": weakest,
        "score_adjustment": adjustment,
        "summary_zh": summary,
    }


def _best_play_type_row(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return max(rows, key=lambda row: (_safe_float(row.get("paper_roi")) if _safe_float(row.get("paper_roi")) is not None else -999.0, _safe_float(row.get("hit_rate")) or 0.0))


def _weakest_play_type_row(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return min(rows, key=lambda row: (_safe_float(row.get("paper_roi")) if _safe_float(row.get("paper_roi")) is not None else 999.0, -(_safe_float(row.get("brier_score")) or 0.0)))


def _play_type_roadmap_score(play_summary: dict) -> int:
    reliable = _safe_int(play_summary.get("reliable_count"))
    weak = _safe_int(play_summary.get("weak_count"))
    if reliable >= 4 and weak == 0:
        return 88
    if reliable >= 3 and weak == 0:
        return 82
    if reliable >= 2:
        return 72 if weak == 0 else 58
    if reliable >= 1:
        return 62 if weak == 0 else 52
    return 42


def _short_cycle_readiness_score(component_map: dict, settled: int, clv_settled: int) -> int:
    market = _safe_int((component_map.get("market_baseline") or {}).get("score"))
    odds = _safe_int((component_map.get("odds_conversion_quality") or {}).get("score"))
    portfolio = _safe_int((component_map.get("portfolio_discipline") or {}).get("score"))
    learning = _safe_int((component_map.get("learning_loop") or {}).get("score"))
    score = round(0.28 * market + 0.22 * odds + 0.25 * portfolio + 0.15 * learning)
    if settled >= 7:
        score += 6
    if settled >= 30:
        score += 5
    if clv_settled >= 5:
        score += 5
    if clv_settled >= 20:
        score += 5
    return max(35, min(92, score))


def _ai_research_quality(preview: dict, optimizer_result: dict, ai_review_history: dict) -> dict:
    ai = optimizer_result.get("ai_combo_research") or preview.get("ai_combo_research") or {}
    archive = preview.get("research_archive") or optimizer_result.get("research_archive") or {}
    structured = ai.get("structured_notes") or ((ai.get("ai_summary") or {}).get("structured_notes")) or {}
    cost = ai.get("ai_cost_ledger") or {}
    hypotheses = _extract_ai_hypotheses(ai, archive)
    ds_completed = bool(ai.get("ds_completed") or (ai.get("ai_summary") or {}).get("ds_completed"))
    token_total = _safe_int(ai.get("token_total") or (ai.get("ai_summary") or {}).get("token_total"))
    deepseek_calls = _safe_int(cost.get("deepseek_call_count"))
    has_summary = bool((ai.get("ai_summary") or {}).get("text") or ai.get("local_summary_zh") or ai.get("display_status_zh"))
    structured_count = _count_structured_notes(structured)
    archive_saved = bool(archive.get("latest_path") or archive.get("path") or archive.get("saved"))
    reviewed_count = _safe_int(ai_review_history.get("reviewed_count"))
    supported_count = _safe_int(ai_review_history.get("supported_count"))
    failed_count = _safe_int(ai_review_history.get("failed_count"))
    supported_rate = _safe_float(ai_review_history.get("supported_rate"))
    factor_rows = ai_review_history.get("factor_rows", []) or []
    weak_factor_count = len([row for row in factor_rows if _safe_int(row.get("reviewed")) >= 5 and (_safe_float(row.get("failed_rate")) or 0.0) >= 0.4])
    supported_factor_count = len([row for row in factor_rows if _safe_int(row.get("reviewed")) >= 5 and (_safe_float(row.get("supported_rate")) or 0.0) >= 0.6])
    quality_score = 25
    if has_summary:
        quality_score += 15
    if structured_count >= 3:
        quality_score += 20
    elif structured_count:
        quality_score += 10
    if ds_completed:
        quality_score += 18
    if token_total > 0:
        quality_score += 8
    if archive_saved:
        quality_score += 10
    if len(hypotheses) >= 5:
        quality_score += 10
    elif hypotheses:
        quality_score += 5
    if reviewed_count >= 10 and supported_rate is not None and supported_rate >= 0.6:
        quality_score += 12
    elif reviewed_count:
        quality_score += 5
    if supported_factor_count:
        quality_score += min(8, supported_factor_count * 3)
    if weak_factor_count:
        quality_score -= min(12, weak_factor_count * 4)
    if failed_count >= supported_count and reviewed_count >= 5:
        quality_score -= 10
    quality_score = min(92, quality_score)
    issues = []
    if not ds_completed:
        issues.append("DS Pro 未稳定完成，本轮解释可能是本地摘要。")
    if structured_count < 3:
        issues.append("结构化笔记覆盖不足，难以赛后验证 AI 判断质量。")
    if not archive_saved:
        issues.append("研究档案未确认保存，AI 摘要难以进入长期学习。")
    if not hypotheses:
        issues.append("缺少可验证假设，赛后难以判断 AI 当时说对了什么。")
    if reviewed_count <= 0:
        issues.append("AI 假设还没有赛后复盘历史，不能证明摘要有预测研究价值。")
    elif failed_count >= supported_count and reviewed_count >= 5:
        issues.append("AI 假设失败数不低于支持数，应降低 AI 摘要权重。")
    return {
        "score": quality_score,
        "grade": "A" if quality_score >= 82 else "B" if quality_score >= 68 else "C" if quality_score >= 50 else "D",
        "ds_completed": ds_completed,
        "token_total": token_total,
        "deepseek_call_count": deepseek_calls,
        "structured_note_count": structured_count,
        "verifiable_hypothesis_count": len(hypotheses),
        "reviewed_hypothesis_count": reviewed_count,
        "supported_hypothesis_count": supported_count,
        "failed_hypothesis_count": failed_count,
        "supported_hypothesis_rate": supported_rate,
        "factor_rows": factor_rows,
        "supported_factor_count": supported_factor_count,
        "weak_factor_count": weak_factor_count,
        "verifiable_hypotheses": hypotheses[:8],
        "archive_saved": archive_saved,
        "summary_zh": _ai_quality_summary(quality_score, ds_completed, structured_count, archive_saved, reviewed_count, supported_rate),
        "issues_zh": issues,
        "evidence_zh": [
            f"DS 完成：{'是' if ds_completed else '否'}。",
            f"Token 消耗：{token_total if token_total else '暂无'}。",
            f"结构化笔记：{structured_count} 条。",
            f"可验证假设：{len(hypotheses)} 条。",
            f"赛后已复盘 AI 假设：{reviewed_count} 条，支持率：{_format_pct(supported_rate)}。",
            _ai_factor_summary(factor_rows),
            f"研究档案：{'已保存' if archive_saved else '未确认'}。",
        ],
        "next_step_zh": "让 AI 输出必须包含可复盘假设：为什么保留、为什么拒绝、赛后用命中、CLV、Brier/Log Loss 或被拒组合复盘验证。",
        "disclaimer": "AI 研究只做解释、质检和复盘，不改写概率、不绕过可信度门控。",
    }


def _count_structured_notes(value) -> int:
    if isinstance(value, list):
        return len(value)
    if not isinstance(value, dict):
        return 0
    total = 0
    for item in value.values():
        if isinstance(item, list):
            total += len(item)
        elif isinstance(item, dict):
            total += 1
        elif item:
            total += 1
    return total


def _extract_ai_hypotheses(ai: dict, archive: dict) -> list[dict]:
    direct = ai.get("verifiable_hypotheses") or archive.get("verifiable_hypotheses")
    if isinstance(direct, list):
        return [item for item in direct if isinstance(item, dict)]
    nested = ((archive.get("latest") or {}).get("ai_research") or {}).get("verifiable_hypotheses")
    if isinstance(nested, list):
        return [item for item in nested if isinstance(item, dict)]
    ai_nested = (ai.get("ai_research") or {}).get("verifiable_hypotheses")
    if isinstance(ai_nested, list):
        return [item for item in ai_nested if isinstance(item, dict)]
    return []


def _ai_quality_summary(score: int, ds_completed: bool, structured_count: int, archive_saved: bool, reviewed_count: int = 0, supported_rate: float | None = None) -> str:
    if reviewed_count >= 10 and supported_rate is not None and supported_rate >= 0.6:
        return "AI 研究不仅有摘要和结构化假设，也已有赛后复盘支持，可作为解释质量证据之一。"
    if score >= 82:
        return "AI 研究层已有较完整摘要、结构化笔记和档案证据，可用于赛后复盘解释质量。"
    if ds_completed:
        return "DS Pro 已参与，但结构化覆盖或档案证据仍需加强。"
    if archive_saved:
        return "AI 研究已进入档案，但当前主要依赖本地摘要或未稳定触发 DS。"
    return "AI 研究还不能证明有效；当前只应视为辅助解释，不应提升模型可信度。"


def _ai_factor_summary(rows: list[dict]) -> str:
    rows = [row for row in rows or [] if isinstance(row, dict)]
    reviewed = [row for row in rows if _safe_int(row.get("reviewed")) > 0]
    if not reviewed:
        return "AI 因子还没有可结算复盘样本。"
    best = max(reviewed, key=lambda row: _safe_float(row.get("supported_rate")) if _safe_float(row.get("supported_rate")) is not None else -1.0)
    weak = max(reviewed, key=lambda row: _safe_float(row.get("failed_rate")) if _safe_float(row.get("failed_rate")) is not None else -1.0)
    return (
        f"AI 因子复盘：目前相对较好的是 {best.get('ai_factor_zh') or best.get('ai_factor')} "
        f"支持率 {_format_pct(_safe_float(best.get('supported_rate')))}；"
        f"最需复查的是 {weak.get('ai_factor_zh') or weak.get('ai_factor')} "
        f"失败率 {_format_pct(_safe_float(weak.get('failed_rate')))}。"
    )


def _score_trend(current_score: int, ceiling: int, components: list[dict], learning_history: dict) -> dict:
    windows = learning_history.get("window_metrics") or []
    if not windows:
        return {
            "status": "empty",
            "summary_zh": "暂无 7 天 / 30 天学习窗口，先累计赛后结果和收盘赔率。",
            "rows": [],
        }
    component_map = {item.get("key"): item for item in components}
    rows = []
    for row in windows:
        estimated = _window_score_estimate(row, component_map, ceiling)
        rows.append(
            {
                "window": row.get("window"),
                "label_zh": row.get("label_zh") or row.get("window"),
                "date_from": row.get("date_from"),
                "date_to": row.get("date_to"),
                "estimated_score": estimated,
                "settled_count": row.get("settled_count", 0),
                "clv_settled_count": row.get("clv_settled_count", 0),
                "hit_rate": row.get("hit_rate"),
                "paper_roi": row.get("paper_roi"),
                "brier_score": row.get("brier_score"),
                "log_loss": row.get("log_loss"),
                "average_clv_pct": row.get("average_clv_pct"),
                "message_zh": _window_score_message(row, estimated),
            }
        )
    by_window = {row.get("window"): row for row in rows}
    last_7 = by_window.get("last_7_days", {})
    last_30 = by_window.get("last_30_days", {})
    all_time = by_window.get("all_time", {})
    trend_delta = None
    if last_7.get("estimated_score") is not None and all_time.get("estimated_score") is not None:
        trend_delta = int(last_7["estimated_score"]) - int(all_time["estimated_score"])
    return {
        "status": "ok",
        "current_score": current_score,
        "ceiling_score": ceiling,
        "trend_delta_vs_all_time": trend_delta,
        "direction": "up" if trend_delta is not None and trend_delta > 2 else "down" if trend_delta is not None and trend_delta < -2 else "flat",
        "summary_zh": _trend_summary(trend_delta, last_7, last_30),
        "rows": rows,
    }


def _window_score_estimate(row: dict, component_map: dict, ceiling: int) -> int:
    updated_scores = {}
    for item in component_map.values():
        updated_scores[item.get("key")] = _safe_int(item.get("score"))
    updated_scores["probability_calibration"] = _calibration_score_from_window(row)
    updated_scores["clv_market_test"] = _clv_score_from_window(row)
    updated_scores["learning_loop"] = _learning_score_from_window(row)
    weighted = 0.0
    for item in component_map.values():
        key = item.get("key")
        weighted += float(item.get("weight") or 0.0) * updated_scores.get(key, _safe_int(item.get("score")))
    return min(ceiling, max(0, round(weighted)))


def _calibration_score_from_window(row: dict) -> int:
    settled = _safe_int(row.get("settled_count"))
    brier = _safe_float(row.get("brier_score"))
    log_loss = _safe_float(row.get("log_loss"))
    if settled >= 100 and brier is not None and log_loss is not None:
        return 92 if brier <= 0.20 and log_loss <= 0.62 else 78
    if settled >= 30 and brier is not None and log_loss is not None:
        return 84 if brier <= 0.24 and log_loss <= 0.70 else 68
    if settled >= 7:
        return 64
    if settled > 0:
        return 54
    return 42


def _clv_score_from_window(row: dict) -> int:
    settled = _safe_int(row.get("clv_settled_count"))
    avg = _safe_float(row.get("average_clv_pct"))
    if avg is not None and settled >= 30:
        return 90 if avg > 0.005 else 72 if avg >= -0.005 else 58
    if avg is not None and settled >= 10:
        return 76 if avg > 0 else 60
    if settled:
        return 58
    return 34


def _learning_score_from_window(row: dict) -> int:
    settled = _safe_int(row.get("settled_count"))
    clv_settled = _safe_int(row.get("clv_settled_count"))
    if settled >= 30 and clv_settled >= 20:
        return 90
    if settled >= 7 or clv_settled >= 5:
        return 74
    if settled > 0 or clv_settled > 0:
        return 64
    return 45


def _window_score_message(row: dict, estimated: int) -> str:
    settled = _safe_int(row.get("settled_count"))
    clv_count = _safe_int(row.get("clv_settled_count"))
    if settled <= 0:
        return "该窗口暂无可结算样本，不参与趋势判断。"
    if clv_count <= 0:
        return f"该窗口有 {settled} 条赛后样本，但缺 CLV，分数只能反映赛果和概率质量。"
    return f"该窗口有 {settled} 条赛后样本、{clv_count} 条 CLV，估算职业分 {estimated}。"


def _trend_summary(delta: int | None, last_7: dict, last_30: dict) -> str:
    if delta is None:
        return "趋势样本不足，先累计 7 天和 30 天复盘。"
    if delta > 2:
        return f"近 7 天估算分比累计高 {delta} 分，说明近期样本方向改善；仍需看 30 天是否确认。"
    if delta < -2:
        return f"近 7 天估算分比累计低 {abs(delta)} 分，说明近期样本走弱；优先复查赔率段、CLV 和冷门降权。"
    return "近 7 天与累计分差不大，当前更像稳定累计阶段；继续补样本比调权重更重要。"


def _roadmap_to_95(score: int, ceiling: int, components: list[dict], learning_history: dict, clv_history: dict) -> dict:
    component_map = {item.get("key"): item for item in components}
    settled = _safe_int(learning_history.get("settled_count"))
    clv_settled = _safe_int(clv_history.get("settled_count"))
    brier = _safe_float(learning_history.get("brier_score"))
    log_loss = _safe_float(learning_history.get("log_loss"))
    average_clv = _safe_float(clv_history.get("average_clv_pct"))
    play_summary = _play_type_learning_summary(learning_history)
    items = [
        _roadmap_item(
            "market_data",
            "稳定真实赔率基准",
            component_map.get("market_baseline", {}).get("score", 0),
            "Sporttery 主赔率 + 海外赔率交叉验证，避免 fallback/mock 把模型上限锁死。",
            "数据源稳定且 provider_used 不再回退时，职业评分上限才可能打开到 95。",
        ),
        _roadmap_item(
            "odds_conversion",
            "提升赔率转概率质量",
            component_map.get("odds_conversion_quality", {}).get("score", 0),
            "当前需要同时查看比例去水、Power 转换、Shin-style 转换、overround 和方法差异。",
            "赔率转概率是所有 Edge/EV 的地基；地基粗糙会直接误导组合。",
        ),
        _roadmap_item(
            "calibration_samples",
            "累计概率校准样本",
            component_map.get("probability_calibration", {}).get("score", 0),
            f"当前已结算样本 {settled} 条；目标先到 30 条，再到 100 条。",
            "用 Brier / Log Loss 验证模型概率，不靠单日命中率判断。",
        ),
        _roadmap_item(
            "clv_samples",
            "验证是否跑赢收盘赔率",
            component_map.get("clv_market_test", {}).get("score", 0),
            f"当前 CLV 样本 {clv_settled} 条；目标先到 20 条，再到 30 条以上。",
            "长期平均 CLV 为正，才说明赛前价格判断可能领先市场。",
        ),
        _roadmap_item(
            "play_type_learning",
            "验证不同玩法是否真的有效",
            _play_type_roadmap_score(play_summary),
            f"当前可参考玩法 {play_summary.get('reliable_count', 0)} 类，弱玩法 {play_summary.get('weak_count', 0)} 类。",
            "让球胜平负、胜平负、总进球、比分和串联都要被赛后样本约束，避免模型机械重复同一玩法。",
        ),
        _roadmap_item(
            "favorite_longshot_bias",
            "控制高赔率冷门偏差",
            component_map.get("favorite_longshot_bias_control", {}).get("score", 0),
            "高赔率冷门必须经过赔率段校准、冷门降权和串联禁入检查。",
            "主流模型会专门处理 favourite-longshot bias，防止被表面高 EV 诱导。",
        ),
        _roadmap_item(
            "play_bias_control",
            "纠正玩法扎堆偏置",
            component_map.get("play_bias_control", {}).get("score", 0),
            "检查候选是否过度集中在让球胜平负、同方向或同类型组合。",
            "如果页面总是同一种玩法，说明模型可能被赔率结构或候选池偏置牵着走，必须降权并赛后验证。",
        ),
        _roadmap_item(
            "intelligence_coverage",
            "补齐关键赛前情报",
            component_map.get("intelligence_coverage", {}).get("score", 0),
            "伤停、首发、天气、新闻事实、战意和中立场信息要区分 confirmed / fallback / unknown。",
            "情报越完整，冷门和串联的可信度折扣越少。",
        ),
        _roadmap_item(
            "portfolio_discipline",
            "组合纪律长期复盘",
            component_map.get("portfolio_discipline", {}).get("score", 0),
            "记录被拒组合赛后是否全中，复查同玩法扎堆、同方向同质化、相关性和低联合概率规则。",
            "如果被拒组合长期表现好，再放宽门控；否则保持严格，尤其避免把同一逻辑腿误认为分散。",
        ),
        _roadmap_item(
            "worldcup_short_cycle",
            "世界杯短周期闭环",
            _short_cycle_readiness_score(component_map, settled, clv_settled),
            "每个比赛日前固定输出单关、2串1、3串1纸面候选，锁定赛前赔率、模型概率、DS/本地解释和拒绝原因。",
            "短赛会没有时间等大样本训练成熟，只能用市场校准、终盘赔率、赛后命中、Brier/Log Loss/CLV 快速反馈。",
        ),
        _roadmap_item(
            "learning_loop",
            "固定 T+1 档案与赛后回填",
            component_map.get("learning_loop", {}).get("score", 0),
            "每天保存赛前快照，赛后补比分和收盘赔率，不允许赛后倒推。",
            "这是从研究工具走向职业级系统的主干。",
        ),
    ]
    ranked_actions = sorted(
        [item for item in items if item["status"] != "done"],
        key=lambda item: (item.get("estimated_score_gain", 0), -item.get("score", 0)),
        reverse=True,
    )
    for index, item in enumerate(ranked_actions, start=1):
        item["priority_rank"] = index
    top_action = ranked_actions[0] if ranked_actions else {}
    return {
        "target_score": 95,
        "current_score": score,
        "ceiling_score": ceiling,
        "can_reach_95_now": ceiling >= 95 and score >= 90,
        "next_best_actions": ranked_actions[:3],
        "estimated_score_gain": top_action.get("estimated_score_gain", 0),
        "priority_zh": top_action.get("priority_zh", "保持跟踪"),
        "items": items,
        "evidence_snapshot": {
            "settled_count": settled,
            "clv_settled_count": clv_settled,
            "brier_score": brier,
            "log_loss": log_loss,
            "average_clv_pct": average_clv,
        },
        "summary_zh": _roadmap_summary(score, ceiling, settled, clv_settled),
    }


def _evidence_requirements(score: int, ceiling: int, components: list[dict], learning_history: dict, clv_history: dict) -> dict:
    settled = _safe_int(learning_history.get("settled_count"))
    clv_settled = _safe_int(clv_history.get("settled_count"))
    brier = _safe_float(learning_history.get("brier_score"))
    log_loss = _safe_float(learning_history.get("log_loss"))
    average_clv = _safe_float(clv_history.get("average_clv_pct"))
    market_skill = build_market_benchmark_from_learning(learning_history)
    market_skill_score = _safe_float(market_skill.get("brier_skill_score"))
    by_key = {item.get("key"): _safe_int(item.get("score")) for item in components}
    ai_history = _safe_build_ai_review_history_for_requirements()
    ai_reviewed = _safe_int(ai_history.get("reviewed_count"))
    ai_supported_rate = _safe_float(ai_history.get("supported_rate"))
    rows = [
        _evidence_gate_row(
            level=60,
            label="可用研究级",
            requirements=[
                ("settled_count", settled, 7, "至少 7 条赛后结算样本"),
                ("market_baseline", by_key.get("market_baseline", 0), 55, "真实或清晰标记的数据源"),
                ("portfolio_discipline", by_key.get("portfolio_discipline", 0), 55, "组合纪律不低于基础线"),
            ],
            current_score=score,
            ceiling=ceiling,
        ),
        _evidence_gate_row(
            level=75,
            label="强研究级",
            requirements=[
                ("settled_count", settled, 30, "至少 30 条赛后结算样本"),
                ("clv_settled_count", clv_settled, 10, "至少 10 条收盘赔率 CLV 样本"),
                ("probability_calibration", by_key.get("probability_calibration", 0), 68, "Brier / Log Loss 已能参与校准"),
                ("intelligence_coverage", by_key.get("intelligence_coverage", 0), 62, "关键情报缺口有状态分层"),
                ("portfolio_discipline", by_key.get("portfolio_discipline", 0), 62, "组合纪律含相关性和同质化审计"),
            ],
            current_score=score,
            ceiling=ceiling,
        ),
        _evidence_gate_row(
            level=85,
            label="准职业级",
            requirements=[
                ("settled_count", settled, 100, "至少 100 条赛后结算样本"),
                ("clv_settled_count", clv_settled, 30, "至少 30 条 CLV 样本"),
                ("brier_score", brier, 0.22, "Brier 需要进入可接受区间", True),
                ("log_loss", log_loss, 0.68, "Log Loss 不能显示明显过度自信", True),
                ("clv_market_test", by_key.get("clv_market_test", 0), 72, "CLV 市场检验不能拖后腿"),
                ("market_skill_score", market_skill_score, 0.0, "模型 Brier 至少不能差于市场概率基准"),
                ("portfolio_discipline", by_key.get("portfolio_discipline", 0), 75, "组合纪律能压住玩法扎堆和同质化"),
                ("ai_hypothesis_reviewed", ai_reviewed, 20, "至少 20 条 AI/DS 假设完成赛后复盘"),
            ],
            current_score=score,
            ceiling=ceiling,
        ),
        _evidence_gate_row(
            level=95,
            label="职业级目标",
            requirements=[
                ("settled_count", settled, 300, "跨日期/赛事累计 300+ 已结算观察"),
                ("clv_settled_count", clv_settled, 100, "100+ CLV 样本，能按玩法和赔率段拆分"),
                ("average_clv_pct", average_clv, 0.002, "平均 CLV 至少略为正"),
                ("market_skill_score", market_skill_score, 0.03, "模型相对市场 Brier Skill 至少 +3%"),
                ("market_baseline", by_key.get("market_baseline", 0), 82, "真实赔率基准稳定"),
                ("odds_conversion_quality", by_key.get("odds_conversion_quality", 0), 78, "赔率转概率有多方法交叉检查"),
                ("favorite_longshot_bias_control", by_key.get("favorite_longshot_bias_control", 0), 78, "冷门偏差有显式降权"),
                ("play_bias_control", by_key.get("play_bias_control", 0), 78, "玩法扎堆偏置已被纠正"),
                ("portfolio_discipline", by_key.get("portfolio_discipline", 0), 82, "组合纪律接近职业级，含同质化审计"),
                ("intelligence_coverage", by_key.get("intelligence_coverage", 0), 78, "情报覆盖足够支持组合判断"),
                ("ai_hypothesis_reviewed", ai_reviewed, 50, "至少 50 条 AI/DS 假设完成赛后复盘"),
                ("ai_hypothesis_supported_rate", ai_supported_rate, 0.55, "AI/DS 假设赛后支持率不低于 55%"),
            ],
            current_score=score,
            ceiling=ceiling,
        ),
    ]
    next_gate = next((row for row in rows if not row["passed"]), rows[-1])
    sample_progress = _sample_progress_to_gate(next_gate, settled, clv_settled)
    return {
        "current_score": score,
        "ceiling_score": ceiling,
        "next_gate": next_gate,
        "rows": rows,
        "sample_progress": sample_progress,
        "gate_checklist": _gate_checklist(rows),
        "summary_zh": (
            f"下一道证据门槛是 {next_gate['level']} 分：{next_gate['label_zh']}。"
            if not next_gate.get("passed")
            else "当前已通过全部列出的证据门槛，后续重点是持续稳定。"
        ),
        "note_zh": "职业级不是靠单日命中证明，而是靠长期赛前记录、赛后校准、收盘赔率和情报覆盖共同证明。",
    }


def _sample_progress_to_gate(next_gate: dict, settled: int, clv_settled: int) -> dict:
    checks = next_gate.get("checks") or []
    settled_check = next((item for item in checks if item.get("key") == "settled_count"), {})
    clv_check = next((item for item in checks if item.get("key") == "clv_settled_count"), {})
    settled_target = _safe_int(settled_check.get("target"))
    clv_target = _safe_int(clv_check.get("target"))
    settled_missing = max(0, settled_target - settled) if settled_target else 0
    clv_missing = max(0, clv_target - clv_settled) if clv_target else 0
    settled_pct = round(min(100, (settled / settled_target) * 100)) if settled_target else 100
    clv_pct = round(min(100, (clv_settled / clv_target) * 100)) if clv_target else 100
    if settled_missing and clv_missing:
        next_action = f"下一档最缺：再补 {settled_missing} 条赛后结果、{clv_missing} 条收盘赔率。"
    elif settled_missing:
        next_action = f"下一档最缺：再补 {settled_missing} 条赛后结果。"
    elif clv_missing:
        next_action = f"下一档最缺：再补 {clv_missing} 条收盘赔率。"
    else:
        next_action = "样本数量已接近下一档，继续看 Brier、Log Loss、CLV 是否达标。"
    return {
        "gate_level": next_gate.get("level"),
        "gate_label_zh": next_gate.get("label_zh", ""),
        "settled_current": settled,
        "settled_target": settled_target,
        "settled_missing": settled_missing,
        "settled_progress_pct": settled_pct,
        "clv_current": clv_settled,
        "clv_target": clv_target,
        "clv_missing": clv_missing,
        "clv_progress_pct": clv_pct,
        "one_result_impact_zh": "新增 1 条赛后比分，会推进概率校准样本；样本足够后才影响 Brier / Log Loss 权重。",
        "one_clv_impact_zh": "新增 1 条收盘赔率，会推进 CLV 市场检验；长期为正才说明价格判断可能领先市场。",
        "next_action_zh": next_action,
    }


def _gate_checklist(rows: list[dict]) -> list[dict]:
    checklist = []
    for row in rows:
        missing = [item for item in (row.get("checks") or []) if not item.get("passed")]
        checklist.append(
            {
                "level": row.get("level"),
                "label_zh": row.get("label_zh", ""),
                "passed": row.get("passed", False),
                "missing_count": len(missing),
                "next_missing_zh": "、".join(item.get("label_zh", "") for item in missing[:3]) if missing else "已满足该档门槛",
                "message_zh": row.get("message_zh", ""),
            }
        )
    return checklist


@lru_cache(maxsize=1)
def _safe_build_ai_review_history_for_requirements() -> dict:
    try:
        return build_ai_hypothesis_review_history()
    except Exception:
        return {}


def _evidence_gate_row(level: int, label: str, requirements: list[tuple], current_score: int, ceiling: int) -> dict:
    checks = []
    for key, current, target, label_zh, *flags in requirements:
        reverse = bool(flags and flags[0])
        current_value = _safe_float(current)
        target_value = _safe_float(target)
        if current_value is None:
            passed = False
            missing = target
        elif reverse:
            passed = current_value <= target_value
            missing = 0 if passed else round(current_value - target_value, 4)
        else:
            passed = current_value >= target_value
            missing = 0 if passed else round(target_value - current_value, 4)
        checks.append(
            {
                "key": key,
                "label_zh": label_zh,
                "current": current,
                "target": target,
                "passed": passed,
                "missing": missing,
                "status_zh": "通过" if passed else "未达标",
            }
        )
    passed = current_score >= level and ceiling >= level and all(item["passed"] for item in checks)
    blockers = [item for item in checks if not item["passed"]]
    return {
        "level": level,
        "label_zh": label,
        "passed": passed,
        "status_zh": "通过" if passed else "未达标",
        "blockers_zh": [item["label_zh"] for item in blockers[:4]],
        "checks": checks,
        "message_zh": "已满足该级别证据门槛。" if passed else f"还缺：{'、'.join(item['label_zh'] for item in blockers[:4])}。",
    }


def _roadmap_item(key: str, label: str, score: int | float, current_state: str, why: str) -> dict:
    value = _safe_int(score)
    if value >= 82:
        status, status_zh = "done", "已接近职业要求"
    elif value >= 65:
        status, status_zh = "in_progress", "已有基础，继续补样本"
    else:
        status, status_zh = "todo", "当前主要短板"
    estimated_gain = _estimated_gain_to_95(value)
    return {
        "key": key,
        "label_zh": label,
        "score": value,
        "status": status,
        "status_zh": status_zh,
        "estimated_score_gain": estimated_gain,
        "priority_zh": _priority_label(estimated_gain),
        "current_state_zh": current_state,
        "why_it_matters_zh": why,
    }


def _estimated_gain_to_95(score: int) -> int:
    if score >= 82:
        return 0
    if score >= 65:
        return max(2, min(6, round((82 - score) * 0.25 + 1)))
    return max(5, min(12, round((65 - score) * 0.15 + 5)))


def _priority_label(gain: int) -> str:
    if gain >= 9:
        return "优先做，最可能抬高上限"
    if gain >= 5:
        return "第二优先，能明显改善"
    if gain > 0:
        return "持续补，逐步加分"
    return "保持跟踪"


def _roadmap_summary(score: int, ceiling: int, settled: int, clv_settled: int) -> str:
    if score >= 90 and ceiling >= 95:
        return "已接近职业级，但仍要持续赛后验证，防止短期过拟合。"
    if ceiling < 95:
        return f"当前不是模型想保守，而是证据上限只有 {ceiling}/95；已结算 {settled} 条、CLV {clv_settled} 条，先补真实样本和收盘赔率。"
    return f"上限已打开，但当前分数 {score}/100；继续补校准、CLV 和情报覆盖。"


def _industry_benchmark(components: list[dict]) -> list[dict]:
    by_key = {item.get("key"): item for item in components}
    checks = [
        (
            "market_calibrated",
            "市场校准",
            "职业模型通常先把赔率市场转成无水概率，再证明模型能改善市场基准。",
            "market_baseline",
            82,
        ),
        (
            "odds_conversion_checked",
            "赔率转换方法",
            "比例去水只是基础，职业级模型会用 Power/Shin-style 等方法交叉检查水位与冷门偏差。",
            "odds_conversion_quality",
            78,
        ),
        (
            "probability_calibrated",
            "概率校准",
            "预测不是只猜对方向，而是 60% 的事长期接近 60% 发生；用 Brier / Log Loss 验证。",
            "probability_calibration",
            82,
        ),
        (
            "closing_line_tested",
            "收盘赔率检验",
            "长期 CLV 为正，才说明赛前价格判断可能领先市场，而不是只靠赛果运气。",
            "clv_market_test",
            82,
        ),
        (
            "longshot_bias_adjusted",
            "冷门偏差修正",
            "高赔率冷门容易制造表面 EV，必须按赔率段降权并禁止低可信冷门进串联核心。",
            "favorite_longshot_bias_control",
            78,
        ),
        (
            "play_bias_controlled",
            "玩法偏置控制",
            "如果候选长期集中在让球胜平负或同一方向，模型必须降权并用赛后样本证明该玩法真的有效。",
            "play_bias_control",
            78,
        ),
        (
            "context_verified",
            "赛前情报验证",
            "伤停、首发、天气、新闻事实和战意必须分 confirmed / fallback / unknown，不编造。",
            "intelligence_coverage",
            78,
        ),
        (
            "portfolio_disciplined",
            "组合纪律",
            "2串1/3串1 要看联合概率、相关性、玩法分散和回撤，不是赔率越高越好。",
            "portfolio_discipline",
            78,
        ),
    ]
    out = []
    for key, label, detail, component_key, pass_score in checks:
        component = by_key.get(component_key, {})
        score = _safe_int(component.get("score"))
        passed = score >= pass_score
        out.append(
            {
                "key": key,
                "label_zh": label,
                "status": "passed" if passed else "not_yet",
                "status_zh": "通过" if passed else "未达标",
                "score": score,
                "pass_score": pass_score,
                "detail_zh": detail,
                "next_step_zh": component.get("next_step_zh", ""),
            }
        )
    return out


def _learning_history(preview: dict, optimizer_result: dict) -> dict:
    supplied = optimizer_result.get("learning_history") or preview.get("learning_history")
    if isinstance(supplied, dict):
        return supplied
    return _cached_learning_history()


def _clv_history(preview: dict, optimizer_result: dict) -> dict:
    supplied = optimizer_result.get("clv_history") or preview.get("clv_history")
    if isinstance(supplied, dict):
        return supplied
    return _cached_clv_history()


def _ai_review_history(preview: dict, optimizer_result: dict) -> dict:
    supplied = optimizer_result.get("ai_hypothesis_review_history") or preview.get("ai_hypothesis_review_history")
    if isinstance(supplied, dict):
        return supplied
    return _cached_ai_review_history()


@lru_cache(maxsize=1)
def _cached_learning_history() -> dict:
    try:
        return build_learning_history()
    except Exception as exc:
        return {"settled_count": 0, "errors": [{"message_zh": f"累计学习读取失败：{str(exc).splitlines()[0]}"}]}


@lru_cache(maxsize=1)
def _cached_clv_history() -> dict:
    try:
        return build_clv_history()
    except Exception as exc:
        return {"settled_count": 0, "errors": [{"message_zh": f"CLV 学习读取失败：{str(exc).splitlines()[0]}"}]}


@lru_cache(maxsize=1)
def _cached_ai_review_history() -> dict:
    try:
        return build_ai_hypothesis_review_history()
    except Exception as exc:
        return {"reviewed_count": 0, "errors": [{"message_zh": f"AI 假设复盘读取失败：{str(exc).splitlines()[0]}"}]}


def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_pct(value) -> str:
    number = _safe_float(value)
    if number is None:
        return "暂无"
    return f"{number:.1%}"


def _component(key: str, label: str, score: float, weight: float, detail: str, next_step: str) -> dict:
    bounded = max(0, min(100, round(float(score))))
    return {
        "key": key,
        "label_zh": label,
        "score": bounded,
        "weight": weight,
        "detail_zh": detail,
        "next_step_zh": next_step,
    }


def _label(score: int) -> str:
    if score >= 90:
        return "接近职业级"
    if score >= 78:
        return "强研究级"
    if score >= 62:
        return "可用研究级"
    return "基础研究级"


def _summary(score: int, ceiling: int, components: list[dict]) -> str:
    weakest = min(components, key=lambda row: row["score"])
    if score >= 90:
        return "市场、校准、情报和学习闭环已较完整，仍需持续赛后验证。"
    return f"当前职业模型分 {score}/100，理论上限 {ceiling}/95；最弱环节是{weakest['label_zh']}。"

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "src/dashboard/static/index.html").read_text(encoding="utf-8")
APP_JS = (ROOT / "src/dashboard/static/app.js").read_text(encoding="utf-8")


def test_dashboard_has_optimizer_page():
    for text in ["赛前优化", "今日赛前组合优化", "生成观察组合", "放弃的候选", "风险解释"]:
        assert text in HTML


def test_dashboard_optimizer_page_has_no_betting_controls():
    button_text = " ".join(part.split("</button>")[0] for part in HTML.split("<button")[1:])
    for forbidden in ["下注", "投注", "购买", "下单", "支付", "代购"]:
        assert forbidden not in button_text


def test_optimizer_page_renders_decision_board_before_detail_tables():
    for text in ["optimizerDecisionBoard", "先看结论，再看细表", "模型-市场一致性", "玩法偏置", "组合同质化", "赛后学习调参", "概率纪律校准", "稳健价值检验", "原模型概率", "校准概率", "概率区间", "赛事语境", "AI因子", "同质化审计", "proScoreConclusionStrip", "最大拖分项", "第一动作", "行业基准", "proGateChecklist", "证据门槛", "市场技能分", "市场基准纪律"]:
        assert text in APP_JS

from __future__ import annotations

from src.explain.safety import DISCLAIMER_TEXT


def build_onboarding_view() -> dict:
    steps = [
        {
            "step": 1,
            "title": "先用 mock 数据体验",
            "summary": "不用准备文件，直接查看一套完整的比赛、概率、候选信号和组合风险示例。",
            "action_label": "开始体验 mock 分析",
            "status": "ready",
        },
        {
            "step": 2,
            "title": "查看竞彩足球比赛",
            "summary": "选择 auto / sporttery / mock 数据源，查看 provider_used 和数据源提醒。",
            "action_label": "查看竞彩足球比赛",
            "status": "ready",
        },
        {
            "step": 3,
            "title": "导入自己的历史 CSV",
            "summary": "先做字段预检，确认日期、赛事、主队、客队、比分和赔率字段。",
            "action_label": "导入历史 CSV",
            "status": "ready",
        },
        {
            "step": 4,
            "title": "运行概率回测",
            "summary": "查看命中率、ROI、最大回撤、Brier Score、Log Loss 和校准分箱。",
            "action_label": "运行概率回测",
            "status": "ready",
        },
        {
            "step": 5,
            "title": "生成校准文件",
            "summary": "完整写文件流程通过 CLI 执行；App 默认只读，只显示校准状态。",
            "action_label": "查看校准状态",
            "status": "cli_only",
        },
        {
            "step": 6,
            "title": "查看候选信号与组合风险",
            "summary": "把候选方向加入临时观察清单，并阅读概率差、EV、风险等级和本地解释。",
            "action_label": "查看候选信号",
            "status": "ready",
        },
    ]
    return {
        "title": "JC Edge onboarding",
        "summary_cards": [
            {"label": "App", "value": "JC Edge", "help": "football-jc-analysis 的本地只读 App 名称。"},
            {"label": "模式", "value": "Read-only local", "help": "默认只监听 127.0.0.1，不写文件。"},
            {"label": "数据源", "value": "mock / sporttery / auto", "help": "auto 会尝试 Sporttery，失败时回退 mock。"},
            {"label": "用途", "value": "概率研究", "help": "展示概率、EV、回测诊断与风险解释。"},
        ],
        "steps": steps,
        "important_notes": [
            "本工具不会告诉你必买哪场，也不会自动下单。",
            "它只展示概率、EV、回测和风险解释，帮助你做研究判断。",
            "实际购彩请用户自行遵守当地法律法规并通过合法官方渠道独立判断。",
        ],
        "warnings": [],
        "disclaimer": DISCLAIMER_TEXT,
    }

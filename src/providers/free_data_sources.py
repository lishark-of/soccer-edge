from __future__ import annotations

import os

from src.config.local_env import build_secret_config_status, load_local_env


def build_free_data_source_status() -> dict:
    load_local_env()
    secret_status = build_secret_config_status()
    secret_by_key = {item["key"]: item for item in secret_status["keys"]}
    sources = [
        {
            "key": "sporttery",
            "name": "Sporttery 官方公开数据",
            "cost_zh": "免费",
            "role_zh": "竞彩足球可售比赛与官方赔率主数据源。",
            "coverage_zh": "竞彩足球胜平负、让球胜平负等公开可售数据。",
            "status": "enabled",
            "needs_account": False,
            "needs_api_key": False,
            "env_var": None,
            "signup_url": "https://www.sporttery.cn/",
            "docs_url": "https://www.sporttery.cn/",
            "setup_action_zh": "无需注册；App 已默认启用。",
            "default_behavior_zh": "App 默认优先尝试；失败时不伪装，会显示回退或缓存状态。",
            "reliability_note_zh": "这是最贴近中国竞彩的免费来源，但不是商业 SLA API，可能受网络、证书或接口变更影响。",
        },
        {
            "key": "the_odds_api",
            "name": "The Odds API",
            "cost_zh": "有免费额度",
            "role_zh": "国际赔率交叉参考，不等同于中国竞彩官方赔率。",
            "coverage_zh": "部分足球赛事的主流 bookmaker odds。",
            "status": _key_status("JC_EDGE_THE_ODDS_API_KEY"),
            "needs_account": True,
            "needs_api_key": True,
            "env_var": "JC_EDGE_THE_ODDS_API_KEY",
            "signup_url": "https://the-odds-api.com/",
            "docs_url": "https://the-odds-api.com/liveapi/guides/v4/",
            "setup_action_zh": "需要你注册免费 key；拿到 key 后配置到 JC_EDGE_THE_ODDS_API_KEY。",
            "default_behavior_zh": "默认不调用；配置 key 后可作为参考源。",
            "reliability_note_zh": "适合一天打开 1-2 次的低频参考，但免费额度按 credits 消耗。",
            "configured": secret_by_key.get("JC_EDGE_THE_ODDS_API_KEY", {}).get("configured", False),
            "masked_key": secret_by_key.get("JC_EDGE_THE_ODDS_API_KEY", {}).get("masked", "未配置"),
        },
        {
            "key": "api_football",
            "name": "API-Football / API-Sports",
            "cost_zh": "有免费额度",
            "role_zh": "赛程、球队、比分、部分赔率和阵容等参考信息。",
            "coverage_zh": "国际足球赛事覆盖较广，竞彩覆盖不保证。",
            "status": _key_status("JC_EDGE_API_FOOTBALL_KEY"),
            "needs_account": True,
            "needs_api_key": True,
            "env_var": "JC_EDGE_API_FOOTBALL_KEY",
            "signup_url": "https://www.api-football.com/",
            "docs_url": "https://www.api-football.com/documentation-v3",
            "setup_action_zh": "需要你注册免费 key；拿到 key 后配置到 JC_EDGE_API_FOOTBALL_KEY。",
            "default_behavior_zh": "默认不调用；配置 key 后可作为补充情报源。",
            "reliability_note_zh": "免费额度有限，适合低频刷新和赛前交叉校验。",
            "configured": secret_by_key.get("JC_EDGE_API_FOOTBALL_KEY", {}).get("configured", False),
            "masked_key": secret_by_key.get("JC_EDGE_API_FOOTBALL_KEY", {}).get("masked", "未配置"),
        },
        {
            "key": "thesportsdb",
            "name": "TheSportsDB",
            "cost_zh": "免费/可选高级",
            "role_zh": "球队、赛程、基础资料参考。",
            "coverage_zh": "足球资料与赛程；赔率能力较弱。",
            "status": "available_optional",
            "needs_account": False,
            "needs_api_key": False,
            "env_var": None,
            "signup_url": "https://www.thesportsdb.com/free_sports_api",
            "docs_url": "https://www.thesportsdb.com/documentation",
            "setup_action_zh": "无需注册即可先试免费 API；后续如需更高额度再升级。",
            "default_behavior_zh": "默认不调用；适合后续做球队资料补全。",
            "reliability_note_zh": "可免费使用，但不适合作为竞彩赔率主源。",
        },
        {
            "key": "open_meteo",
            "name": "Open-Meteo",
            "cost_zh": "免费，无需 key",
            "role_zh": "天气情报补充。",
            "coverage_zh": "全球天气预报与历史天气。",
            "status": "available_optional",
            "needs_account": False,
            "needs_api_key": False,
            "env_var": None,
            "signup_url": "https://open-meteo.com/",
            "docs_url": "https://open-meteo.com/en/docs",
            "setup_action_zh": "无需注册；后续需要先补球场/城市坐标。",
            "default_behavior_zh": "默认不调用；需要先有球场/城市坐标映射。",
            "reliability_note_zh": "适合补齐天气维度，但天气不应直接替代赔率和模型。",
        },
        {
            "key": "football_data_uk",
            "name": "football-data.co.uk",
            "cost_zh": "免费 CSV",
            "role_zh": "历史赛果与历史赔率回测。",
            "coverage_zh": "欧洲联赛历史结果、赔率、部分技术统计。",
            "status": "available_offline",
            "needs_account": False,
            "needs_api_key": False,
            "env_var": None,
            "signup_url": "https://www.football-data.co.uk/",
            "docs_url": "https://www.football-data.co.uk/data.php",
            "setup_action_zh": "无需注册；适合下载 CSV 后导入做历史回测。",
            "default_behavior_zh": "适合手动/定期导入 CSV 做回测，不作为实时竞彩源。",
            "reliability_note_zh": "历史研究价值高，但不能提供今日中国竞彩官方可售赔率。",
        },
    ]
    configured = sum(
        1
        for item in sources
        if item["status"] in {"enabled", "configured", "available_optional", "available_offline"}
    )
    return {
        "data_source_layer_version": "phase2p_free_source_status_v0",
        "summary_zh": "免费优先：Sporttery 做竞彩主源；免费第三方只做参考、天气或历史回测；账号型 API 默认关闭。",
        "daily_low_frequency_fit_zh": "一天打开 1-2 次时，免费额度通常够做参考刷新；但官方竞彩赔率仍以 Sporttery 公开数据为准。",
        "configured_or_available_count": configured,
        "sources": sources,
        "secret_config": secret_status,
        "recommended_order": [
            "Sporttery 官方公开数据",
            "Sporttery 会话缓存",
            "The Odds API / API-Football 低频交叉参考",
            "Open-Meteo 天气补充",
            "football-data.co.uk 历史回测",
            "mock 仅演示流程",
        ],
        "credential_policy_zh": "账号、手机号和 API key 由用户自己注册和保管；本地 App 只读取环境变量，不保存密码。",
        "next_registration_zh": "如果要先接一个免费 key，优先注册 The Odds API；如果还想补球队/阵容/赛程，再注册 API-Football。",
        "disclaimer": "所有数据仅用于本地概率分析、纸面模拟和风险诊断，不提供真实投注、下单、支付或代购能力。",
    }


def _key_status(env_var: str) -> str:
    load_local_env()
    return "configured" if os.getenv(env_var) else "not_configured"

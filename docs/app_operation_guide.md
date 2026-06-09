# JC Edge App Operation Guide

JC Edge 是 `football-jc-analysis` 的本地只读 App 名称，用于竞彩足球概率分析、概率回测、数据导入预检和风险解释。

## 如何使用

1. 启动 App：`python3 -m src.cli.launch_app`
2. 打开 `http://127.0.0.1:8766`
3. 在总览页先点“开始体验 mock 分析”
4. 在竞彩足球页查看 `mock / sporttery / auto` 数据源状态
5. 在数据导入页预检自己的历史 CSV
6. 在概率回测页查看命中率、ROI、最大回撤、Brier Score 和 Log Loss
7. 在候选信号页查看模型观察项、EV、Edge、风险等级和解释
8. 在组合风险页重点阅读“串关会显著放大风险”
9. 在 QA 页查看本地质量检查
10. 关闭服务时使用页面交付时提供的 `kill <api_pid> <dashboard_pid>`

## 安全边界

本工具只做本地概率分析与回测诊断，不提供投注、下单、支付、代购或自动化购彩能力。实际购彩请用户自行遵守当地法律法规并通过合法官方渠道独立判断。

概率模型不保证结果。回测结果不保证未来表现。串关会显著放大风险。

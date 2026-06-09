# Sporttery Usage Guide

JC Edge 可以尝试读取 Sporttery / 中国体育彩票竞彩足球公开数据，但本项目不代表官方合作，也不提供购彩平台入口。

## 数据源模式

- `mock`：本地示例数据，适合第一次体验。
- `sporttery`：只尝试 Sporttery 公开数据。
- `auto`：优先尝试 Sporttery；如果网络、证书或接口变更导致失败，会回退到 mock。

## 如何查看

1. 打开 App 的“竞彩足球”页。
2. 选择日期和 provider。
3. 点击“查看竞彩足球比赛”。
4. 查看 `provider_used`、比赛数量、赔率列和数据源提醒。

如果 Sporttery 失败，页面会显示中文说明：当前未能读取 Sporttery 数据，已回退到本地 mock 示例。

## 安全说明

本工具不提供投注、下单、支付、代购或自动化购彩能力。数据展示仅用于研究与娱乐参考。

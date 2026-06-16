# Phase 2-R 验收清单

Phase 2-R 包含五个目标：

- R1：串联命中率纪律引擎
- R2：今日观察页面进一步简化
- R3：DeepSeek Pro 解释层
- R4：CLV / 收盘赔率跟踪
- R5：用户 CSV 回测可信度增强

本清单用于本地验收，不涉及 push、remote、真实投注、下单、支付、代购或自动化购彩。

## R1：串联命中率纪律引擎

验收点：

- 风险档位包含 2串1 / 3串1 最低组合命中率门槛。
- 单腿可信度不足时，组合被拒。
- 高赔率冷门可作为单关观察，但默认不能作为串联核心。
- best parlay summary 显示 `hit_rate_pass` 和拒绝原因。
- App 显示“暂无优秀串联观察”时不是错误，而是纪律门控结果。

建议检查：

```bash
python3 -m src.cli.optimize_today --provider auto --date 2026-06-10 --bankroll 10000 --risk-profile aggressive --show-rejected --format json
```

应能看到：

- `min_parlay_2x1_prob`
- `min_parlay_3x1_prob`
- `min_leg_confidence`
- `hit_rate_discipline_zh`
- `longshot_warning`

## R2：今日观察页面进一步简化

验收点：

- 首页第一屏优先显示 Top 单关、Top 2串1、Top 总进球、Top 比分。
- 数据源、情报覆盖、可信度细节进入详情或其它页面。
- 今日观察区域不显示 `API Base` 等技术配置。
- 页面包含 `CLV / 收盘赔率复盘` 与 `CSV 回测可信度` 入口。

建议检查：

```text
打开 http://127.0.0.1:8766
```

或查看：

```text
reports/app_preview_phase2r.html
```

## R3：DeepSeek Pro 解释层

验收点：

- 默认关闭。
- 只读取 `/api/llm/status`，不会自动调用解释接口。
- key 可保存到本地 `.env.local`，不回显完整 key。
- 只做中文解释层，不参与概率、EV、候选筛选或组合决策。

建议检查：

```text
GET /api/llm/status
```

应能看到：

- `status: disabled`
- `external_calls_default: false`
- `safe_usage: optional_explainer_only`

本地配置变量：

```text
JC_EDGE_DEEPSEEK_ENABLED=false
JC_EDGE_DEEPSEEK_API_KEY=your-token
JC_EDGE_DEEPSEEK_MODEL=deepseek-chat
JC_EDGE_DEEPSEEK_MAX_INPUT_TOKENS=6000
JC_EDGE_DEEPSEEK_MAX_OUTPUT_TOKENS=800
```

## R4：CLV / 收盘赔率跟踪

验收点：

- 赛前优化结果包含 `clv_tracking`。
- App 赛前优化页显示 CLV 复盘状态。
- `/api/view/clv` 可查看赛前观察的 CLV 等待状态。
- `clv_review` CLI 可用本地收盘赔率 CSV 做赛后复盘。
- `/api/view/clv-review` 可只读复盘本地观察 JSON + 收盘赔率 CSV。

建议检查：

```bash
python3 -m src.cli.clv_review --observations-json data/fixtures/clv_observations_example.json --closing-odds data/fixtures/closing_odds_example.csv --format json
```

应能看到：

- `tracked_count: 2`
- `settled_count: 2`
- `positive_clv_count: 1`
- `negative_clv_count: 1`

## R5：用户 CSV 回测可信度增强

验收点：

- `backtest_credibility` 可按样本量、赔率覆盖、赛果覆盖、时间跨度和来源上限打分。
- fixture / mock 数据不能被评为高可信。
- 数据导入页显示 CSV 回测可信度。
- `/api/view/backtest` 附带 `backtest_credibility`。
- `/api/view/backtest-credibility` 可独立评估本地 CSV。

建议检查：

```bash
python3 -m src.cli.backtest_credibility --input data/fixtures/operation_walkforward_sample.csv --source-type fixture --format json
```

应能看到 fixture 来源被封顶在中等可信度附近。

## 安全边界

验收点：

- 不实现真实投注。
- 不实现下单、支付、代购。
- 不实现自动化购彩。
- 不输出稳赚、必中、保本、杀庄等承诺。
- DeepSeek 默认不调用。
- CLV 不联网抓收盘赔率，只读取用户提供的本地 CSV。
- 用户真实 CSV、真实 key、真实 external signals 不应提交。

## 最终建议验收顺序

1. `python3 -m compileall src tests`
2. 打开 `http://127.0.0.1:8766`
3. 查看今日观察、赛前优化、数据导入、数据可靠性
4. 运行 CLV 示例 CLI
5. 运行 CSV 可信度 CLI
6. 如环境有 pytest，再运行 `python3 -m pytest`
7. 视觉确认后再本地 commit

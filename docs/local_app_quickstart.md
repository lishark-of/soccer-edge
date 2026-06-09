# Local App Quickstart

1. 启动 App：

```bash
python3 -m src.cli.launch_app
```

2. 打开浏览器：

```text
http://127.0.0.1:8766
```

3. 看总览：确认 Version、Mode、Remote 和 DeepSeek 状态。

4. 跑一次 mock 分析：点击“先看 mock 分析”。

5. 跑一次概率回测：点击“再看概率回测”。

6. 看候选信号：进入“候选买点”页，查看模型概率、去水概率、Edge、EV 和风险等级。

7. 看风险解释：进入“组合风险”页，重点阅读串关风险说明。

8. 看原始 JSON：进入“原始 JSON”页，确认 API 响应细节。

9. 关闭服务：回到终端按 Ctrl-C。

## Reminder

本地 App 是 read-only。概率模型不保证结果。回测结果不保证未来表现。不提供投注、下单、支付、代购或任何自动化购彩能力。

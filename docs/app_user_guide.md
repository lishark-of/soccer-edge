# App User Guide

## 启动 App

```bash
python3 -m src.cli.launch_app
```

打开：

```text
http://127.0.0.1:8766
```

## 首页 6 步

1. 使用 mock 数据体验。
2. 导入历史 CSV。
3. 查看字段识别结果。
4. 运行概率回测。
5. 生成 calibration artifact。
6. 查看明日分析与候选风险解释。

## 导入页

导入页显示 input path、adapter、字段识别成功列表、缺失字段、修复建议、赔率覆盖率和行数。App 默认只做 dry-run，不写文件。

## 回测页

回测页显示样本量、有效比赛数、候选触发次数、命中率、ROI、PnL、最大回撤、Brier Score、Log Loss 和 Calibration 表。

## 分析页

分析页显示数据源、日期、provider_used、calibration_status、比赛数量、单关候选、2串1候选、3串1候选、EV、风险等级和本地解释。

## 校准页

校准页验证本地 calibration artifact 是否可读取。校准只是诊断辅助，不保证未来表现。

## QA 页

QA 页显示整体健康状态、warning 和 error。QA 通过不代表预测准确。

## 错误提示

新增用户流程会尽量使用中文说明，例如：未识别主队字段、比分无法解析、缺少赔率字段等。

## DeepSeek 状态

DeepSeek 默认关闭，只作为可选解释层，不参与概率计算或候选筛选。

## Safety

本工具只做本地概率分析与回测诊断，不提供投注、下单、支付、代购或自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

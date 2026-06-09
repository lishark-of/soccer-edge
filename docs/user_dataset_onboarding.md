# User Dataset Onboarding

## 1. 准备 CSV

你的历史 CSV 至少需要包含：比赛日期、赛事、主队、客队、比分。若要运行基于赔率的 EV 回测，还需要胜赔、平赔、负赔。

## 2. 必需字段

- date / 比赛日期
- league / 赛事 / 联赛
- home_team / 主队
- away_team / 客队
- score / 比分，或 home_goals + away_goals

## 3. 可选字段

- half_time_score / 半场比分
- odds_home / 胜赔
- odds_draw / 平赔
- odds_away / 负赔
- handicap / 让球
- hhad_win / 让胜
- hhad_draw / 让平
- hhad_lose / 让负

## 4. 中文列名支持

系统会自动识别常见中文列名，例如 `比赛日期`、`赛事`、`主队`、`客队`、`比分`、`胜赔`、`平赔`、`负赔`。

## 5. mapping JSON

如果你的列名比较特殊，可以提供 mapping JSON：

```json
{
  "date": "比赛日期",
  "league": "赛事",
  "home_team": "主队",
  "away_team": "客队",
  "score": "比分",
  "odds_home": "胜赔",
  "odds_draw": "平赔",
  "odds_away": "负赔"
}
```

## 6. Dry-run

```bash
python3 -m src.cli.import_history --input data/fixtures/user_onboarding_sample.csv --dry-run --format json
```

或者使用完整用户流程：

```bash
python3 -m src.cli.user_data_workflow --input data/fixtures/user_onboarding_sample.csv --mapping data/fixtures/user_onboarding_mapping_example.json --format json
```

## 7. normalized CSV

完整 workflow 会把标准化数据写入 `data/normalized/user_workflow/`，该目录已被 Git 忽略。

## 8. 回测

workflow 会基于 normalized CSV 运行概率回测。回测结果只用于诊断，不保证未来表现。

## 9. calibration artifact

workflow 会生成 calibration artifact 到 `artifacts/calibration/`，该目录已被 Git 忽略。

## 10. 明日分析

workflow 会用 calibration artifact 跑一次 mock provider 明日分析，帮助你确认完整流程可用。

## 11. 常见错误

- 文件不存在：检查 CSV 路径。
- 未识别主队字段：增加 `主队` 列，或在 mapping JSON 中设置 `home_team`。
- 未识别比分字段：增加 `比分` 列，例如 `2-1`。
- 缺少赔率字段：可以导入赛果，但 EV 回测可能不足。

## 12. Safety

不要提交真实数据。不要把 API Key 写入 Git。  
不提供投注、下单、支付、代购或任何自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

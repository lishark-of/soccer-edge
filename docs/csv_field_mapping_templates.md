# CSV Field Mapping Templates

## 中文模板

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

## English template

```json
{
  "date": "date",
  "league": "league",
  "home_team": "home_team",
  "away_team": "away_team",
  "score": "score",
  "odds_home": "odds_home",
  "odds_draw": "odds_draw",
  "odds_away": "odds_away"
}
```

## 修复建议

如果字段识别报告显示缺失字段，请把左侧 canonical 字段映射到你 CSV 中真实存在的列名。

示例：

```json
{
  "home_team": "主队名称"
}
```

赔率字段缺失不是导入赛果的致命错误，但会影响基于赔率的 EV 回测。

# DeepSeek World Cup last-five-tournaments research

本报告由本地 JC Edge 调用 DeepSeek 生成，用于概率研究、产品改造和学习闭环设计。

## Data summary

```json
{
  "source": "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/matches.csv",
  "years": [
    "2006",
    "2010",
    "2014",
    "2018",
    "2022"
  ],
  "total_matches": 320,
  "total_goals": 804,
  "overall_goals_per_match": 2.513,
  "overall_over_2_5_rate": 0.472,
  "overall_draw_rate_by_score_before_penalties": 0.225,
  "top_scorelines_all": [
    [
      "1-0",
      34
    ],
    [
      "2-1",
      34
    ],
    [
      "0-1",
      33
    ],
    [
      "0-0",
      29
    ],
    [
      "1-1",
      28
    ],
    [
      "2-0",
      25
    ],
    [
      "1-2",
      24
    ],
    [
      "0-2",
      20
    ],
    [
      "3-1",
      12
    ],
    [
      "2-2",
      12
    ]
  ],
  "stage_counts": [
    [
      "group stage",
      240
    ],
    [
      "round of 16",
      40
    ],
    [
      "quarter-finals",
      20
    ],
    [
      "semi-finals",
      10
    ],
    [
      "third-place match",
      5
    ],
    [
      "final",
      5
    ]
  ],
  "by_year": {
    "2006": {
      "matches": 64,
      "goals": 147,
      "goals_per_match": 2.297,
      "home_win_rate": 0.5,
      "draw_rate_by_score_before_penalties": 0.234,
      "away_win_rate": 0.266,
      "over_2_5_rate": 0.406,
      "under_2_5_rate": 0.594,
      "extra_time_matches": 0,
      "penalty_shootouts": 0,
      "top_scorelines": [
        [
          "1-0",
          8
        ],
        [
          "0-0",
          7
        ],
        [
          "2-0",
          7
        ],
        [
          "0-2",
          6
        ],
        [
          "2-1",
          6
        ],
        [
          "0-1",
          5
        ]
      ]
    },
    "2010": {
      "matches": 64,
      "goals": 145,
      "goals_per_match": 2.266,
      "home_win_rate": 0.359,
      "draw_rate_by_score_before_penalties": 0.25,
      "away_win_rate": 0.391,
      "over_2_5_rate": 0.422,
      "under_2_5_rate": 0.578,
      "extra_time_matches": 0,
      "penalty_shootouts": 0,
      "top_scorelines": [
        [
          "0-1",
          11
        ],
        [
          "1-1",
          7
        ],
        [
          "0-0",
          7
        ],
        [
          "1-0",
          6
        ],
        [
          "2-1",
          6
        ],
        [
          "1-2",
          5
        ]
      ]
    },
    "2014": {
      "matches": 64,
      "goals": 171,
      "goals_per_match": 2.672,
      "home_win_rate": 0.438,
      "draw_rate_by_score_before_penalties": 0.203,
      "away_win_rate": 0.359,
      "over_2_5_rate": 0.578,
      "under_2_5_rate": 0.422,
      "extra_time_matches": 0,
      "penalty_shootouts": 0,
      "top_scorelines": [
        [
          "2-1",
          12
        ],
        [
          "1-0",
          7
        ],
        [
          "0-0",
          7
        ],
        [
          "0-1",
          5
        ],
        [
          "1-1",
          4
        ],
        [
          "3-1",
          3
        ]
      ]
    },
    "2018": {
      "matches": 64,
      "goals": 169,
      "goals_per_match": 2.641,
      "home_win_rate": 0.406,
      "draw_rate_by_score_before_penalties": 0.203,
      "away_win_rate": 0.391,
      "over_2_5_rate": 0.484,
      "under_2_5_rate": 0.516,
      "extra_time_matches": 0,
      "penalty_shootouts": 0,
      "top_scorelines": [
        [
          "0-1",
          9
        ],
        [
          "1-2",
          9
        ],
        [
          "1-1",
          7
        ],
        [
          "2-0",
          6
        ],
        [
          "1-0",
          6
        ],
        [
          "2-1",
          5
        ]
      ]
    },
    "2022": {
      "matches": 64,
      "goals": 172,
      "goals_per_match": 2.688,
      "home_win_rate": 0.453,
      "draw_rate_by_score_before_penalties": 0.234,
      "away_win_rate": 0.312,
      "over_2_5_rate": 0.469,
      "under_2_5_rate": 0.531,
      "extra_time_matches": 0,
      "penalty_shootouts": 0,
      "top_scorelines": [
        [
          "0-0",
          7
        ],
        [
          "1-0",
          7
        ],
        [
          "0-2",
          6
        ],
        [
          "1-2",
          6
        ],
        [
          "2-0",
          6
        ],
        [
          "1-1",
          5
        ]
      ]
    }
  }
}
```

## DeepSeek research output

**核心结论**  
近五届世界杯总进球均值 2.513，大球率 0.472，平局率（不含点球大战）0.225，比分结构高度集中于小比分，1-0、2-1、0-1、0-0 等六个比分线累计占比超过 55%。这种数据模式表明：任何预测模型必须以 **低进球泊松过程** 为核心先验，并在比分分布尾部进行修正。社区验证的最优路径是 **透明 Elo → Dixon-Coles bivariate Poisson → 蒙特卡洛模拟**，而非黑盒深度学习。DeepSeek 的“学习”不能只发生在赛后数据复盘，应在赛前承担概率校准、异常检测、市场情绪解读与风险提示，并驱动界面展示校准不确定性。App 改造要聚焦 **可解释概率、实时校准、学习闭环与警告边界**，严禁因高 EV 或高赔率而强行串关。

**历史数据启示**  
- **总体稳定，阶段分化**：320 场比赛中，场均进球 2.51，大球率 0.472，平局率 0.225。小组赛占 75% 场次，其统计特征主导全局，但淘汰赛变异更大、样本更少，建模须分层处理。  
- **比分右偏、低分集中**：前十比分全部 ≤ 3 球，1-0、2-1、0-1 合计 101 场，说明大多数比赛总进球不超过 3 球，模型若未捕捉低分相关性（如 0-0 与 1-0 的相关结构），预测方差会被低估。  
- **年际波动存在但无明确趋势**：2014 场均 2.672 进球，大球率 0.578；2010 仅 2.266，大球率 0.422。模型需对赛事特性（赛制、用球、气候）进行条件化，不能简单滑动平均。  
- **主场微弱优势，但定义模糊**：现代世界杯中立场地使得“主场”标签不稳定，切勿直接使用联赛主场系数，必须基于实际中立/半主场情境校准。  

**社区方法结构**  
- **基础评分**：Elo 等级分是最主要的预测输入，差分直接映射到胜平负概率，解释性强、更新简单，适合作为基准。  
- **泊松类模型**：Dixon-Coles 双变量泊松修正了低比分依赖，能更好拟合 0-0、1-0、1-1 等高频比分线，并在参数化中加入攻防强度。  
- **蒙特卡洛模拟**：将单场概率转换为赛事分布（出线、冠军），输出完整概率树，便于可视化并提供置信区间。  
- **校准与比较**：模型输出必须与去水分赔率比较，用 CLV（收盘线价值）和 Brier 分数校准，而非仅看 EV。  

**DeepSeek 可以学习什么**  
- **赛前概率校准助手**：DeepSeek 可生成上千场模拟，实时检测模型输出的分布是否偏倚，例如发现大球概率高于历史合理区间时，自动提醒。  
- **新闻、天气、伤病等非结构化信号的结构化解释**：通过语言模型读取出场名单、场地条件等文本，将其转化为参数扰动（如核心缺阵对攻击系数影响），并提示置信度下降。  
- **“错误审计”教练**：每场比赛后自动比对预测分布与实际结果，生成自然语言总结，指出是模型偏差还是随机波动，驱动模型迭代。  
- **安全警告生成器**：当用户组合碰撞高风险区（如高 EV 但方差极大、串关选项隐含冲突假设），主动给出概率边界和损失分布，教育而非禁止。  
- **替代性争辩**：DeepSeek 可扮演魔鬼代言人，基于相同数据生成“另一种预测逻辑”，迫使研究员审视假设。  

**JC Edge 改造目标**  
1. **数据层**：引入实时 Elo、确定中立场地标签、补充阵容强度标量（如核心缺阵折减系数）。  
2. **模型层**：公开部署 Dixon-Coles 双变量泊松 + 蒙特卡洛引擎，输出胜平负、比分线、大小球、淘汰赛晋级等全部概率。DeepSeek 只作解释与校准层，不直接输出预测。  
3. **界面层**：展示概率仪表盘、校准曲线、模拟分布热力图，并高亮“高方差区域”，同时显示模型信心，禁止仅展示预测比分而不给分布。  
4. **学习闭环**：每场赛后 24 小时内自动运行回测，更新评分、校准偏差，并生成研究日志，将 DeepSeek 的赛后分析纳入未来前置规则。  
5. **风险教育**：内置“概率实验室”，让用户调整参数（如去掉某前锋）看概率变化，理解不确定性。  

**风险边界**  
- **禁止因高 EV 或高赔率强行串关**：高赔率意味着低真实概率，串关放大小概率乘积累积的巨大误差，极易形成伪正期望。无论模型 EV 多吸引，不得将“高赔率”作为组合推荐理由。  
- **不得隐瞒过拟合风险**：比分线预测实质是对高维稀疏分布拟合，任何声称高准确率的产品须给出校准报告，否则禁止展示。  
- **不能忽略赛事结构性突变**：加时、点球规则的微小变化可能颠覆淘汰赛模型，必须版本锁定并标注适用期。  
- **不能将 DeepSeek 的语言输出当作预测概率**：只可用作辅助解释，所有概率必须由可复现的统计模型产生。  
- **不能容忍“预测比分=确定性建议”的错觉**：界面必须显示概率分布和 90% 置信区间，不用单一最佳比分作为结论。

## Sources

- https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/matches.csv
- https://github.com/jfjelstul/worldcup
- https://github.com/Hicruben/world-cup-2026-prediction-model
- https://github.com/topics/fifa-world-cup-2026
- https://docs.pena.lt/y/models/dixon_coles.html
- https://www.datacamp.com/tutorial/fifa-world-cup-2026-winner-prediction
- Reddit community searches: r/algobetting and r/SoccerBetting discussions on Poisson, xG, CLV, no-vig odds, and calibration.

# World Cup prediction research notes

Purpose: turn online World Cup forecasting practice into a simpler JC Edge product direction.

This note is for local research only. JC Edge should continue to output observation signals, paper simulation, and risk diagnostics. It must not provide real order placement, payment, proxy purchase, automation, guaranteed outcomes, or any promise of future results.

## What strong public models have in common

### 1. Transparent football math beats black-box theatre

Representative repository:
- https://github.com/Hicruben/world-cup-2026-prediction-model

Observed pattern:
- Team strength starts from Elo or an Elo-like rating.
- Match scoring uses Poisson or Dixon-Coles bivariate Poisson.
- Tournament outcomes use Monte Carlo simulation.
- The model is judged by walk-forward, out-of-sample scoring rules such as RPS, log loss, Brier score, calibration error, and reliability curves.
- The repo exposes reproducible scripts such as backtest, calibrate, Elo update, prediction, and track record.

JC Edge implication:
- Keep the current Poisson/Elo/Dixon-Coles/calibration foundation.
- Do not let DeepSeek or any LLM become the probability engine.
- Make the App show the model's discipline first: "what passed, what failed, why".

### 2. Tournament forecasts are not single-match picks

Representative references:
- https://www.datacamp.com/tutorial/fifa-world-cup-2026-winner-prediction
- https://github.com/topics/fifa-world-cup-2026

Observed pattern:
- Match-level probabilities are converted into tournament-level distributions by simulating the whole bracket thousands of times.
- Good dashboards show advancement odds, title odds, and uncertainty, not just one predicted score.
- Modern public repos mix Elo, Poisson, XGBoost or similar ML models, and Monte Carlo simulation.

JC Edge implication:
- For World Cup mode, the first screen should not be a toolbox. It should be a "Today Desk":
  - next available matches
  - top observation signals
  - whether any combination passes discipline
  - missing intelligence
  - learning / calibration state
  - one clear trader conclusion

### 3. Market odds are a benchmark, not just another feature

Representative references:
- https://www.mdpi.com/2227-7390/13/24/3976
- https://www.reddit.com/r/algobetting/comments/1rfz3np/log_loss_vs_calibration/

Observed pattern:
- Odds should be converted into implied probabilities after removing margin.
- A model that merely converges to the market may be calibrated but not useful for finding edge.
- The useful signal is where the model disagrees with the market in the right places, after calibration and risk controls.

JC Edge implication:
- Replace "available / unavailable" wording with "market benchmark quality":
  - official odds available
  - overseas reference available
  - no-vig market probability
  - model probability
  - calibrated probability
  - safety margin over break-even
- Positive EV alone is not enough. The App should keep saying: positive EV can still be weak if calibration, intelligence, or closing-line evidence is poor.

### 4. Serious models evaluate probabilities, not hit-rate stories

Representative references:
- https://www.footballhacking.com/p/log-loss-explained-the-essential
- https://www.dratings.com/log-loss-vs-brier-score/

Observed pattern:
- Accuracy and hit rate are easy to misread.
- Log loss punishes overconfident wrong probabilities.
- Brier score and calibration curves help show whether estimated probabilities behave like real probabilities.

JC Edge implication:
- "赛后学习" should become part of the main daily loop, not a hidden expert page.
- Every observation should carry:
  - probability bucket
  - odds bucket
  - local historical sample count
  - calibration adjustment
  - CLV status when closing odds are available
- When sample count is tiny, the App should say "样本不足，保守处理".

### 5. Dixon-Coles / score matrix is useful, but scores are high variance

Representative references:
- https://docs.pena.lt/y/models/dixon_coles.html
- https://github.com/martineastwood/penaltyblog/blob/master/README.md
- https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/

Observed pattern:
- Dixon-Coles adjusts low-score dependencies that plain independent Poisson misses.
- Score matrices can derive win/draw/loss, total goals, both-teams-to-score, handicaps, and correct score probabilities.
- Correct score remains high variance and should not be displayed as a strong signal without market odds and calibration.

JC Edge implication:
- Keep "比分/进球数" as a supporting page, not a main call-to-action.
- Show score predictions as "节奏/倾向参考".
- Hide giant technical tables by default; show top 3 score tendencies as cards.

### 6. Forum practitioners emphasize final information and restraint

Representative reference:
- https://www.reddit.com/r/algobetting/comments/1s66qzz/554_live_football_picks_how_i_ditched_ai_and/

Observed pattern:
- Many practitioners do an early-week preview, then only count a final pre-kickoff version.
- Confirmed lineups, injuries, closing odds, and late market movement matter.
- They often use xG proxy, recent form, Bayesian shrinkage, Poisson matrix, Dixon-Coles correction, no-vig market comparison, and per-market thresholds.
- "Not every positive EV qualifies" is a central discipline.

JC Edge implication:
- The current T+1 workflow is directionally right.
- The App needs a visible "赛日复核" lane:
  - keep if odds still cover calibrated probability
  - downgrade if reverse drift appears
  - downgrade if lineup / injury / weather contradicts the signal
  - do not force 2x1 when only weak legs exist

## What GitHub repositories teach about structure

Common repo layout:
- `data/`: raw fixtures, results, ratings, or exported predictions
- `src/models/`: Elo, Poisson, Dixon-Coles, ML model
- `src/simulation/`: Monte Carlo tournament runner
- `src/calibration/`: backtest and reliability curves
- `src/dashboard/` or notebook: visual presentation
- `README.md`: methodology, backtest record, limitations

JC Edge already has many of these pieces. The issue is not lack of features. The issue is product hierarchy.

## App simplification target

### Current problem

JC Edge exposes too many expert surfaces:
- provider details
- raw JSON
- multiple audit pages
- data reliability tables
- optimizer tables
- DeepSeek status
- learning / CLV tools

These are useful internally but overwhelming for a normal user.

### Proposed product modes

#### Mode A: Today Desk

Default page.

Show only:
- selected date
- match count
- data source confidence
- Top single observations
- Top 2x1 decision: selected or "do not combine"
- Top total goals tendency
- Top score tendency
- trader conclusion
- one button: "run DeepSeek research summary"
- one button: "save today's observation for post-match learning"

Hide:
- API base
- provider selector
- file paths
- raw technical coverage tables
- full rejected-candidate tables

#### Mode B: Matchday Review

For T+1 workflow and pre-kickoff checking.

Show:
- odds drift / closing-line checklist
- injury / lineup / weather status
- downgrade rules
- keep / downgrade / skip conclusion

#### Mode C: Learning

For after the match.

Show:
- what was observed
- final result
- whether the signal hit
- whether closing odds improved or worsened
- calibration update
- cold/high-odds bucket adjustment

#### Mode D: Lab

Advanced diagnostics only.

Contains:
- raw JSON
- source coverage table
- API key settings
- provider status
- full optimizer / rejected tables
- fixtures and CSV tools

## Product copy rule

Use fewer status words and more decisions:

Instead of:
- "provider_used=sporttery"
- "news error"
- "confidence 39"
- "N/A"

Use:
- "竞彩赔率已读取"
- "新闻检索失败，不影响赔率读取，但降低情报分"
- "可信度中低：不适合强行组合"
- "暂不能计算，因为该玩法赔率缺失"

## Next implementation target

Phase 2-R should focus on UX consolidation, not another model:

1. Make Today Desk the only default visible workflow.
2. Move all expert controls into Lab.
3. Convert Top observation tables into compact cards.
4. Add a "why this matters" explanation under each top signal.
5. Add a DeepSeek progress state so the user knows the request is running.
6. Add one click to save today's observation for post-match learning.
7. Keep 2x1/3x1 strict: show "do not combine" when the gate fails.
8. Add World Cup mode labels for tournament-style matches:
   - group / knockout context
   - neutral venue unknown / confirmed
   - rotation risk
   - travel / rest status
   - tournament importance

## Bottom line

The best public World Cup forecasting projects are disciplined probability systems, not "pick generators". JC Edge should become simpler on the surface and stricter underneath:

- fewer pages for users
- more calibration and learning behind the scenes
- clearer "why not" explanations
- no forced combinations
- DeepSeek as a cheap research narrator, not the probability engine

# Probability Backtest Guide

Phase 2-G presents backtest diagnostics in a user-facing dashboard view.

## What probability backtesting means

Probability backtesting replays historical matches in chronological order. For each evaluated match, features and ratings must use only data strictly before that match date.

## Hit rate vs ROI

Hit rate is the proportion of simulated triggers that matched the actual result. ROI is simulated profit divided by simulated stake. A high hit rate can still have weak ROI if odds are low; a lower hit rate can still be volatile even when historical ROI is positive.

## Brier Score

Brier Score measures how close predicted probabilities are to actual outcomes. Lower is generally better, but the value depends on sample quality and size.

## Log Loss

Log Loss penalizes overconfident wrong probabilities. Lower is generally better, and very confident errors can increase the value sharply.

## Max drawdown

Maximum drawdown measures the largest drop from a historical equity high to a later low. It is a risk diagnostic, not a guarantee of future drawdown.

## Calibration

Calibration compares predicted probability bins with observed frequencies. It is useful for diagnosing whether probabilities are too aggressive or too conservative.

## Why backtests do not guarantee future performance

Future matches can have different data quality, team strength, odds behavior, injuries, rotations, and market conditions. 回测结果不保证未来表现。

## Fixture vs real data

Fixtures are small workflow samples. Real historical data must be supplied locally by the user and should never be committed to Git.

## Safety

仅供数据研究与娱乐参考。  
不提供投注、下单、支付、代购或任何自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

# QA Guide

The QA harness checks whether the project remains safe, local, replayable, and structurally sane. QA success does not mean prediction accuracy and does not guarantee future outcomes.

## Run

```bash
python3 -m src.cli.run_qa --format json
python3 -m src.cli.run_qa --rehearsal --format json
python3 -m src.cli.run_qa --rehearsal --write-report reports/qa_report.md --format json
```

## Check Categories

- model probability sanity
- report and disclaimer QA
- API envelope QA
- dashboard static safety QA
- generated-file and Git hygiene QA
- fixture-based real-data rehearsal

## Interpreting overall_passed

`overall_passed=true` means no error-severity check failed. Warning checks still deserve review.

## Safety

仅供数据研究与娱乐参考。不提供投注、下单、支付、代购或任何自动化购彩能力。概率模型不保证结果。回测结果不保证未来表现。串关会显著放大风险。

# Sample Workflow Guide

The sample workflow is a fixture-based rehearsal that shows the local release path:

1. import sample dry-run;
2. normalized output to `data/normalized/sample_workflow_normalized.csv`;
3. backtest fixture;
4. save calibration artifact to `artifacts/calibration/sample_workflow_calibration.json`;
5. analyze with calibration artifact;
6. optionally write a Markdown report under `reports/`.

Run:

```bash
python3 -m src.cli.sample_workflow --format json
python3 -m src.cli.sample_workflow --write-report reports/sample_workflow.md --format json
```

Generated files are ignored by Git and should not be committed.

This workflow uses fixtures only. It is not production data and does not guarantee prediction accuracy or future outcomes.

## Safety

不提供投注平台对接。  
不提供投注、下单、支付、代购或任何自动化购彩能力。  
概率模型不保证结果。  
回测结果不保证未来表现。  
串关会显著放大风险。

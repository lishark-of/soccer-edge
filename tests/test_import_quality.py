from src.backtesting.historical_loader import load_historical_matches
from src.ingestion.quality import build_quality_report


def test_quality_report_odds_coverage():
    matches = load_historical_matches("data/fixtures/import_sample_generic.csv")
    report = build_quality_report(matches)
    assert report["odds_coverage"]["had"] == 1.0
    assert report["matches"] >= 10

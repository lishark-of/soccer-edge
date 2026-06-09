from src.qa.rehearsal import run_sample_import_rehearsal


def test_rehearsal_returns_overall_status():
    payload = run_sample_import_rehearsal(".", "data/fixtures/rehearsal_real_like_generic.csv")
    assert payload["rows_normalized"] >= 20
    assert payload["rows_skipped"] >= 1

from pathlib import Path

from src.backtesting.historical_loader import load_historical_matches, load_historical_matches_with_warnings, normalize_historical_row


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "fixtures" / "historical_matches_sample.csv"


def test_historical_loader_normalizes_rows():
    row = {
        "date": "2026/05/01",
        "league": "Mock League",
        "home_team": "Alpha FC",
        "away_team": "Beta United",
        "score": "2:1",
    }
    match = normalize_historical_row(row)

    assert match.date == "2026-05-01"
    assert match.home_goals == 2
    assert match.away_goals == 1
    assert match.result_1x2 == "H"


def test_historical_loader_skips_bad_rows(tmp_path):
    path = tmp_path / "bad_rows.csv"
    path.write_text(
        "date,league,home_team,away_team,home_goals,away_goals\n"
        "2026-05-01,Mock,A,B,2,1\n"
        "bad-date,Mock,A,B,1,0\n",
        encoding="utf-8",
    )

    matches, warnings = load_historical_matches_with_warnings(str(path))

    assert len(matches) == 1
    assert warnings


def test_fixture_loader_reads_sample_csv():
    matches = load_historical_matches(str(FIXTURE_PATH))

    assert len(matches) >= 20

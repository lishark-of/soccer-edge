import json

from src.cli.clv_review import main


def test_clv_review_cli_json_shape(tmp_path, capsys):
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps(
            {
                "selected_portfolio": {
                    "singles": [
                        {
                            "match_id": "m1",
                            "play_type": "had",
                            "outcome_key": "win",
                            "odds": 2.2,
                            "home_team": "A",
                            "away_team": "B",
                        }
                    ]
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    closing = tmp_path / "closing.csv"
    closing.write_text("key,closing_odds\nm1|had|win,2.0\n", encoding="utf-8")
    import sys

    old_argv = sys.argv
    sys.argv = ["clv_review", "--observations-json", str(observations), "--closing-odds", str(closing), "--format", "json"]
    try:
        assert main() == 0
    finally:
        sys.argv = old_argv
    payload = json.loads(capsys.readouterr().out)
    assert payload["settled_count"] == 1
    assert payload["positive_clv_count"] == 1

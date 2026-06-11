from src.intelligence.feature_context import build_match_context
from src.intelligence.fusion import build_intelligence_preview, build_observations_from_context, fused_probability
from src.domain.match import Match
from src.view_models.intelligence_view import build_intelligence_view


def _match():
    return Match(match_id="m1", match_no="001", date="2026-06-10", league="测试", kickoff_at="2026-06-10T20:00:00+08:00", home_team="主队", away_team="客队", had_odds={"win": 2.0, "draw": 3.2, "lose": 3.6}, hhad_odds={"handicap": -1.0, "win": 4.0, "draw": 3.6, "lose": 1.8})


def test_fused_probability_normalized():
    context = build_match_context(_match())
    fused = fused_probability(context)
    assert abs(sum(fused["had"].values()) - 1.0) < 1e-6
    assert "top_scores" in fused


def test_observations_include_reasons():
    context = build_match_context(_match())
    observations, candidates = build_observations_from_context(context)
    assert observations
    assert candidates
    assert all("selection_reason" in row for row in observations)


def test_intelligence_view_marks_missing_signals_not_connected_unknown():
    context = build_match_context(_match())
    view = build_intelligence_view({"contexts": [context], "missing_signals": context["missing_signals"], "optimizer": {"selected_portfolio": {}}})
    rows = {row["key"]: row for row in view["signal_status"]}
    assert rows["news"]["status"] == "未接入"
    assert rows["news"]["impact"] == "未知"
    assert rows["injuries"]["status"] == "未接入"
    assert rows["weather"]["message_zh"] == "未接入可靠数据，模型不会编造该情报。"
    assert rows["schedule"]["status"] == "已检查但未返回"
    assert rows["schedule"]["impact"] == "未知"
    assert rows["travel"]["status"] == "未接入"
    assert rows["travel"]["impact"] == "未知"
    actions = {row["json_key"]: row for row in view["intelligence_gap_actions"]}
    assert actions["news"]["confidence_impact"].startswith("降低信心")
    assert "不会编造" in actions["news"]["confidence_impact"]
    assert "external_signals JSON" in actions["injuries"]["next_action_zh"]
    assert actions["travel"]["status"] == "未接入"
    assert actions["schedule"]["status"] == "已检查但未返回"


def test_intelligence_preview_connects_external_signal_fixture():
    preview = build_intelligence_preview("mock", "2026-06-10", "data/fixtures/external_signals_mock_20260610.json")
    view = build_intelligence_view(preview)
    rows = {row["key"]: row for row in view["signal_status"]}
    assert view["external_signals_status"]["source_type"] == "user_json"
    assert view["external_signals_status"]["load_status"] == "loaded"
    assert view["external_signals_status"]["invalid_items"] == 0
    assert view["external_signals_status"]["matched_count"] == 1
    assert view["external_signals_status"]["matches_count"] == 5
    assert rows["news"]["status"] == "已确认"
    assert rows["news"]["source_zh"] == "用户 JSON"
    assert rows["injuries"]["status"] == "已确认"
    assert rows["lineup"]["status"] == "已确认"
    assert rows["weather"]["status"] == "已确认"
    assert rows["motivation"]["status"] == "已确认"
    assert rows["travel"]["status"] == "未接入"
    actions = {row["json_key"]: row for row in view["intelligence_gap_actions"]}
    assert actions["news"]["confidence_impact"] == "已有覆盖记录，仅用于解释信心，不直接替代概率模型。"
    assert actions["travel"]["confidence_impact"].startswith("降低信心")


def test_intelligence_preview_reports_bad_external_signal_json(tmp_path):
    bad = tmp_path / "bad_signals.json"
    bad.write_text("{bad json", encoding="utf-8")
    preview = build_intelligence_preview("mock", "2026-06-10", str(bad))
    view = build_intelligence_view(preview)
    rows = {row["key"]: row for row in view["signal_status"]}
    assert view["external_signals_status"]["source_type"] == "user_json"
    assert view["external_signals_status"]["load_status"] == "parse_error"
    assert view["external_signals_status"]["signals_loaded"] == 0
    assert rows["news"]["status"] == "未接入"
    assert rows["news"]["impact"] == "未知"

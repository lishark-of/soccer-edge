from src.audit.credibility import build_credibility_gate


def test_credibility_under_50_closes_combo_gate():
    gate = build_credibility_gate({"credibility_score": 39, "grade": "D", "missing_information": ["伤停"]})
    assert gate["combo_gate"] == "closed"
    assert gate["allow_parlay"] is False


def test_credibility_50_to_64_restricts_combo_gate():
    gate = build_credibility_gate({"credibility_score": 55, "grade": "C", "missing_information": []})
    assert gate["combo_gate"] == "restricted"
    assert gate["allow_parlay"] == "only_low_risk_2x1"

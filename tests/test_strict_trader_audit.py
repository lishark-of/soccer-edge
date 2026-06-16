from src.cli.strict_trader_audit import run_strict_trader_audit


def test_strict_trader_audit_json_shape():
    report = run_strict_trader_audit(".")
    assert report["audit_version"] == "phase2o_strict_trader_audit_v0"
    assert "summary" in report
    assert "endpoint_summary" in report
    assert "acceptance_summary" in report
    assert "acceptance_criteria" in report
    assert "phase3_summary" in report
    assert "phase3_readiness" in report
    assert "goal_summary" in report
    assert "goal_readiness" in report


def test_strict_trader_audit_static_checks_pass():
    report = run_strict_trader_audit(".")
    failed_static = [c for c in report["checks"] if c["name"].startswith("audit.home") and not c["passed"]]
    assert failed_static == []


def test_strict_trader_audit_acceptance_criteria_present():
    report = run_strict_trader_audit(".")
    names = {c["name"] for c in report["acceptance_criteria"]}
    assert len(names) >= 17
    assert "acceptance.01_today_observation_default" in names
    assert "acceptance.04_no_transaction_controls" in names
    assert "acceptance.08_rejected_combos_have_reasons" in names
    assert "acceptance.09_operation_profit_explained" in names
    assert "acceptance.10_model_outputs_are_not_guarantees" in names
    assert "acceptance.12_ai_telemetry_unified" in names
    assert "acceptance.13_learning_metrics_returned" in names
    assert "acceptance.14_combo_gate_explicit" in names
    assert "acceptance.15_learning_digests_present" in names
    assert "acceptance.16_llm_guidance_present" in names
    assert "acceptance.17_learning_reports_present" in names


def test_strict_trader_audit_acceptance7_requires_visible_context_columns():
    report = run_strict_trader_audit(".")
    checks = {item["name"]: item for item in report["acceptance_criteria"]}
    assert checks["acceptance.07_observations_have_discipline_context"]["passed"] is True
    assert "展示入选原因、反对因素和缺失情报" in checks["acceptance.07_observations_have_discipline_context"]["message"]


def test_strict_trader_audit_acceptance8_requires_home_rejected_combo_reasons():
    report = run_strict_trader_audit(".")
    checks = {item["name"]: item for item in report["acceptance_criteria"]}
    assert checks["acceptance.08_rejected_combos_have_reasons"]["passed"] is True
    assert "今日观察首页展示" in checks["acceptance.08_rejected_combos_have_reasons"]["message"]


def test_strict_trader_audit_acceptance12_requires_ai_telemetry_fields():
    report = run_strict_trader_audit(".")
    checks = {item["name"]: item for item in report["acceptance_criteria"]}
    assert checks["acceptance.12_ai_telemetry_unified"]["passed"] is True
    assert "telemetry" in checks["acceptance.12_ai_telemetry_unified"]["message"]


def test_strict_trader_audit_acceptance13_requires_learning_metrics():
    report = run_strict_trader_audit(".")
    checks = {item["name"]: item for item in report["acceptance_criteria"]}
    assert checks["acceptance.13_learning_metrics_returned"]["passed"] is True
    assert "今日和区间指标" in checks["acceptance.13_learning_metrics_returned"]["message"]


def test_strict_trader_audit_acceptance14_requires_combo_gate_fields():
    report = run_strict_trader_audit(".")
    checks = {item["name"]: item for item in report["acceptance_criteria"]}
    assert checks["acceptance.14_combo_gate_explicit"]["passed"] is True
    assert "combo_gate" in checks["acceptance.14_combo_gate_explicit"]["message"]


def test_strict_trader_audit_acceptance15_requires_learning_digests():
    report = run_strict_trader_audit(".")
    checks = {item["name"]: item for item in report["acceptance_criteria"]}
    assert checks["acceptance.15_learning_digests_present"]["passed"] is True
    assert "复盘摘要" in checks["acceptance.15_learning_digests_present"]["message"]


def test_strict_trader_audit_acceptance16_requires_llm_guidance():
    report = run_strict_trader_audit(".")
    checks = {item["name"]: item for item in report["acceptance_criteria"]}
    assert checks["acceptance.16_llm_guidance_present"]["passed"] is True
    assert "配置状态" in checks["acceptance.16_llm_guidance_present"]["message"]


def test_strict_trader_audit_acceptance17_requires_learning_reports():
    report = run_strict_trader_audit(".")
    checks = {item["name"]: item for item in report["acceptance_criteria"]}
    assert checks["acceptance.17_learning_reports_present"]["passed"] is True
    assert "固定返回今日/区间复盘段落" in checks["acceptance.17_learning_reports_present"]["message"]


def test_strict_trader_audit_phase3_readiness_present():
    report = run_strict_trader_audit(".")
    phases = {item["phase"]: item for item in report["phase3_readiness"]}
    assert set(phases) >= {"Phase 3-A", "Phase 3-B", "Phase 3-C", "Phase 3-D", "Phase 3-E", "Phase 3-F"}
    assert phases["Phase 3-A"]["title"] == "首页极简化与今日观察"
    assert phases["Phase 3-F"]["title"] == "组合优化器展示被拒组合和原因"
    assert report["phase3_summary"]["total"] >= 6
    assert report["phase3_summary"]["overall_ready"] is True


def test_strict_trader_audit_goal_readiness_all_achieved():
    report = run_strict_trader_audit(".")
    assert report["goal_summary"]["overall_ready"] is True
    failed = [item for item in report["goal_readiness"] if not item["achieved"]]
    assert failed == []


def test_strict_trader_audit_goal_readiness_covers_objective_groups():
    report = run_strict_trader_audit(".")
    categories = {item["category"] for item in report["goal_readiness"]}
    assert {"产品原则", "技术目标", "验收标准"}.issubset(categories)
    requirements = " ".join(item["requirement"] for item in report["goal_readiness"])
    assert "DeepSeek" in requirements
    assert "赔率市场去水概率" in requirements
    assert "真实用户历史 CSV" in requirements


def test_strict_trader_audit_phase3b_mentions_source_health():
    report = run_strict_trader_audit(".")
    phases = {item["phase"]: item for item in report["phase3_readiness"]}
    evidence = " ".join(phases["Phase 3-B"]["evidence"])
    assert "source_health=" in evidence
    assert "all_attempts_stable=" in evidence
    assert "scan_window=" in evidence
    assert "scan_complete=True" in evidence
    assert "scanned_dates=" in evidence
    assert "fallback_attempts=" in evidence
    assert "empty_attempts=" in evidence
    assert "warning_attempts=" in evidence


def test_strict_trader_audit_phase3e_mentions_user_readiness():
    report = run_strict_trader_audit(".")
    phases = {item["phase"]: item for item in report["phase3_readiness"]}
    evidence = " ".join(phases["Phase 3-E"]["evidence"])
    assert "user_readiness_items=" in evidence
    assert "user_readiness_status=" in evidence
    assert "preflight_checks=" in evidence
    assert "rows_normalized=" in evidence
    assert "had_odds_coverage=" in evidence
    assert "replay_readiness=" in evidence
    assert "calibration_status=" in evidence
    assert "cli_handoff_mode=cli_only_write_step" in evidence
    assert "cli_handoff_outputs=2" in evidence


def test_strict_trader_audit_phase3c_mentions_schedule_and_travel():
    report = run_strict_trader_audit(".")
    phases = {item["phase"]: item for item in report["phase3_readiness"]}
    evidence = " ".join(phases["Phase 3-C"]["evidence"])
    assert "signal_status_keys=" in evidence
    assert "intelligence_gap_actions=" in evidence
    assert "gap_action_status=" in evidence
    assert "schedule" in evidence
    assert "travel" in evidence
    assert "external_signal_connected=" in evidence
    assert "external_signal_source=user_json" in evidence
    assert "external_signal_load_status=loaded" in evidence
    assert "external_signal_invalid_items=0" in evidence
    assert "external_signal_coverage=" in evidence
    assert "news" in evidence


def test_strict_trader_audit_phase3d_mentions_probability_integrity():
    report = run_strict_trader_audit(".")
    phases = {item["phase"]: item for item in report["phase3_readiness"]}
    evidence = " ".join(phases["Phase 3-D"]["evidence"])
    assert "integrity_rows=" in evidence
    assert "integrity_status=pass:" in evidence

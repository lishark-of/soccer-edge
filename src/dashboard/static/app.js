const C = window.FootballComponents;

const state = {
  lastRaw: {},
  todayView: null,
  matchesView: null,
  optimizerView: null,
  scoreGoalsView: null,
  operationView: null,
  importView: null,
  qaView: null,
};

function qs(selector) { return document.querySelector(selector); }
function value(selector, fallback = "") {
  const el = qs(selector);
  return el && el.value !== undefined ? el.value : fallback;
}
function apiBase() { return value("#apiBase", "http://127.0.0.1:8765").replace(/\/$/, ""); }
function currentDateParam() { return value("#date", ""); }
function providerParam() { return value("#provider", "auto"); }
function bankrollParam() { return value("#initialBankroll", "10000"); }
function riskProfileParam() { return value("#riskProfile", "aggressive"); }

function endpoint(path, params = {}) {
  const url = new URL(`${apiBase()}${path}`);
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== "") url.searchParams.set(key, val);
  });
  return url.toString();
}

async function request(path, params = {}, label = "请求") {
  setStatus("Loading", `${label}进行中`);
  try {
    const response = await fetch(endpoint(path, params));
    const payload = await response.json();
    state.lastRaw = payload;
    renderRaw(payload);
    renderWarnings(payload.warnings || payload.data?.warnings || []);
    setStatus(payload.ok ? "OK" : "Error", label);
    return payload;
  } catch (error) {
    const payload = { ok: false, error: { code: "connection_error", message: "本地 API 连接失败，请确认服务已启动。" }, warnings: ["本地 API 可能尚未启动，或端口被占用。"] };
    state.lastRaw = payload;
    renderRaw(payload);
    renderWarnings(payload.warnings);
    setStatus("Offline", "连接失败");
    return payload;
  }
}

function setStatus(status, action) {
  if (qs("#statusText")) qs("#statusText").textContent = status;
  if (qs("#lastAction")) qs("#lastAction").textContent = action || "";
}
function renderRaw(payload) { if (qs("#jsonOutput")) qs("#jsonOutput").textContent = JSON.stringify(payload || {}, null, 2); }
function renderWarnings(warnings = []) { if (qs("#warningsList")) qs("#warningsList").innerHTML = C.warnings(warnings); }
function switchView(name) {
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("isActive", tab.dataset.view === name));
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("isVisible", view.id === `view-${name}`));
}

function tableOrEmpty(rows, columns, message = "暂无数据") {
  return rows && rows.length ? C.table(rows, columns) : `<div class="emptyState">${C.escapeHtml(message)}</div>`;
}

const obsColumns = [
  { key: "match", label: "比赛" },
  { key: "play_type", label: "玩法" },
  { key: "direction", label: "方向" },
  { key: "official_odds", label: "官方赔率" },
  { key: "market_prob", label: "市场去水概率" },
  { key: "model_prob", label: "融合概率" },
  { key: "edge", label: "Edge" },
  { key: "ev", label: "EV" },
  { key: "confidence_score", label: "信心" },
  { key: "risk_level", label: "风险" },
  { key: "selection_reason", label: "纪律判断" },
  { key: "supporting_factors", label: "支持因素" },
  { key: "opposing_factors", label: "反对因素" },
  { key: "missing_signals", label: "缺失情报" },
];
const comboColumns = [
  { key: "legs", label: "组合" },
  { key: "odds", label: "组合赔率" },
  { key: "model_prob", label: "组合概率" },
  { key: "market_prob", label: "市场概率" },
  { key: "ev", label: "EV" },
  { key: "risk_level", label: "风险" },
  { key: "paper_stake", label: "纸面投入" },
];
const rejectedComboColumns = [
  { key: "type", label: "类型" },
  { key: "legs", label: "组合" },
  { key: "odds", label: "组合赔率" },
  { key: "model_prob", label: "组合概率" },
  { key: "market_prob", label: "市场概率" },
  { key: "ev", label: "EV" },
  { key: "edge", label: "Edge" },
  { key: "risk_level", label: "风险" },
  { key: "status", label: "状态" },
  { key: "reject_reason", label: "被拒原因" },
];

async function loadToday() {
  const payload = await request("/api/view/next-available", {
    provider: providerParam(),
    date: currentDateParam(),
    bankroll: bankrollParam(),
    risk_profile: riskProfileParam(),
  }, "自动读取今日观察");
  if (payload.ok) renderToday(payload.data);
  switchView("today");
}

function renderToday(view) {
  state.todayView = view;
  qs("#todayCards").classList.remove("skeletonBlock");
  qs("#todayCards").innerHTML = C.cards([
    { label: "selected_date", value: view.selected_date || "N/A", help: "自动尝试 today 到 today+3 后选中的日期。" },
    { label: "可售比赛数", value: view.matches_count ?? 0, help: "当前找到的可售竞彩足球比赛数量。" },
    { label: "provider_used", value: view.provider_used || "unknown", help: "实际数据源，Sporttery 失败时会标记 fallback。" },
    { label: "Top 单关", value: (view.top_singles || []).length, help: "按 EV / 概率排序的单关观察。" },
    { label: "Top 2串1", value: (view.top_2x1 || []).length, help: "通过组合纪律的 2串1 观察。" },
    { label: "缺失情报", value: (view.missing_signals || []).length, help: "新闻、伤停、首发、天气未接入时不编造。" },
  ]);
  const status = view.data_source_status || {};
  const health = view.source_health || {};
  const externalSignals = view.external_signals_status || {};
  qs("#dataSourceStatus").innerHTML = C.list([
    `健康状态：${health.health || status.status || "unknown"}`,
    `说明：${health.message_zh || status.message_zh || "暂无说明"}`,
    `实际 provider：${health.provider_used || view.provider_used || "unknown"}`,
    `扫描日期：${(health.scanned_dates || []).join("、") || "N/A"}`,
    health.scan_summary_zh || "扫描窗口：N/A",
    `成功次数：${health.successful_attempts ?? 0}/${health.attempt_count ?? 0}`,
    `提醒数量：${health.warning_count ?? 0}`,
    `外部情报：${externalSignals.source_type || "not_provided"}，覆盖 ${externalSignals.matched_count ?? 0}/${externalSignals.matches_count ?? 0} 场`,
    `情报读取状态：${externalSignals.load_status || "not_provided"}，无效条目：${externalSignals.invalid_items ?? 0}`,
    externalSignals.message_zh || "未提供外部情报 JSON。",
    health.recovery_hint_zh || "数据源状态会明确标记，不会把回退数据伪装成 Sporttery。",
  ]);
  qs("#todaySingles").innerHTML = tableOrEmpty(view.top_singles || [], obsColumns, "当前没有通过纪律筛选的单关观察。若无 Edge，显示无观察价值。");
  qs("#todayParlay2").innerHTML = tableOrEmpty(view.top_2x1 || [], comboColumns, "当前没有 2串1 入选。组合需要多场同时命中，风险纪律会更严格。 ");
  qs("#todayTotalGoals").innerHTML = tableOrEmpty(view.top_total_goals || [], obsColumns, "当前没有总进球观察。 ");
  qs("#todayScores").innerHTML = tableOrEmpty(view.top_scores || [], obsColumns, "当前没有比分观察。 ");
  qs("#todayRejectedParlay2").innerHTML = tableOrEmpty(view.top_rejected_2x1 || [], rejectedComboColumns, "当前没有 2串1 被拒候选。");
  qs("#todayRejectedParlay3").innerHTML = tableOrEmpty(view.top_rejected_3x1 || [], rejectedComboColumns, "当前没有 3串1 被拒候选。");
  qs("#todayRiskTip").innerHTML = C.list([view.max_risk_tip || "请先查看数据源状态和缺失情报。"]);
  qs("#todayMissing").innerHTML = (view.signal_status || []).length
    ? C.table(view.signal_status, [
      { key: "signal", label: "情报" },
      { key: "status", label: "状态" },
      { key: "impact", label: "影响" },
      { key: "coverage", label: "覆盖" },
      { key: "source_zh", label: "来源" },
      { key: "message_zh", label: "说明" },
    ])
    : C.list((view.missing_signals || []).length ? view.missing_signals : ["当前没有缺失情报记录。"]);
}

async function loadMatches() {
  const payload = await request("/api/view/matches", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam() }, "查看竞彩足球");
  if (payload.ok) renderMatches(payload.data);
  switchView("matches");
}
function renderMatches(view) {
  state.matchesView = view;
  qs("#matchesCards").innerHTML = C.cards(view.summary_cards || []);
  qs("#matchesNotes").innerHTML = C.list(view.explanations || view.data_source_notes || []);
  qs("#matchesTable").innerHTML = C.table(view.matches_table || [], [
    { key: "match_no", label: "编号" }, { key: "league", label: "联赛" }, { key: "kickoff_at", label: "开赛时间" },
    { key: "home_team", label: "主队" }, { key: "away_team", label: "客队" }, { key: "had_win", label: "胜" },
    { key: "had_draw", label: "平" }, { key: "had_lose", label: "负" }, { key: "handicap", label: "让球" },
    { key: "hhad_win", label: "让胜" }, { key: "hhad_draw", label: "让平" }, { key: "hhad_lose", label: "让负" },
    { key: "source", label: "数据源" },
  ]);
}

async function runOptimizer(compareProfiles = true) {
  const payload = await request("/api/view/optimizer", {
    provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), bankroll: bankrollParam(), risk_profile: riskProfileParam(), show_rejected: "1", compare_profiles: compareProfiles ? "1" : "0",
  }, compareProfiles ? "对比风险档位" : "生成观察组合");
  if (payload.ok) renderOptimizer(payload.data);
  switchView("optimizer");
}
function renderOptimizer(view) {
  state.optimizerView = view;
  qs("#optimizerCards").innerHTML = C.cards(view.summary_cards || []);
  qs("#optimizerNo2Reason").innerHTML = C.list([view.no_2x1_reason || "当前没有 2串1 入选，请查看被拒原因。"]);
  qs("#optimizerProfileComparison").innerHTML = C.table(view.profile_comparison || [], [
    { key: "profile", label: "方案" }, { key: "daily_exposure_cap", label: "每日上限" }, { key: "recommended_paper_exposure", label: "纸面投入" },
    { key: "singles_count", label: "单关" }, { key: "parlay_2x1_count", label: "2串1" }, { key: "parlay_3x1_count", label: "3串1" }, { key: "note", label: "说明" },
  ]);
  const selectedCols = [
    { key: "type", label: "类型" }, { key: "match", label: "比赛" }, { key: "legs", label: "组成" }, { key: "odds", label: "赔率" },
    { key: "model_prob", label: "模型概率" }, { key: "market_prob", label: "市场概率" }, { key: "ev", label: "EV" }, { key: "edge", label: "Edge" },
    { key: "paper_stake", label: "纸面投入" }, { key: "risk_level", label: "风险" }, { key: "reason", label: "原因" },
  ];
  qs("#optimizerSingles").innerHTML = tableOrEmpty(view.singles_table || [], selectedCols);
  qs("#optimizerParlay2").innerHTML = tableOrEmpty(view.parlay_2x1_table || [], selectedCols, "当前没有 2串1 入选。不要因为赔率高就盲目组合。");
  qs("#optimizerParlay3").innerHTML = tableOrEmpty(view.parlay_3x1_table || [], selectedCols, "当前没有 3串1 入选。3串1 风险最高。 ");
  const rankCols = [
    { key: "type", label: "类型" }, { key: "match", label: "候选" }, { key: "legs", label: "组成" }, { key: "odds", label: "赔率" },
    { key: "model_prob", label: "模型概率" }, { key: "market_prob", label: "市场概率" }, { key: "ev", label: "EV" }, { key: "edge", label: "Edge" },
    { key: "correlation_discount", label: "相关性折扣" }, { key: "paper_stake", label: "纸面投入" }, { key: "status", label: "状态" }, { key: "reject_reason", label: "被拒原因" },
  ];
  qs("#optimizerSingleRanking").innerHTML = C.table(view.candidate_rankings?.singles || [], rankCols);
  qs("#optimizerParlay2Ranking").innerHTML = tableOrEmpty(view.candidate_rankings?.parlay_2x1 || [], rankCols, "当前没有可排序的 2串1 候选。 ");
  qs("#optimizerParlay3Ranking").innerHTML = tableOrEmpty(view.candidate_rankings?.parlay_3x1 || [], rankCols, "当前没有可排序的 3串1 候选。 ");
  qs("#optimizerRejected").innerHTML = C.table(view.rejected_table || [], [
    { key: "type", label: "类型" }, { key: "match", label: "候选" }, { key: "ev", label: "EV" }, { key: "edge", label: "Edge" }, { key: "risk_level", label: "风险" }, { key: "reason", label: "被拒原因" },
  ]);
  qs("#optimizerExplanations").innerHTML = C.list(view.explanations || []);
  qs("#parlay2Table").innerHTML = qs("#optimizerParlay2").innerHTML;
  qs("#parlay3Table").innerHTML = qs("#optimizerParlay3").innerHTML;
  qs("#parlay2RejectedTable").innerHTML = tableOrEmpty(view.candidate_rankings?.parlay_2x1 || [], rankCols, "当前没有 2串1 被拒候选。 ");
  qs("#parlay3RejectedTable").innerHTML = tableOrEmpty(view.candidate_rankings?.parlay_3x1 || [], rankCols, "当前没有 3串1 被拒候选。 ");
  qs("#riskNotes").innerHTML = C.list([view.no_2x1_reason || "组合观察会放大风险。", ...(view.explanations || [])]);
}

async function loadScoreGoals() {
  const payload = await request("/api/view/score-goals", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam() }, "刷新比分/进球数");
  if (payload.ok) renderScoreGoals(payload.data);
  switchView("scoregoals");
}
function renderScoreGoals(view) {
  state.scoreGoalsView = view;
  qs("#scoreGoalsCards").innerHTML = C.cards(view.summary_cards || []);
  qs("#scoreGoalsHandicap").innerHTML = tableOrEmpty(view.handicap_table || [], obsColumns, "当前没有让球胜平负观察。 ");
  qs("#scoreGoalsTotals").innerHTML = C.table(view.total_goals_table || [], obsColumns);
  qs("#scoreGoalsScores").innerHTML = C.table(view.score_table || [], obsColumns);
  qs("#scoreGoalsIntegrity").innerHTML = tableOrEmpty(view.probability_integrity || [], [
    { key: "match", label: "比赛" },
    { key: "total_goals_sum", label: "总进球合计" },
    { key: "had_sum", label: "胜平负合计" },
    { key: "hhad_sum", label: "让球合计" },
    { key: "top5_score_mass", label: "Top5 比分覆盖" },
    { key: "status", label: "状态" },
    { key: "message_zh", label: "说明" },
  ], "暂无概率矩阵完整性数据。");
  qs("#scoreGoalsNotes").innerHTML = C.list([...(view.risk_notes || []), ...((view.missing_signals || []).map((x) => `缺失情报：${x}`))]);
}

async function runOperation() {
  const payload = await request("/api/view/operation", { historical_data: value("#operationData"), initial_bankroll: bankrollParam() }, "运行模拟走盘");
  if (payload.ok) renderOperation(payload.data);
  switchView("operation");
}
function renderOperation(view) {
  state.operationView = view;
  qs("#operationCards").innerHTML = C.cards(view.summary_cards || []);
  qs("#operationEquityTable").innerHTML = C.table(view.equity_curve || [], [{ key: "date", label: "日期" }, { key: "bankroll", label: "纸面本金" }, { key: "daily_profit", label: "当日盈亏" }, { key: "observations", label: "观察项" }]);
  qs("#operationComboTable").innerHTML = C.table(view.combo_summary || [], [{ key: "type", label: "类型" }, { key: "count", label: "观察数" }, { key: "hit_rate", label: "命中率" }, { key: "profit", label: "盈亏" }, { key: "roi", label: "ROI" }]);
  qs("#operationWalkLog").innerHTML = C.table(view.walk_log_table || [], [{ key: "date", label: "日期" }, { key: "type", label: "类型" }, { key: "match", label: "比赛/组合" }, { key: "direction", label: "方向" }, { key: "paper_stake", label: "纸面金额" }, { key: "profit", label: "盈亏" }]);
  qs("#operationProfitExplanation").innerHTML = C.list(view.profit_explanation || ["暂无盈亏归因。请先运行模拟走盘。"]);
  qs("#operationDiagnostics").innerHTML = C.list((view.diagnostics || []).map((item) => `问题：${item.title}；影响：${item.detail}；建议：${item.suggestion}`));
}

async function previewImport() {
  const params = { input: value("#importInput"), adapter: value("#adapter"), mapping: value("#mappingPath") };
  const payload = await request("/api/view/import/preview", params, "预检字段");
  if (payload.ok) renderImport(payload.data);
  const workflow = await request("/api/view/user-workflow", { input: params.input, mapping: params.mapping }, "生成用户 CSV 复盘路径");
  if (workflow.ok) renderUserWorkflow(workflow.data);
  switchView("import");
}
function renderImport(view) {
  state.importView = view;
  qs("#importCards").innerHTML = C.cards(view.summary_cards || []);
  qs("#fieldReportTable").innerHTML = C.table(view.field_report?.recognized_fields || [], [{ key: "canonical", label: "系统字段" }, { key: "label_zh", label: "中文含义" }, { key: "source", label: "CSV 列名" }, { key: "status", label: "状态" }]);
  qs("#repairSuggestionTable").innerHTML = C.table(view.repair_suggestions || [], [{ key: "severity", label: "级别" }, { key: "field", label: "字段" }, { key: "message_zh", label: "问题" }, { key: "suggestion_zh", label: "怎么修" }, { key: "mapping_example", label: "mapping 示例" }]);
  qs("#importQuality").innerHTML = `<pre>${C.escapeHtml(JSON.stringify(view.quality || {}, null, 2))}</pre>`;
}
function renderUserWorkflow(view) {
  qs("#userWorkflowReadinessCards").innerHTML = C.cards(view.readiness_cards || []);
  qs("#userWorkflowReadinessTable").innerHTML = C.table(view.readiness_table || [], [
    { key: "item", label: "环节" },
    { key: "status", label: "状态" },
    { key: "meaning_zh", label: "含义" },
    { key: "next_action_zh", label: "下一步" },
  ]);
  qs("#userWorkflowPreflightChecks").innerHTML = C.table(view.preflight_checks || [], [
    { key: "item", label: "检查项" },
    { key: "status", label: "状态" },
    { key: "value", label: "数值" },
    { key: "message_zh", label: "说明" },
  ]);
  const handoff = view.cli_handoff || {};
  qs("#userWorkflowCliHandoff").innerHTML = [
    C.list(handoff.notes || ["Dashboard/API 保持只读；完整 workflow 由 CLI 执行。"]),
    handoff.command ? `<pre>${C.escapeHtml(handoff.command)}</pre>` : "",
    C.table(handoff.expected_outputs || [], [
      { key: "label", label: "输出" },
      { key: "path", label: "路径" },
      { key: "git_policy", label: "Git 策略" },
    ]),
  ].join("");
  qs("#userWorkflowSteps").innerHTML = C.table(view.steps || [], [
    { key: "step", label: "步骤" },
    { key: "title", label: "动作" },
    { key: "status", label: "状态" },
    { key: "summary", label: "说明" },
  ]);
  qs("#userWorkflowBacktestNotes").innerHTML = C.list(view.backtest_explanation || ["完整执行 workflow 后会显示回测解释。"]);
  qs("#userWorkflowCalibrationNotes").innerHTML = C.list(view.calibration_explanation || ["完整执行 workflow 后会显示校准说明。"]);
  qs("#userWorkflowQualityNotes").innerHTML = C.list(view.data_quality_notes || ["字段预检后会显示数据质量提示。"]);
  qs("#userWorkflowNextSteps").innerHTML = C.list(view.next_steps || ["字段预检通过后，可使用 CLI 完整执行标准化、回测、校准和分析。"]);
}

async function runQa() {
  const payload = await request("/api/view/qa", {}, "查看 QA 状态");
  if (payload.ok) renderQa(payload.data);
  switchView("qa");
}
function renderQa(view) {
  state.qaView = view;
  qs("#qaCards").innerHTML = C.cards(view.summary_cards || []);
  qs("#qaChecks").innerHTML = C.table([...(view.failed_checks || []), ...(view.warning_checks || [])], [{ key: "name", label: "检查项" }, { key: "severity", label: "等级" }, { key: "passed", label: "通过" }, { key: "message", label: "说明" }]);
}

async function checkHealth() { await request("/api/health", {}, "检查本地服务"); }
function clearOutput() { state.lastRaw = {}; renderRaw({}); renderWarnings([]); setStatus("Idle", "已清空"); }

function bind(selector, event, handler) { const el = qs(selector); if (el) el.addEventListener(event, handler); }
document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => switchView(tab.dataset.view)));
bind("#todayRefreshBtn", "click", loadToday);
bind("#todayOptimizerBtn", "click", () => runOptimizer(true));
bind("#todayOperationBtn", "click", runOperation);
bind("#todayImportBtn", "click", previewImport);
bind("#healthBtn", "click", checkHealth);
bind("#clearBtn", "click", clearOutput);
bind("#matchesBtn", "click", loadMatches);
bind("#matchesToOptimizerBtn", "click", () => runOptimizer(true));
bind("#optimizerBtn", "click", () => runOptimizer(false));
bind("#optimizerCompareBtn", "click", () => runOptimizer(true));
bind("#scoreGoalsBtn", "click", loadScoreGoals);
bind("#operationBtn", "click", runOperation);
bind("#importBtn", "click", previewImport);
bind("#qaBtn", "click", runQa);

renderRaw({});
loadToday();

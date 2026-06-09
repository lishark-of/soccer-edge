const C = window.FootballComponents;
const GLOSSARY = window.FootballGlossary || {};
const state = {
  lastRaw: {},
  analysisView: null,
  backtestView: null,
  importView: null,
  calibrationView: null,
  qaView: null,
  matchesView: null,
  onboardingView: null,
  operationView: null,
  optimizerView: null,
  llmStatus: null,
  observationList: [],
};

const selectors = {
  apiBase: document.querySelector("#apiBase"),
  statusText: document.querySelector("#statusText"),
  lastAction: document.querySelector("#lastAction"),
  warningsList: document.querySelector("#warningsList"),
  jsonOutput: document.querySelector("#jsonOutput"),
};

function apiBase() {
  return selectors.apiBase.value.replace(/\/$/, "");
}

function value(id) {
  return document.querySelector(id).value;
}

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
  selectors.statusText.textContent = status;
  selectors.lastAction.textContent = action || "";
}

function renderRaw(payload) {
  selectors.jsonOutput.textContent = JSON.stringify(payload || {}, null, 2);
}

function renderWarnings(warnings = []) {
  selectors.warningsList.innerHTML = C.warnings(warnings);
}

function switchView(name) {
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("isActive", tab.dataset.view === name));
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("isVisible", view.id === `view-${name}`));
}

function renderOverview(healthPayload = null) {
  const health = healthPayload?.data || {};
  const cards = [
    { label: "App", value: "JC Edge", help: "竞彩足球概率分析与回测 · 本地只读。" },
    { label: "Version", value: health.version || "0.1.0-local", help: "当前本地 release 版本。" },
    { label: "Mode", value: "local read-only", help: "API 和 App 默认不写文件。" },
    { label: "API 状态", value: health.status || "待检查", help: "点击检查状态确认本地服务。" },
    { label: "Sporttery 状态", value: state.matchesView?.summary_cards?.find((c) => c.label === "实际数据源")?.value || "待查看", help: "auto 会尝试公开数据并可回退 mock。" },
    { label: "DeepSeek", value: state.llmStatus?.enabled ? "可选启用" : "默认关闭", help: "只用于解释，不参与概率计算。" },
  ];
  document.querySelector("#overviewCards").innerHTML = C.cards(cards);
  renderOnboardingSteps(state.onboardingView?.steps || defaultSteps());
  renderLlmStatus(state.llmStatus);
}

function defaultSteps() {
  return [
    { step: 1, title: "先用 mock 数据体验", summary: "不用准备文件，直接看完整流程。", action_label: "开始体验 mock 分析" },
    { step: 2, title: "查看竞彩足球比赛", summary: "查看 provider_used、赔率和数据源提醒。", action_label: "查看竞彩足球比赛" },
    { step: 3, title: "导入自己的历史 CSV", summary: "做字段识别和中文修复建议。", action_label: "导入历史 CSV" },
    { step: 4, title: "运行概率回测", summary: "查看命中率、ROI、回撤和校准表。", action_label: "运行概率回测" },
    { step: 5, title: "生成校准文件", summary: "写文件流程通过 CLI，App 只读展示状态。", action_label: "查看校准状态" },
    { step: 6, title: "查看候选信号与组合风险", summary: "加入观察清单，阅读风险解释。", action_label: "查看候选信号" },
  ];
}

function renderOnboardingSteps(steps = []) {
  document.querySelector("#onboardingSteps").innerHTML = steps.map((item) => `
    <article class="stepCard">
      <span class="stepIndex">${C.escapeHtml(item.step)}</span>
      <strong>${C.escapeHtml(item.title)}</strong>
      <p>${C.escapeHtml(item.summary)}</p>
      <span class="stepAction">${C.escapeHtml(item.action_label || "查看")}</span>
    </article>`).join("");
}

function renderMatches(view) {
  state.matchesView = view;
  document.querySelector("#matchesCards").innerHTML = C.cards(view.summary_cards || []);
  document.querySelector("#matchesNotes").innerHTML = C.list(view.explanations || view.data_source_notes || []);
  document.querySelector("#matchesTable").innerHTML = C.table(view.matches_table || [], [
    { key: "match_no", label: "编号" },
    { key: "league", label: "联赛" },
    { key: "kickoff_at", label: "开赛时间" },
    { key: "home_team", label: "主队" },
    { key: "away_team", label: "客队" },
    { key: "had_win", label: "胜" },
    { key: "had_draw", label: "平" },
    { key: "had_lose", label: "负" },
    { key: "handicap", label: "让球" },
    { key: "hhad_win", label: "让胜" },
    { key: "hhad_draw", label: "让平" },
    { key: "hhad_lose", label: "让负" },
    { key: "source", label: "数据源" },
  ]);
}

function renderAnalysis(view) {
  state.analysisView = view;
  document.querySelector("#singleTable").innerHTML = candidateTable(view.candidate_tables?.single || []);
  renderObservationList();
  const parlayColumns = [
    { key: "pass_type", label: "组合" },
    { key: "legs", label: "组成" },
    { key: "combined_odds", label: "组合赔率" },
    { key: "hit_probability", label: "组合模型命中概率" },
    { key: "market_probability", label: "市场概率" },
    { key: "ev", label: "EV" },
    { key: "risk_label", label: "风险" },
    { key: "explanation", label: "风险解释" },
  ];
  document.querySelector("#parlay2Table").innerHTML = C.table(view.candidate_tables?.parlay_2x1 || [], parlayColumns);
  document.querySelector("#parlay3Table").innerHTML = C.table(view.candidate_tables?.parlay_3x1 || [], parlayColumns);
  document.querySelector("#riskNotes").innerHTML = C.list(view.risk_notes || []);
  if (view.explanation_status) {
    state.llmStatus = {
      provider: view.explanation_status.provider || "local",
      enabled: view.explanation_status.provider === "deepseek",
      status: view.explanation_status.status || "loaded",
      model: "see API status",
      api_key_present: false,
      external_calls_default: false,
    };
    renderLlmStatus(state.llmStatus);
  }
}

function candidateTable(rows = []) {
  if (!rows.length) return '<div class="emptyState">暂无候选信号。可以先运行 mock 分析体验完整流程。</div>';
  return `<div class="tableWrap"><table><thead><tr>${["比赛", "玩法", "方向", "赔率", "去水概率", "模型概率", "Edge", "EV", "风险", "解释", "观察清单"].map((h) => `<th>${C.escapeHtml(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((row, index) => `
    <tr>
      <td>${C.escapeHtml(row.match)}</td>
      <td>${C.escapeHtml(row.play_type)}</td>
      <td>${C.escapeHtml(row.direction)}</td>
      <td>${C.escapeHtml(row.odds)}</td>
      <td>${C.escapeHtml(row.market_probability)}</td>
      <td>${C.escapeHtml(row.model_probability)}</td>
      <td>${C.escapeHtml(row.edge)}</td>
      <td>${C.escapeHtml(row.ev)}</td>
      <td><span class="riskPill">${C.escapeHtml(row.risk_label)}</span></td>
      <td>${C.escapeHtml(row.explanation)}</td>
      <td><button class="miniButton" data-observe="${index}">加入观察</button></td>
    </tr>`).join("")}</tbody></table></div>`;
}

function renderObservationList() {
  const target = document.querySelector("#observationList");
  if (!state.observationList.length) {
    target.innerHTML = '<div class="emptyState">观察清单为空。你可以把想继续研究的候选信号加入这里。</div>';
    return;
  }
  target.innerHTML = state.observationList.map((item, index) => `
    <article class="observationCard">
      <strong>${C.escapeHtml(item.match)} · ${C.escapeHtml(item.direction)}</strong>
      <p>${C.escapeHtml(item.explanation || "请结合概率、EV 和风险等级继续研究。")}</p>
      <button class="miniButton secondary" data-remove-observe="${index}">移出观察</button>
    </article>`).join("");
}

function renderLlmStatus(status) {
  const target = document.querySelector("#llmStatusCards");
  if (!target) return;
  const data = status || { provider: "deepseek", enabled: false, api_key_present: false, model: "deepseek-v4-flash", status: "disabled", external_calls_default: false };
  target.innerHTML = C.cards([
    { label: "解释 provider", value: data.provider || "deepseek", help: "DeepSeek 仅作为可选解释层。"},
    { label: "enabled", value: String(Boolean(data.enabled)), help: "默认 false；未启用时不发外部请求。"},
    { label: "API key present", value: String(Boolean(data.api_key_present)), help: "只显示布尔值，不暴露 key。"},
    { label: "model", value: data.model || "deepseek-v4-flash", help: "默认使用非废弃模型。"},
    { label: "status", value: data.status || "disabled", help: "disabled / missing_api_key / ready / fallback_local。"},
    { label: "默认外部调用", value: String(Boolean(data.external_calls_default)), help: "默认必须为 false。"},
  ]);
}

function renderOptimizer(view) {
  state.optimizerView = view;
  document.querySelector("#optimizerCards").innerHTML = C.cards(view.summary_cards || []);
  const columns = [
    { key: "type", label: "类型" },
    { key: "match", label: "比赛 / 组合" },
    { key: "legs", label: "组成" },
    { key: "odds", label: "赔率" },
    { key: "model_prob", label: "模型概率" },
    { key: "market_prob", label: "市场概率" },
    { key: "ev", label: "EV" },
    { key: "edge", label: "Edge" },
    { key: "paper_stake", label: "建议纸面投入" },
    { key: "risk_level", label: "风险" },
    { key: "reason", label: "入选原因" },
  ];
  document.querySelector("#optimizerSingles").innerHTML = C.table(view.singles_table || [], columns);
  document.querySelector("#optimizerParlay2").innerHTML = C.table(view.parlay_2x1_table || [], columns);
  document.querySelector("#optimizerParlay3").innerHTML = C.table(view.parlay_3x1_table || [], columns);
  document.querySelector("#optimizerRejected").innerHTML = C.table(view.rejected_table || [], [
    { key: "type", label: "类型" },
    { key: "match", label: "候选" },
    { key: "ev", label: "EV" },
    { key: "edge", label: "Edge" },
    { key: "risk_level", label: "风险" },
    { key: "reason", label: "放弃原因" },
  ]);
  document.querySelector("#optimizerExplanations").innerHTML = C.list(view.explanations || []);
}

function renderBacktest(view) {
  state.backtestView = view;
  document.querySelector("#backtestCards").innerHTML = C.cards(view.summary_cards || []);
  document.querySelector("#metricExplanations").innerHTML = C.list(view.metric_explanations || []);
  document.querySelector("#calibrationTable").innerHTML = C.table(view.calibration_table || [], [
    { key: "outcome", label: "结果" },
    { key: "range", label: "概率分箱" },
    { key: "count", label: "样本数" },
    { key: "avg_predicted_prob", label: "平均预测概率" },
    { key: "observed_frequency", label: "实际频率" },
    { key: "gap", label: "差距" },
  ]);
  document.querySelector("#betsTable").innerHTML = C.table(view.bets_table || [], [
    { key: "date", label: "日期" },
    { key: "league", label: "联赛" },
    { key: "match", label: "比赛" },
    { key: "direction", label: "方向" },
    { key: "odds", label: "赔率" },
    { key: "model_probability", label: "模型概率" },
    { key: "market_probability", label: "市场概率" },
    { key: "ev", label: "EV" },
    { key: "hit", label: "是否命中" },
    { key: "profit", label: "模拟收益" },
  ]);
}

function renderOperation(view) {
  state.operationView = view;
  document.querySelector("#operationCards").innerHTML = C.cards(view.summary_cards || []);
  document.querySelector("#operationEquityTable").innerHTML = C.table(view.equity_curve || [], [
    { key: "date", label: "日期" },
    { key: "bankroll", label: "纸面本金" },
    { key: "daily_profit", label: "当日盈亏" },
    { key: "observations", label: "观察项数" },
  ]);
  document.querySelector("#operationComboTable").innerHTML = C.table(view.combo_summary || [], [
    { key: "type", label: "类型" },
    { key: "count", label: "观察数" },
    { key: "settled", label: "已结算" },
    { key: "hits", label: "命中" },
    { key: "hit_rate", label: "命中率" },
    { key: "paper_staked", label: "纸面投入" },
    { key: "profit", label: "盈亏" },
    { key: "roi", label: "ROI" },
  ]);
  document.querySelector("#operationWalkLog").innerHTML = C.table(view.walk_log_table || [], [
    { key: "date", label: "日期" },
    { key: "type", label: "类型" },
    { key: "match", label: "比赛 / 组合" },
    { key: "direction", label: "方向" },
    { key: "paper_stake", label: "纸面金额" },
    { key: "odds", label: "赔率" },
    { key: "hit", label: "模拟结算" },
    { key: "profit", label: "盈亏" },
    { key: "bankroll_after", label: "结算后本金" },
  ]);
  const issues = (view.diagnostics || []).map((item) => `问题：${item.title}；影响：${item.detail}；建议调整：${item.suggestion}`);
  document.querySelector("#operationDiagnostics").innerHTML = C.list(issues.length ? issues : ["当前未发现严重问题，但仍需更多真实历史数据验证。"]);
}

function renderImport(view) {
  state.importView = view;
  document.querySelector("#importCards").innerHTML = C.cards(view.summary_cards || []);
  const fieldReport = view.field_report || {};
  document.querySelector("#fieldReportTable").innerHTML = C.table(fieldReport.recognized_fields || [], [
    { key: "canonical", label: "系统字段" },
    { key: "label_zh", label: "中文含义" },
    { key: "source", label: "CSV 列名" },
    { key: "status", label: "状态" },
  ]);
  document.querySelector("#repairSuggestionTable").innerHTML = C.table(view.repair_suggestions || [], [
    { key: "severity", label: "级别" },
    { key: "field", label: "字段" },
    { key: "message_zh", label: "问题" },
    { key: "suggestion_zh", label: "怎么修" },
    { key: "mapping_example", label: "mapping 示例" },
  ]);
  document.querySelector("#importQuality").innerHTML = `<pre>${C.escapeHtml(JSON.stringify(view.quality || {}, null, 2))}</pre>`;
}

function renderCalibration(view) {
  state.calibrationView = view;
  document.querySelector("#calibrationCards").innerHTML = C.cards(view.summary_cards || []);
  document.querySelector("#calibrationNotes").innerHTML = C.list(view.explanations || []);
}

function renderQa(view) {
  state.qaView = view;
  document.querySelector("#qaCards").innerHTML = C.cards(view.summary_cards || []);
  const checks = [...(view.failed_checks || []), ...(view.warning_checks || [])];
  document.querySelector("#qaChecks").innerHTML = C.table(checks, [
    { key: "name", label: "检查项" },
    { key: "severity", label: "等级" },
    { key: "passed", label: "通过" },
    { key: "message", label: "说明" },
  ]);
}

function renderGlossary() {
  const rows = Object.entries(GLOSSARY).map(([key, text]) => ({ key, text }));
  document.querySelector("#glossaryList").innerHTML = C.table(rows, [
    { key: "key", label: "术语" },
    { key: "text", label: "解释" },
  ]);
}

async function loadOnboarding() {
  const payload = await request("/api/view/onboarding", {}, "加载使用路径");
  if (payload.ok) {
    state.onboardingView = payload.data;
    renderOverview();
  }
}

async function checkHealth() {
  const payload = await request("/api/health", {}, "检查状态");
  renderOverview(payload.ok ? payload : null);
}

async function loadMatches() {
  const payload = await request("/api/view/matches", { provider: value("#provider"), date: value("#date") }, "查看竞彩足球比赛");
  if (payload.ok) renderMatches(payload.data);
  switchView("matches");
}

async function loadSportteryStatus() {
  const payload = await request("/api/view/sporttery-status", { provider: value("#provider"), date: value("#date") }, "刷新数据源状态");
  if (payload.ok) {
    renderMatches(payload.data);
    renderWarnings(payload.data.warnings || []);
  }
  switchView("matches");
}

async function runAnalysis() {
  const payload = await request("/api/view/analyze", { provider: value("#provider"), date: value("#date"), explain: value("#explainMode") }, "运行概率分析");
  if (payload.ok) renderAnalysis(payload.data);
  switchView("signals");
}

async function checkLlmStatus() {
  const payload = await request("/api/llm/status", {}, "检查解释模式");
  if (payload.ok) {
    state.llmStatus = payload.data;
    renderLlmStatus(payload.data);
  }
}

async function runOptimizer() {
  const payload = await request("/api/view/optimizer", { provider: value("#provider"), date: value("#date"), bankroll: value("#initialBankroll") }, "生成观察组合");
  if (payload.ok) renderOptimizer(payload.data);
  switchView("optimizer");
}

async function runBacktest() {
  const payload = await request("/api/view/backtest", { historical_data: value("#historicalData") }, "运行概率回测");
  if (payload.ok) renderBacktest(payload.data);
  switchView("backtest");
}

async function runOperation() {
  const payload = await request("/api/view/operation", { historical_data: value("#operationData"), initial_bankroll: value("#initialBankroll") }, "运行模拟走盘");
  if (payload.ok) renderOperation(payload.data);
  switchView("operation");
}

async function previewImport() {
  const payload = await request("/api/view/import/preview", { input: value("#importInput"), adapter: value("#adapter"), mapping: value("#mappingPath") }, "预检字段");
  if (payload.ok) renderImport(payload.data);
  switchView("import");
}

async function validateCalibration() {
  const payload = await request("/api/view/calibration/validate", { path: value("#calibrationPath") }, "验证校准文件");
  if (payload.ok) renderCalibration(payload.data);
  switchView("calibration");
}

async function runQa() {
  const payload = await request("/api/view/qa", {}, "查看 QA 状态");
  if (payload.ok) renderQa(payload.data);
  switchView("qa");
}

function clearOutput() {
  state.lastRaw = {};
  renderRaw({});
  renderWarnings([]);
  setStatus("Idle", "已清空");
}

document.addEventListener("click", (event) => {
  const observe = event.target.closest("[data-observe]");
  if (observe && state.analysisView) {
    const rows = state.analysisView.candidate_tables?.single || [];
    const item = rows[Number(observe.dataset.observe)];
    if (item) {
      state.observationList.push(item);
      renderObservationList();
    }
  }
  const remove = event.target.closest("[data-remove-observe]");
  if (remove) {
    state.observationList.splice(Number(remove.dataset.removeObserve), 1);
    renderObservationList();
  }
});

document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => switchView(tab.dataset.view)));
document.querySelector("#healthBtn").addEventListener("click", checkHealth);
document.querySelector("#matchesBtn").addEventListener("click", loadMatches);
document.querySelector("#sportteryStatusBtn").addEventListener("click", loadSportteryStatus);
document.querySelector("#analyzeBtn").addEventListener("click", runAnalysis);
document.querySelector("#optimizerBtn").addEventListener("click", runOptimizer);
document.querySelector("#backtestBtn").addEventListener("click", runBacktest);
document.querySelector("#operationBtn").addEventListener("click", runOperation);
document.querySelector("#importBtn").addEventListener("click", previewImport);
document.querySelector("#calibrationBtn").addEventListener("click", validateCalibration);
document.querySelector("#qaBtn").addEventListener("click", runQa);
document.querySelector("#clearBtn").addEventListener("click", clearOutput);
document.querySelector("#heroAnalyzeBtn").addEventListener("click", runAnalysis);
document.querySelector("#heroMatchesBtn").addEventListener("click", loadMatches);
document.querySelector("#heroImportBtn").addEventListener("click", previewImport);
document.querySelector("#overviewMatchesBtn").addEventListener("click", loadMatches);
document.querySelector("#overviewSignalsBtn").addEventListener("click", runAnalysis);
document.querySelector("#overviewBacktestBtn").addEventListener("click", runBacktest);
document.querySelector("#matchesToSignalsBtn").addEventListener("click", runAnalysis);
document.querySelector("#operationDetailBtn").addEventListener("click", () => switchView("operation"));
document.querySelector("#operationDiagBtn").addEventListener("click", () => switchView("operation"));
document.querySelector("#operationRawBtn").addEventListener("click", () => switchView("raw"));
document.querySelector("#providerWarningBtn").addEventListener("click", () => renderWarnings(state.matchesView?.warnings || []));

renderGlossary();
renderOverview();
loadOnboarding();
checkHealth();
checkLlmStatus();

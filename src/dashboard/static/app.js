const C = window.FootballComponents;
const GLOSSARY = window.FootballGlossary || {};
const state = {
  lastRaw: {},
  analysisView: null,
  backtestView: null,
  importView: null,
  calibrationView: null,
  qaView: null,
  llmStatus: null,
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
    const payload = { ok: false, error: { code: "connection_error", message: String(error) }, warnings: ["本地 API 可能尚未启动。"] };
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
    { label: "Version", value: health.version || "0.1.0-local", help: "当前本地 release 版本。" },
    { label: "Mode", value: "local read-only", help: "API 和 App 默认不写文件。" },
    { label: "Remote", value: "none", help: "当前本地仓库未配置 GitHub remote。" },
    { label: "服务状态", value: health.status || "待检查", help: "本地 API 健康状态。" },
    { label: "Release phase", value: health.release_phase || "phase2i", help: "当前 release packaging 阶段。" },
    { label: "分析能力", value: state.analysisView ? "已加载" : "待运行", help: "运行分析后会更新候选信号和组合风险。" },
    { label: "回测诊断", value: state.backtestView ? "已加载" : "待运行", help: "运行回测后会更新概率诊断。" },
    { label: "校准 artifact", value: state.calibrationView ? "已验证" : "待验证", help: "校准只是诊断辅助。" },
    { label: "QA", value: state.qaView ? "已运行" : "待运行", help: "质量检查不代表预测准确。" },
  ];
  document.querySelector("#overviewCards").innerHTML = C.cards(cards);
  renderLlmStatus(state.llmStatus);
}

function renderAnalysis(view) {
  state.analysisView = view;
  document.querySelector("#analysisCards").innerHTML = C.cards(view.summary_cards || []);
  document.querySelector("#componentNotes").innerHTML = C.list(view.component_notes || []);
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
  const singleColumns = [
    { key: "match", label: "比赛" },
    { key: "play_type", label: "玩法" },
    { key: "direction", label: "方向" },
    { key: "odds", label: "赔率" },
    { key: "market_probability", label: "去水概率" },
    { key: "model_probability", label: "模型概率" },
    { key: "edge", label: "Edge" },
    { key: "ev", label: "EV" },
    { key: "risk_label", label: "风险" },
    { key: "explanation", label: "本地解释" },
  ];
  document.querySelector("#singleTable").innerHTML = C.table(view.candidate_tables?.single || [], singleColumns);
  const parlayColumns = [
    { key: "pass_type", label: "组合" },
    { key: "legs", label: "组成" },
    { key: "combined_odds", label: "组合赔率" },
    { key: "hit_probability", label: "组合命中概率" },
    { key: "market_probability", label: "市场概率" },
    { key: "ev", label: "EV" },
    { key: "risk_label", label: "风险" },
    { key: "explanation", label: "风险解释" },
  ];
  document.querySelector("#parlay2Table").innerHTML = C.table(view.candidate_tables?.parlay_2x1 || [], parlayColumns);
  document.querySelector("#parlay3Table").innerHTML = C.table(view.candidate_tables?.parlay_3x1 || [], parlayColumns);
  document.querySelector("#riskNotes").innerHTML = C.list(view.risk_notes || []);
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
    { label: "默认外部调用", value: String(Boolean(data.external_calls_default)), help: "验证流程中必须为 false。"},
  ]);
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

function renderImport(view) {
  state.importView = view;
  document.querySelector("#importCards").innerHTML = C.cards(view.summary_cards || []);
  document.querySelector("#importQuality").innerHTML = `<h3>质量报告</h3><pre>${C.escapeHtml(JSON.stringify(view.quality || {}, null, 2))}</pre>`;
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

async function checkHealth() {
  const payload = await request("/api/health", {}, "检查状态");
  renderOverview(payload.ok ? payload : null);
}

async function runAnalysis() {
  const payload = await request("/api/view/analyze", { provider: value("#provider"), date: value("#date"), explain: value("#explainMode") }, "运行分析");
  if (payload.ok) renderAnalysis(payload.data);
  switchView("analysis");
}

async function checkLlmStatus() {
  const payload = await request("/api/llm/status", {}, "检查解释模式");
  if (payload.ok) {
    state.llmStatus = payload.data;
    renderLlmStatus(payload.data);
  }
  switchView("overview");
}

async function runBacktest() {
  const payload = await request("/api/view/backtest", { historical_data: value("#historicalData") }, "运行回测");
  if (payload.ok) renderBacktest(payload.data);
  switchView("backtest");
}

async function previewImport() {
  const payload = await request("/api/view/import/preview", { input: value("#importInput"), adapter: value("#adapter") }, "预检导入");
  if (payload.ok) renderImport(payload.data);
  switchView("import");
}

async function validateCalibration() {
  const payload = await request("/api/view/calibration/validate", { path: value("#calibrationPath") }, "验证校准");
  if (payload.ok) renderCalibration(payload.data);
  switchView("calibration");
}

async function runQa() {
  const payload = await request("/api/view/qa", {}, "运行 QA");
  if (payload.ok) renderQa(payload.data);
  switchView("qa");
}

function clearOutput() {
  state.lastRaw = {};
  renderRaw({});
  renderWarnings([]);
  setStatus("Idle", "已清空");
}

document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => switchView(tab.dataset.view)));
document.querySelector("#healthBtn").addEventListener("click", checkHealth);
document.querySelector("#llmStatusBtn").addEventListener("click", checkLlmStatus);
document.querySelector("#analyzeBtn").addEventListener("click", runAnalysis);
document.querySelector("#backtestBtn").addEventListener("click", runBacktest);
document.querySelector("#importBtn").addEventListener("click", previewImport);
document.querySelector("#calibrationBtn").addEventListener("click", validateCalibration);
document.querySelector("#qaBtn").addEventListener("click", runQa);
document.querySelector("#clearBtn").addEventListener("click", clearOutput);
document.querySelector("#quickAnalyzeBtn").addEventListener("click", runAnalysis);
document.querySelector("#quickBacktestBtn").addEventListener("click", runBacktest);
document.querySelector("#quickQaBtn").addEventListener("click", runQa);

renderGlossary();
renderOverview();
checkHealth();
checkLlmStatus();

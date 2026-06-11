const C = window.FootballComponents;

const state = {
  lastRaw: {},
  todayView: null,
  signalExplainView: null,
  reliabilityView: null,
  credibilityView: null,
  missingInfoView: null,
  signalsPreviewView: null,
  bestParlayView: null,
  traderReviewView: null,
  matchesView: null,
  optimizerView: null,
  scoreGoalsView: null,
  operationView: null,
  importView: null,
  qaView: null,
  dataSourcesView: null,
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
function externalSignalsParam() { return value("#externalSignalsPath", "data/fixtures/external_signals_example.json"); }

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

async function postJson(path, body = {}, label = "保存配置") {
  setStatus("Loading", `${label}进行中`);
  try {
    const response = await fetch(endpoint(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
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

function signalCards(rows, kind = "single", message = "暂无观察信号") {
  if (!rows || !rows.length) return `<div class="emptyState">${C.escapeHtml(message)}</div>`;
  return `<div class="signalCardGrid">${rows.slice(0, 4).map((row) => {
    const isCombo = kind === "combo";
    const title = isCombo ? (row.legs || row.match || "组合观察") : (row.match || "观察信号");
    const tag = isCombo ? (row.status || row.type || "组合") : `${row.play_type || "玩法"} · ${row.direction || "方向"}`;
    const reason = isCombo ? (row.discipline_summary_zh || row.reject_reason || row.reason || "通过组合纪律筛选。") : (row.recommended_action_zh || row.selection_reason || "查看概率、EV 和风险。");
    const metrics = isCombo
      ? [
          ["赔率", row.odds],
          ["概率", row.model_prob],
          ["EV", row.ev],
          ["风险", row.risk_level],
        ]
      : [
          ["赔率", row.official_odds],
          ["融合概率", row.model_prob],
          ["EV", row.ev],
          ["可信度", [row.confidence_label_zh, row.observation_confidence || row.confidence_score].filter(Boolean).join(" ")],
        ];
    return `
      <article class="signalCard ${isCombo && row.status === "未入选" ? "isRejected" : ""}">
        <div class="signalHead">
          <strong>${C.escapeHtml(title)}</strong>
          <span>${C.escapeHtml(tag)}</span>
        </div>
        <div class="metricStrip">${metrics.map(([label, value]) => `
          <div><span>${C.escapeHtml(label)}</span><b>${C.escapeHtml(value ?? "N/A")}</b></div>
        `).join("")}</div>
        <p class="reasonLine">${C.escapeHtml(reason)}</p>
        ${!isCombo && longshotText(row) ? `<p class="warningLine">${C.escapeHtml(longshotText(row))}</p>` : ""}
        ${!isCombo && row.reliability_explanation_zh ? `<p class="mutedLine">${C.escapeHtml(row.reliability_explanation_zh)}</p>` : ""}
        ${!isCombo && row.opposing_factors ? `<p class="mutedLine">${C.escapeHtml(row.opposing_factors)}</p>` : ""}
      </article>`;
  }).join("")}</div>`;
}

const obsColumns = [
  { key: "match", label: "比赛" },
  { key: "play_type", label: "玩法" },
  { key: "direction", label: "方向" },
  { key: "official_odds", label: "官方赔率" },
  { key: "odds_status_zh", label: "赔率状态" },
  { key: "market_prob", label: "市场去水概率" },
  { key: "model_prob", label: "融合概率" },
  { key: "edge", label: "Edge" },
  { key: "ev", label: "EV" },
  { key: "ev_status_zh", label: "EV 状态" },
  { key: "observation_confidence", label: "观察可信度" },
  { key: "confidence_label_zh", label: "可信度评级" },
  { key: "recommended_action_zh", label: "建议动作" },
  { key: "risk_level", label: "风险" },
  { key: "selection_reason", label: "纪律判断" },
  { key: "reliability_explanation_zh", label: "可靠性解释" },
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
  { key: "discipline_summary_zh", label: "纪律拆解" },
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
    { label: "情报完整度", value: `${view.intelligence_completeness?.score ?? "N/A"}/100`, help: view.intelligence_completeness?.summary_zh || "按赔率、赛程、球队、伤停、首发、天气等评分。" },
    { label: "可信度评分", value: `${view.credibility_audit?.credibility_score ?? "N/A"}/100`, help: view.credibility_audit?.reasons?.[0] || "综合数据源、缺失情报、模型一致性与风险质量。" },
    { label: "可信度门控", value: view.credibility_gate?.label_zh || view.credibility_audit?.credibility_gate?.label_zh || "N/A", help: view.credibility_gate?.reason_zh || view.credibility_audit?.credibility_gate?.reason_zh || "门控决定是否允许串联。" },
    { label: "完整度评级", value: view.intelligence_completeness?.label_zh || "N/A", help: "高/中/中低/低。缺失情报不会被编造。" },
    { label: "Top 单关", value: (view.top_singles || []).length, help: "按 EV / 概率排序的单关观察。" },
    { label: "Top 2串1", value: (view.top_2x1_display || view.top_2x1 || []).length, help: "通过组合纪律；若未入选，则展示最接近候选和被拒原因。" },
    { label: "缺失情报", value: (view.missing_signals || []).length, help: "新闻、伤停、首发、天气未接入时不编造。" },
  ]);
  qs("#todayReliabilityCards").innerHTML = C.cards((view.reliability_summary?.source_cards || view.source_coverage_cards || []).map((row) => ({
    label: row.source || row.label_zh,
    value: row.coverage || row.status || "N/A",
    help: row.message_zh || row.role || "",
  })));
  qs("#todaySourceCoverage").innerHTML = C.table(view.match_coverage_table || [], [
    { key: "match", label: "比赛" },
    { key: "api_football", label: "API-Football" },
    { key: "the_odds_api", label: "海外赔率" },
    { key: "injuries", label: "伤停" },
    { key: "lineup", label: "首发" },
    { key: "weather", label: "天气" },
    { key: "news", label: "新闻" },
    { key: "match_confidence", label: "匹配置信度" },
    { key: "message_zh", label: "说明" },
  ]);
  const status = view.data_source_status || {};
  const health = view.source_health || {};
  const externalSignals = view.external_signals_status || {};
  qs("#dataSourceStatus").innerHTML = C.list([
    `健康状态：${health.health || status.status || "unknown"}`,
    `可靠性评级：${health.reliability_label_zh || "N/A"}（${health.reliability_score ?? "N/A"}/100）`,
    `说明：${health.message_zh || status.message_zh || "暂无说明"}`,
    `判断建议：${health.decision_guide_zh || "请结合 provider_used、扫描窗口和缺失情报查看。"}`,
    `实际 provider：${health.provider_used || view.provider_used || "unknown"}`,
    `扫描日期：${(health.scanned_dates || []).join("、") || "N/A"}`,
    health.scan_summary_zh || "扫描窗口：N/A",
    `成功次数：${health.successful_attempts ?? 0}/${health.attempt_count ?? 0}`,
    `提醒数量：${health.warning_count ?? 0}`,
    ...(health.source_action_items || []),
    `外部情报：${externalSignals.source_type || "not_provided"}，覆盖 ${externalSignals.matched_count ?? 0}/${externalSignals.matches_count ?? 0} 场`,
    `情报读取状态：${externalSignals.load_status || "not_provided"}，无效条目：${externalSignals.invalid_items ?? 0}`,
    externalSignals.message_zh || "未提供外部情报 JSON。",
    health.recovery_hint_zh || "数据源状态会明确标记，不会把回退数据伪装成 Sporttery。",
  ]);
  qs("#todaySingles").innerHTML = signalCards(view.top_singles || [], "single", "当前没有通过纪律筛选的单关观察。若无 Edge，显示无观察价值。");
  const parlay2Selected = view.top_2x1 || [];
  const parlay2Display = parlay2Selected.length ? parlay2Selected : (view.top_2x1_display || []);
  const parlay2Intro = `<div class="note">${C.escapeHtml(view.top_2x1_empty_explanation || "2串1 需要多场同时命中，风险纪律会更严格。")}</div>`;
  qs("#todayParlay2").innerHTML = parlay2Intro + signalCards(parlay2Display, "combo", "当前没有 2串1 入选，也没有可排序的候选。");
  qs("#todayTotalGoals").innerHTML = signalCards(view.top_total_goals || [], "single", "当前没有总进球观察。 ");
  qs("#todayScores").innerHTML = signalCards(view.top_scores || [], "single", "当前没有比分观察。 ");
  qs("#todayRejectedParlay2").innerHTML = tableOrEmpty(view.top_rejected_2x1 || [], rejectedComboColumns, "当前没有 2串1 被拒候选。");
  qs("#todayRejectedParlay3").innerHTML = tableOrEmpty(view.top_rejected_3x1 || [], rejectedComboColumns, "当前没有 3串1 被拒候选。");
  const operationEntry = view.operation_entry || {};
  qs("#todayRiskTip").innerHTML = [
    C.list([
      view.max_risk_tip || "请先查看数据源状态和缺失情报。",
      operationEntry.summary || "查看模拟走盘可理解历史资金曲线、最大回撤、玩法贡献和为什么赚/亏。",
      operationEntry.disclaimer || "模拟经营不代表未来表现。",
    ]),
    operationEntry.metrics ? `<h4>${C.escapeHtml(operationEntry.title || "回测表现怎么看")}</h4>${C.list(operationEntry.metrics)}` : "",
  ].join("");
  qs("#todayTraderConclusion").innerHTML = C.list([
    view.strict_trader_conclusion || view.trader_review?.final_call_zh || "请先刷新今日观察。",
    view.optimizer?.no_combo_reason || view.best_parlay_summary?.no_combo_reason || view.credibility_gate?.reason_zh || "",
    ...(view.trader_review?.conclusions_zh || []),
  ]);
  const signalStatusHtml = (view.signal_status || []).length
    ? C.table(view.signal_status, [
      { key: "signal", label: "情报" },
      { key: "status", label: "状态" },
      { key: "confidence_zh", label: "可信度" },
      { key: "coverage", label: "覆盖" },
      { key: "source_zh", label: "来源" },
      { key: "message_zh", label: "说明" },
    ])
    : C.list((view.missing_signals || []).length ? view.missing_signals : ["当前没有缺失情报记录。"]);
  const gapActionsHtml = tableOrEmpty(view.intelligence_gap_actions || [], [
    { key: "signal", label: "情报" },
    { key: "status", label: "当前状态" },
    { key: "confidence_impact", label: "对信心的影响" },
    { key: "why_it_matters", label: "为什么重要" },
    { key: "next_action_zh", label: "如何补齐" },
    { key: "app_behavior", label: "App 处理方式" },
  ], "暂无情报缺口行动清单。");
  qs("#todayMissing").innerHTML = [
    signalStatusHtml,
    `<h4>情报覆盖怎么处理</h4>`,
    gapActionsHtml,
  ].join("");
  renderSignalExplainFromToday(view);
  renderReliabilityFromToday(view);
  renderCredibility(view.credibility_audit || {});
  renderBestParlay(view.best_parlay_summary || {});
  renderTraderReview(view.trader_review || {});
}

async function loadCredibility() {
  const payload = await request("/api/audit/credibility", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), risk_profile: riskProfileParam() }, "刷新可信度审计");
  if (payload.ok) renderCredibility(payload.data);
  switchView("credibility");
}
function renderCredibility(view) {
  state.credibilityView = view;
  if (!qs("#credibilityCards")) return;
  qs("#credibilityCards").innerHTML = C.cards([
    { label: "可信度评分", value: `${view.credibility_score ?? "N/A"}/100`, help: "不是胜率，是对数据和信号质量的审计分。" },
    { label: "评级", value: view.grade || "N/A", help: view.confidence_level_zh || view.confidence_level || "" },
    { label: "信心水平", value: view.confidence_level_zh || view.confidence_level || "N/A", help: "mock/fixture 数据不会给 high credibility。" },
    { label: "缺失信息", value: (view.missing_information || []).slice(0, 4).join("、") || "暂无", help: "缺失项会扣分，不会被编造。" },
  ]);
  qs("#credibilityReasons").innerHTML = C.list(view.reasons || ["暂无评分原因。"]);
  qs("#credibilityMissing").innerHTML = C.table([
    { type: "主要缺失", items: (view.missing_information || []).join("、") || "暂无" },
    { type: "部分覆盖", items: (view.partial_information || []).join("、") || "暂无" },
  ], [{ key: "type", label: "类型" }, { key: "items", label: "内容" }]);
  qs("#credibilityMustNot").innerHTML = C.list(view.must_not_overtrust || ["不要把高 EV 自动理解为高可信。"]);
}

async function loadMissingInfo() {
  const payload = await request("/api/intelligence/missing", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), risk_profile: riskProfileParam() }, "查看缺失情报");
  if (payload.ok) renderMissingInfo(payload.data);
  switchView("missinginfo");
}
function renderMissingInfo(view) {
  state.missingInfoView = view;
  if (!qs("#missingInfoCards")) return;
  qs("#missingInfoCards").innerHTML = C.cards([
    { label: "主要缺失", value: (view.missing_information || []).slice(0, 4).join("、") || "暂无", help: view.summary_zh || "" },
    { label: "部分覆盖", value: (view.partial_information || []).slice(0, 4).join("、") || "暂无", help: "已尝试读取，但源头暂未给出完整信息。" },
    { label: "门控状态", value: view.credibility_gate?.label_zh || "N/A", help: view.credibility_gate?.reason_zh || "" },
    { label: "补齐目录", value: view.external_signals_dir || "data/external_signals/", help: "用户真实 JSON 默认不提交。" },
  ]);
  qs("#missingInfoTable").innerHTML = C.table(view.fields || [], [
    { key: "label_zh", label: "情报" }, { key: "status_zh", label: "状态" }, { key: "impact_zh", label: "影响" },
    { key: "user_can_supply", label: "可由用户补齐" }, { key: "supply_hint_zh", label: "如何补齐" }, { key: "message_zh", label: "说明" },
  ]);
}

async function previewSignals() {
  const payload = await request("/api/intelligence/signals-preview", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), risk_profile: riskProfileParam(), signals_path: externalSignalsParam() }, "预览本地情报 JSON");
  if (payload.ok) renderSignalsPreview(payload.data);
  switchView("missinginfo");
}
function renderSignalsPreview(view) {
  state.signalsPreviewView = view;
  if (!qs("#signalsPreviewBox")) return;
  qs("#signalsPreviewBox").innerHTML = [
    C.list([
      `状态：${view.status?.load_status || "unknown"}`,
      `读取场次：${view.signals_count ?? 0}`,
      `用户已提供字段：${(view.supplied_fields || []).join("、") || "暂无"}`,
      `仍缺字段：${(view.missing_fields || []).join("、") || "暂无"}`,
      `门控：${view.credibility_gate?.label_zh || "N/A"} / ${view.credibility_gate?.score ?? "N/A"}`,
      view.message_zh || "本地 JSON 只读预览。",
      view.disclaimer || "不联网、不编造。",
    ]),
    view.missing_information_after_preview ? `<h4>覆盖预览后仍缺</h4>${C.list(view.missing_information_after_preview.missing_information || [])}` : "",
  ].join("");
}

async function loadBestParlay() {
  const payload = await request("/api/view/best-parlay", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), bankroll: bankrollParam(), risk_profile: riskProfileParam() }, "刷新优秀串联");
  if (payload.ok) renderBestParlay(payload.data);
  switchView("bestparlay");
}
function renderBestParlay(view) {
  state.bestParlayView = view;
  if (!qs("#bestParlayCards")) return;
  const bestCards = [
    { label: "最佳单关", value: shortCandidate(view.best_single), help: view.best_single?.selected_reason_zh || "" },
    { label: "最佳2串1", value: shortCandidate(view.best_2x1), help: view.best_2x1?.reject_reason || view.best_2x1?.selected_reason_zh || "" },
    { label: "最佳3串1", value: shortCandidate(view.best_3x1_if_allowed), help: view.best_3x1_if_allowed?.reject_reason || view.best_3x1_if_allowed?.selected_reason_zh || "" },
    { label: "风险调整最佳", value: shortCandidate(view.best_risk_adjusted_combo), help: view.conclusion_zh || "" },
  ];
  qs("#bestParlayCards").innerHTML = C.cards(bestCards);
  const rows = [
    rowCandidate("最佳单关", view.best_single),
    rowCandidate("最佳2串1", view.best_2x1),
    rowCandidate("最佳3串1", view.best_3x1_if_allowed),
    rowCandidate("最稳组合", view.safest_combo),
    rowCandidate("最高EV组合", view.highest_ev_combo),
    rowCandidate("风险调整最佳", view.best_risk_adjusted_combo),
  ];
  qs("#bestParlayTable").innerHTML = C.table(rows, bestParlayColumns());
  qs("#bestParlayRejected").innerHTML = tableOrEmpty((view.rejected_combos || []).slice(0, 10).map((item) => rowCandidate(item.label_zh || item.type || "被拒", item)), bestParlayColumns(), "暂无被拒组合。");
  qs("#bestParlayConclusion").innerHTML = C.list([view.conclusion_zh || "暂无结论。", view.risk_note_zh || "串关会放大风险。"]);
}

async function loadTraderReview() {
  const payload = await request("/api/view/trader-review", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), bankroll: bankrollParam(), risk_profile: riskProfileParam() }, "刷新严厉交易者复盘");
  if (payload.ok) renderTraderReview(payload.data);
  switchView("traderreview");
}
function renderTraderReview(view) {
  state.traderReviewView = view;
  if (!qs("#traderReviewCards")) return;
  const credibility = view.credibility || {};
  qs("#traderReviewCards").innerHTML = C.cards([
    { label: "最终判断", value: view.final_call_zh || "N/A", help: "严厉交易者结论。" },
    { label: "可信度", value: `${credibility.credibility_score ?? "N/A"}/100`, help: credibility.confidence_level_zh || "" },
    { label: "数据源", value: view.provider_used || "unknown", help: "实际使用的数据源。" },
    { label: "日期", value: view.selected_date || "N/A", help: "本次复盘日期。" },
  ]);
  qs("#traderReviewConclusions").innerHTML = C.list(view.conclusions_zh || []);
  qs("#traderReviewBest").innerHTML = C.table([
    rowCandidate("风险调整最佳", view.best_parlay?.best_risk_adjusted_combo),
    rowCandidate("最佳2串1", view.best_parlay?.best_2x1),
    rowCandidate("最佳3串1", view.best_parlay?.best_3x1_if_allowed),
  ], bestParlayColumns());
}

function rowCandidate(category, item = {}) {
  return {
    category,
    candidate: item?.legs || item?.match || item?.message_zh || "暂无",
    status: item?.status || "",
    odds: fmtNum(item?.odds),
    model_prob: fmtPct(item?.model_prob),
    market_prob: fmtPct(item?.market_prob),
    ev: fmtSignedPct(item?.ev),
    edge: fmtSignedPct(item?.edge),
    confidence: fmtPct(item?.confidence_score),
    risk_adjusted_score: fmtNum(item?.risk_adjusted_score),
    paper_stake: fmtRmb(item?.paper_stake),
    reason: item?.selected_reason_zh || item?.reject_reason || "",
  };
}
function longshotText(row = {}) {
  if (row.longshot_warning) return row.longshot_warning;
  const odds = Number(row.official_odds || row.odds || 0);
  if (Number.isFinite(odds) && odds >= 6) return "这是高赔率冷门观察，不是稳健信号；不适合作为串联核心。";
  return "";
}
function bestParlayColumns() {
  return [
    { key: "category", label: "类别" }, { key: "candidate", label: "候选" }, { key: "status", label: "状态" },
    { key: "odds", label: "赔率" }, { key: "model_prob", label: "模型概率" }, { key: "market_prob", label: "市场概率" },
    { key: "ev", label: "EV" }, { key: "edge", label: "Edge" }, { key: "confidence", label: "可信度" },
    { key: "risk_adjusted_score", label: "风险调整分" }, { key: "paper_stake", label: "纸面投入" }, { key: "reason", label: "原因" },
  ];
}
function shortCandidate(item = {}) {
  if (!item || item.status === "empty") return "暂无";
  return [item.status, item.legs || item.match || item.message_zh || "候选"].filter(Boolean).join(" · ");
}
function fmtPct(value) { const n = Number(value); return Number.isFinite(n) ? `${(n * 100).toFixed(1)}%` : "N/A"; }
function fmtSignedPct(value) { const n = Number(value); return Number.isFinite(n) ? `${n >= 0 ? "+" : ""}${(n * 100).toFixed(1)}%` : "N/A"; }
function fmtNum(value) { const n = Number(value); return Number.isFinite(n) ? n.toFixed(4) : "N/A"; }
function fmtRmb(value) { const n = Number(value); return Number.isFinite(n) ? `¥${n.toFixed(2)}` : "N/A"; }

function renderSignalExplainFromToday(view) {
  const rows = [...(view.top_singles || []), ...(view.top_total_goals || []), ...(view.top_scores || [])];
  const strong = rows.filter((row) => String(row.recommended_action_zh || "").startsWith("可观察"));
  const weak = rows.filter((row) => String(row.recommended_action_zh || "").startsWith("弱观察"));
  const waiting = rows.filter((row) => String(row.recommended_action_zh || "").startsWith("等待"));
  const rejected = rows.filter((row) => String(row.recommended_action_zh || "").startsWith("放弃"));
  qs("#signalExplainCards").innerHTML = C.cards([
    { label: "可观察", value: strong.length, help: "赔率和模型存在一定差异，但仍需看缺失情报。" },
    { label: "弱观察", value: weak.length, help: "有倾向，但可信度不足。" },
    { label: "等待赔率/情报", value: waiting.length, help: "暂不能判断价值。" },
    { label: "放弃", value: rejected.length, help: "当前无观察价值。" },
  ]);
  qs("#signalExplainStrong").innerHTML = signalCards(strong, "single", "当前没有强观察。");
  qs("#signalExplainWeak").innerHTML = signalCards(weak, "single", "当前没有弱观察。");
  qs("#signalExplainWaiting").innerHTML = signalCards(waiting, "single", "当前没有等待赔率/情报项。");
  qs("#signalExplainRejected").innerHTML = signalCards(rejected, "single", "当前没有放弃项。");
  qs("#signalExplainNotes").innerHTML = C.list([
    "观察可信度由市场赔率、模型概率、情报完整度、回测支撑和数据源可靠性组合而来。",
    "比分和总进球如果没有官方赔率，只展示模型倾向，暂不计算 EV。",
    "缺少伤停、首发、天气、新闻时不会编造，只会降低信心。",
  ]);
}

function renderReliabilityFromToday(view) {
  qs("#reliabilityCards").innerHTML = C.cards([
    { label: "情报完整度", value: `${view.intelligence_completeness?.score ?? "N/A"}/100`, help: view.intelligence_completeness?.summary_zh || "" },
    { label: "评级", value: view.intelligence_completeness?.label_zh || "N/A", help: "由真实赔率、第三方匹配、伤停/首发/天气等决定。" },
    { label: "主要缺口", value: (view.intelligence_completeness?.main_gaps_zh || []).slice(0, 4).join("、") || "暂无", help: "缺口不会被模型编造。" },
    { label: "比赛数", value: view.matches_count ?? 0, help: "本次可靠性评估覆盖的可售比赛。" },
  ]);
  qs("#reliabilitySourceCards").innerHTML = C.table(view.source_coverage_cards || [], [
    { key: "source", label: "数据源" },
    { key: "role", label: "用途" },
    { key: "status", label: "状态" },
    { key: "coverage", label: "覆盖" },
    { key: "score", label: "分数" },
    { key: "message_zh", label: "说明" },
  ]);
  qs("#reliabilityMatchCoverage").innerHTML = C.table(view.match_coverage_table || [], [
    { key: "match", label: "比赛" },
    { key: "api_football", label: "API-Football" },
    { key: "the_odds_api", label: "海外赔率" },
    { key: "injuries", label: "伤停" },
    { key: "lineup", label: "首发" },
    { key: "weather", label: "天气" },
    { key: "news", label: "新闻" },
    { key: "match_confidence", label: "匹配置信度" },
    { key: "message_zh", label: "说明" },
  ]);
  qs("#reliabilityGuide").innerHTML = C.list([
    view.reliability_summary?.decision_guide_zh || "先看 Sporttery 主数据，再看第三方匹配和缺失情报。",
    "The Odds API 是海外赔率参考，不替代中国竞彩官方赔率。",
    "天气需要球场/城市坐标，未接入时保持未知。",
  ]);
}

function renderDataSources(view) {
  if (!qs("#freeDataSources")) return;
  state.dataSourcesView = view;
  const rows = (view.sources || []).map((item) => ({
    name: item.name,
    cost_zh: item.cost_zh,
    role_zh: item.role_zh,
    status: sourceStatusLabel(item.status),
    masked_key: item.masked_key || (item.needs_api_key ? "未配置" : "不需要"),
    default_behavior_zh: item.default_behavior_zh,
    reliability_note_zh: item.reliability_note_zh,
    env_var: item.env_var || "不需要",
    setup_action_zh: item.setup_action_zh,
    signup_url: item.signup_url || "不需要",
    docs_url: item.docs_url || "不需要",
  }));
  const secretConfig = view.secret_config || {};
  const keyRows = secretConfig.keys || [];
  qs("#freeDataSources").innerHTML = [
    C.list([
      view.summary_zh || "免费优先数据源。",
      view.daily_low_frequency_fit_zh || "低频使用可先用免费源。",
      view.credential_policy_zh || "账号和 key 由用户自己保管。",
      view.next_registration_zh || "优先继续使用 Sporttery。",
    ]),
    `<details class="secretConfigBox">
      <summary>本地 Key 安全配置</summary>
      <div class="secretConfigGrid">
        <label>API-Football key<input id="apiFootballKeyInput" type="password" autocomplete="off" placeholder="粘贴后保存到本机 .env.local"></label>
        <label>The Odds API key<input id="theOddsKeyInput" type="password" autocomplete="off" placeholder="粘贴后保存到本机 .env.local"></label>
      </div>
      <div class="inlineActions">
        <button id="saveLocalSecretsBtn" class="secondary">保存到本机配置</button>
        <button id="verifyApiFootballBtn" class="ghost">验证 API-Football</button>
        <button id="verifyTheOddsBtn" class="ghost">验证 The Odds API</button>
      </div>
      <p class="mutedLine">保存位置：${C.escapeHtml(secretConfig.env_path || ".env.local")}。页面不会回显完整 key；空输入会保持原配置。</p>
      <div id="secretConfigStatus">${C.table(keyRows, [
        { key: "label", label: "服务" },
        { key: "configured", label: "已配置" },
        { key: "masked", label: "掩码" },
        { key: "source", label: "来源" },
      ])}</div>
      <div id="thirdPartyVerifyResult" class="noteBox"></div>
    </details>`,
    C.table(rows, [
      { key: "name", label: "数据源" },
      { key: "cost_zh", label: "成本" },
      { key: "role_zh", label: "用途" },
      { key: "status", label: "状态" },
      { key: "masked_key", label: "key 状态" },
      { key: "setup_action_zh", label: "你要做什么" },
      { key: "default_behavior_zh", label: "默认行为" },
      { key: "reliability_note_zh", label: "可靠性说明" },
      { key: "env_var", label: "本地配置" },
      { key: "signup_url", label: "注册/官网" },
      { key: "docs_url", label: "文档" },
    ]),
    `<h4>推荐顺序</h4>${C.list(view.recommended_order || [])}`,
  ].join("");
  bindSecretConfigButtons();
}

function sourceStatusLabel(status) {
  return {
    enabled: "已启用",
    configured: "已配置",
    not_configured: "未配置",
    available_optional: "可选免费源",
    available_offline: "可离线导入",
  }[status] || status || "unknown";
}

function bindSecretConfigButtons() {
  bind("#saveLocalSecretsBtn", "click", saveLocalSecrets);
  bind("#verifyApiFootballBtn", "click", () => verifyThirdPartySource("api_football"));
  bind("#verifyTheOddsBtn", "click", () => verifyThirdPartySource("the_odds_api"));
}

async function saveLocalSecrets() {
  const body = {
    JC_EDGE_API_FOOTBALL_KEY: value("#apiFootballKeyInput"),
    JC_EDGE_THE_ODDS_API_KEY: value("#theOddsKeyInput"),
  };
  const payload = await postJson("/api/config/local-env", body, "保存本地 key");
  if (payload.ok) {
    if (qs("#apiFootballKeyInput")) qs("#apiFootballKeyInput").value = "";
    if (qs("#theOddsKeyInput")) qs("#theOddsKeyInput").value = "";
    await refreshDataSourcesOnly();
  }
}

async function refreshDataSourcesOnly() {
  const sourcesPayload = await request("/api/view/data-sources", {}, "刷新数据源配置状态");
  if (sourcesPayload.ok) renderDataSources(sourcesPayload.data);
}

async function verifyThirdPartySource(source) {
  const payload = await request("/api/data-sources/verify", { source }, `验证 ${source}`);
  const data = payload.data || {};
  if (qs("#thirdPartyVerifyResult")) {
    qs("#thirdPartyVerifyResult").innerHTML = C.list([
      `状态：${data.status || "unknown"}`,
      data.message_zh || "暂无说明。",
      data.masked_key ? `key：${data.masked_key}` : "key：未显示完整值",
      data.requests_remaining ? `剩余额度：${data.requests_remaining}` : "",
      data.requests_used ? `已用额度：${data.requests_used}` : "",
      data.host ? `接口：${data.host}` : "",
    ].filter(Boolean));
  }
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
    { key: "confidence", label: "观察可信度" }, { key: "confidence_label_zh", label: "评级" }, { key: "recommended_action_zh", label: "建议动作" },
    { key: "paper_stake", label: "纸面投入" }, { key: "risk_level", label: "风险" }, { key: "reason", label: "原因" },
  ];
  qs("#optimizerSingles").innerHTML = tableOrEmpty(view.singles_table || [], selectedCols);
  qs("#optimizerParlay2").innerHTML = tableOrEmpty(view.parlay_2x1_table || [], selectedCols, "当前没有 2串1 入选。不要因为赔率高就盲目组合。");
  qs("#optimizerParlay3").innerHTML = tableOrEmpty(view.parlay_3x1_table || [], selectedCols, "当前没有 3串1 入选。3串1 风险最高。 ");
  const rankCols = [
    { key: "type", label: "类型" }, { key: "match", label: "候选" }, { key: "legs", label: "组成" }, { key: "odds", label: "赔率" },
    { key: "model_prob", label: "模型概率" }, { key: "market_prob", label: "市场概率" }, { key: "ev", label: "EV" }, { key: "edge", label: "Edge" },
    { key: "confidence", label: "观察可信度" }, { key: "confidence_label_zh", label: "评级" }, { key: "recommended_action_zh", label: "建议动作" },
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
  qs("#scoreGoalsNotes").innerHTML = [
    C.table(view.reliability_notes || [], [
      { key: "type", label: "玩法" },
      { key: "reliability", label: "可靠性" },
      { key: "usage", label: "适合用途" },
      { key: "why", label: "原因" },
      { key: "top_example", label: "当前示例" },
    ]),
    C.list([...(view.risk_notes || []), ...((view.missing_signals || []).map((x) => `缺失情报：${x}`))]),
  ].join("");
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
  const replayReadiness = view.replay_readiness_summary || {};
  const replayReadinessHtml = [
    `<h4>CSV 复盘准备度</h4>`,
    C.cards([
      { label: "准备度", value: replayReadiness.label || "unknown", help: replayReadiness.summary_zh || "等待预检。" },
      { label: "评分", value: replayReadiness.score ?? "N/A", help: "基于字段、赔率覆盖、样本量、回测和校准准备度。" },
      { label: "校准准备", value: replayReadiness.calibration_status || "pending", help: replayReadiness.calibration_note_zh || "校准只用于诊断概率偏差。" },
    ]),
    C.list([
      replayReadiness.summary_zh || "预检后显示 CSV 是否可以进入完整复盘。",
      replayReadiness.next_action_zh || "字段预检通过后，再执行完整 workflow。",
      replayReadiness.calibration_note_zh || "校准文件不保证未来表现。",
    ]),
    C.table((replayReadiness.proof_points || []).map((item) => ({ proof: item })), [{ key: "proof", label: "准备度证据" }]),
  ].join("");
  qs("#userWorkflowReadinessCards").innerHTML = C.cards(view.readiness_cards || []) + `<div class="subPanel">${replayReadinessHtml}</div>`;
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
bind("#credibilityBtn", "click", loadCredibility);
bind("#missingInfoBtn", "click", loadMissingInfo);
bind("#signalsPreviewBtn", "click", previewSignals);
bind("#bestParlayBtn", "click", loadBestParlay);
bind("#traderReviewBtn", "click", loadTraderReview);
bind("#optimizerBtn", "click", () => runOptimizer(false));
bind("#optimizerCompareBtn", "click", () => runOptimizer(true));
bind("#scoreGoalsBtn", "click", loadScoreGoals);
bind("#operationBtn", "click", runOperation);
bind("#importBtn", "click", previewImport);
bind("#qaBtn", "click", runQa);

renderRaw({});
loadToday();

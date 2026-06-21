const C = window.FootballComponents;

const state = {
  lastRaw: {},
  todayView: null,
  signalExplainView: null,
  reliabilityView: null,
  credibilityView: null,
  proScoreView: null,
  missingInfoView: null,
  signalsPreviewView: null,
  bestParlayView: null,
  traderReviewView: null,
  learningView: null,
  matchesView: null,
  optimizerView: null,
  scoreGoalsView: null,
  operationView: null,
  importView: null,
  qaView: null,
  dataSourcesView: null,
  autoAiResearchKey: "",
  latestAiResearch: null,
  latestResearchArchive: null,
  lastLearningImpact: null,
  lastLearningPack: null,
  lastWorkflowAction: null,
  workflowActionHistory: [],
  currentWorkflowScore: null,
  currentWorkflowBottleneck: null,
  currentWorkflowItems: [],
  currentWorkflowTarget: null,
  todayProgressTimer: null,
  todayProgressStartedAt: 0,
  optimizerInlineProgressTimer: null,
  optimizerInlineProgressStartedAt: 0,
  optimizerProgressTimer: null,
  optimizerProgressStartedAt: 0,
};

const __virtualNodeCache = Object.create(null);

function createVirtualNode(nodeId = "") {
  const style = {};
  return {
    innerHTML: "",
    textContent: "",
    hidden: false,
    id: nodeId || "",
    className: "",
    value: "",
    style,
    dataset: {},
    classList: {
      add() {},
      remove() {},
      toggle() { return false; },
      contains() { return false; },
    },
    setAttribute() {},
    removeAttribute() {},
    getAttribute() { return null; },
    hasAttribute() { return false; },
    addEventListener() {},
    removeEventListener() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
    append() {},
    appendChild() {},
    insertAdjacentHTML() {},
    focus() {},
    scrollIntoView() {},
    cloneNode() { return createVirtualNode(nodeId); },
  };
}

function normalizeSelector(selector) {
  return String(selector || "").trim();
}

function qs(selector) {
  const target = normalizeSelector(selector);
  if (!target) return null;
  const found = document.querySelector(target);
  if (found) return found;
  if (!__virtualNodeCache[target]) {
    const node = createVirtualNode(target.replace(/^#/, ""));
    __virtualNodeCache[target] = node;
  }
  return __virtualNodeCache[target];
}

function setNodeHtml(selector, html) {
  const node = qs(selector);
  if (node) node.innerHTML = html || "";
}

function setNodeText(selector, text) {
  const node = qs(selector);
  if (node) node.textContent = text === undefined ? "" : String(text);
}

function setTodayQuickActionStatus(text) {
  const target = qs("#quickActionStatus");
  if (target) target.textContent = text || "当前：等待下一可售比赛扫描结果";
}

function safeClearNode(selector) {
  const node = qs(selector);
  if (node) node.innerHTML = "";
}

function startTodayOptimizerInlineProgress() {
  const host = qs("#todayOptimizerProgressHost");
  if (!host) return;
  state.optimizerInlineProgressStartedAt = Date.now();
  if (state.optimizerInlineProgressTimer) window.clearInterval(state.optimizerInlineProgressTimer);
  host.innerHTML = optimizerFlowProgressMarkup(0);
  state.optimizerInlineProgressTimer = window.setInterval(() => {
    const elapsed = Date.now() - state.optimizerInlineProgressStartedAt;
    const percent = Math.min(98, 6 + Math.floor(elapsed / 900));
    updateOptimizerInlineProgress(percent);
  }, 500);
}

function stopTodayOptimizerInlineProgress(successLabel = "完成") {
  if (state.optimizerInlineProgressTimer) {
    window.clearInterval(state.optimizerInlineProgressTimer);
    state.optimizerInlineProgressTimer = null;
  }
  const host = qs("#todayOptimizerProgressHost");
  if (!host) return;
  host.innerHTML = `
    <div id="todayOptimizerInlineProgress" class="todayLoadingProgress isNova isDoneState">
      <div class="todayProgressHeader">
        <span>OPTIMIZER</span>
        <strong>${C.escapeHtml(successLabel)}</strong>
        <em>100%</em>
      </div>
      <div class="todayProgressNovaWrap" aria-hidden="true">
        <div class="todayProgressNovaRail">
          <span class="todayProgressNovaGlow"></span>
          <span class="todayProgressNovaFill" style="--progress:100%"></span>
          <span class="todayProgressNovaShimmer"></span>
          <i class="todayProgressNovaDot" style="--dot-angle:0deg"></i>
          <i class="todayProgressNovaDot" style="--dot-angle:90deg"></i>
          <i class="todayProgressNovaDot" style="--dot-angle:180deg"></i>
          <i class="todayProgressNovaDot" style="--dot-angle:270deg"></i>
        </div>
      </div>
      <div class="todayProgressSteps todayProgressStepsNova" aria-label="赛前优化进度">
        ${OPTIMIZER_LOADING_STEPS.map((_, index) => `<b class="isDone" data-step="${index}">${index + 1}</b>`).join("")}
      </div>
      <p class="todayProgressDetail">已生成赛前观察摘要，可继续查看候选和拒绝原因。</p>
    </div>
  `;
  setTimeout(() => {
    safeClearNode("#todayOptimizerProgressHost");
  }, 900);
}

function abortTodayOptimizerInlineProgress(message = "未完成") {
  if (state.optimizerInlineProgressTimer) {
    window.clearInterval(state.optimizerInlineProgressTimer);
    state.optimizerInlineProgressTimer = null;
  }
  setNodeHtml("#todayOptimizerProgressHost", `
    <div id="todayOptimizerInlineProgress" class="todayLoadingProgress isNova">
      <div class="todayProgressHeader">
        <span>OPTIMIZER</span>
        <strong>${C.escapeHtml(message)}</strong>
        <em>--</em>
      </div>
      <p class="todayProgressDetail">本次未完整产出，可先查看赛前观察和情报覆盖，稍后再试。</p>
    </div>
  `);
  setTimeout(() => {
    safeClearNode("#todayOptimizerProgressHost");
  }, 1400);
}

function optimizerFlowProgressMarkup(stepIndex = 0) {
  const safeIndex = Math.max(0, Math.min(stepIndex, OPTIMIZER_LOADING_STEPS.length - 1));
  const current = OPTIMIZER_LOADING_STEPS[safeIndex];
  const visibleSteps = OPTIMIZER_LOADING_STEPS.slice(0, 7);
  return `
    <div id="todayOptimizerInlineProgress" class="todayLoadingProgress isNova" style="--progress:${current.percent}%">
      <div class="todayProgressHeader">
        <span>OPTIMIZER</span>
        <strong>${C.escapeHtml(current.label)}</strong>
        <em>${C.escapeHtml(String(current.percent))}%</em>
      </div>
      <div class="todayProgressNovaWrap" aria-hidden="true">
        <div class="todayProgressNovaRail">
          <span class="todayProgressNovaGlow"></span>
          <span class="todayProgressNovaFill" style="--progress:${current.percent}%"></span>
          <span class="todayProgressNovaShimmer"></span>
          ${[0, 90, 180, 270].map((angle) => `<i class="todayProgressNovaDot" style="--dot-angle:${angle}deg"></i>`).join("")}
        </div>
      </div>
      <div class="todayProgressSteps todayProgressStepsNova" aria-label="赛前优化进度">
        ${visibleSteps.map((step, index) => `
          <b class="${index < safeIndex ? "isDone" : index === safeIndex ? "isActive" : ""}" data-index="${index}">
            <em>${index + 1}</em>
            ${C.escapeHtml(step.label)}
          </b>
        `).join("")}
      </div>
      <p class="todayProgressDetail">${C.escapeHtml(current.detail)}</p>
    </div>
  `;
}

function updateOptimizerInlineProgress(percent) {
  const host = qs("#todayOptimizerInlineProgress");
  if (!host) return;
  const targetPercent = Math.min(98, Math.max(0, Number(percent) || 0));
  let stepIndex = 0;
  for (let i = 0; i < OPTIMIZER_LOADING_STEPS.length; i += 1) {
    if (targetPercent >= OPTIMIZER_LOADING_STEPS[i].percent) stepIndex = i;
  }
  const step = OPTIMIZER_LOADING_STEPS[stepIndex] || OPTIMIZER_LOADING_STEPS[0];
  host.style.setProperty("--progress", `${targetPercent}%`);
  const fill = host.querySelector(".todayProgressNovaFill");
  if (fill) fill.style.setProperty("--progress", `${targetPercent}%`);
  const strong = host.querySelector(".todayProgressHeader strong");
  const em = host.querySelector(".todayProgressHeader em");
  const detail = host.querySelector(".todayProgressDetail");
  if (strong) strong.textContent = step.label || "运行中";
  if (em) em.textContent = `${Math.round(targetPercent)}%`;
  if (detail) detail.textContent = step.detail || "正在生成候选池。";
  const stepNodes = host.querySelectorAll(".todayProgressSteps b");
  stepNodes.forEach((node, index) => {
    node.classList.toggle("isDone", index < stepIndex);
    node.classList.toggle("isActive", index === stepIndex);
  });
}

async function loadProfessionalModelScore() {
  const payload = await request("/api/audit/professional-model-score", {
    provider: providerParam(),
    date: currentDateParam(),
    bankroll: bankrollParam(),
    risk_profile: riskProfileParam(),
    external_signals: externalSignalsParam(),
  }, "模型体检", 24000);
  if (payload.ok) {
    state.proScoreView = payload.data;
    renderProfessionalModelScoreAudit(payload.data);
  } else {
    renderProfessionalModelScoreAudit({
      professional_model_score: {},
      warnings: payload.warnings || ["模型体检暂未返回。"],
      error_zh: payload.error?.message || "模型体检暂未返回。",
    });
  }
}

function renderProfessionalModelScoreAudit(view = {}) {
  const score = view.professional_model_score || {};
  const roadmap = score.roadmap_to_95 || {};
  const evidence = score.learning_evidence || {};
  const cards = [
    { label: "职业模型分", value: score.score == null ? "N/A" : `${score.score}/${score.ceiling_score || 95}`, help: score.summary_zh || "分数越高，说明数据、校准、CLV 和纪律越接近职业模型标准。" },
    { label: "理论上限", value: score.ceiling_score == null ? "N/A" : `${score.ceiling_score}`, help: "如果真实数据、赛后样本或收盘赔率不足，上限会被主动压低。" },
    { label: "评级", value: score.grade || "N/A", help: score.label_zh || "评级反映当前模型可信层级，不是赛果承诺。" },
    { label: "已结算样本", value: evidence.settled_count ?? "0", help: "长期样本越多，Brier / Log Loss 才越有判断力。" },
    { label: "CLV 样本", value: evidence.clv_settled_count ?? "0", help: "CLV 用来检查赛前价格是否跑赢市场终盘。" },
    { label: "AI假设复盘", value: evidence.ai_hypothesis_reviewed_count ?? "0", help: evidence.ai_hypothesis_summary_zh || "AI/DS 赛前摘要必须被赛后结果审计，不能只看 token。" },
    { label: "下一步增益", value: `${roadmap.estimated_score_gain || 0}`, help: roadmap.priority_zh || "优先补最能拉升模型上限的短板。" },
  ];
  setNodeHtml("#proScoreCards", C.cards(cards));
  setNodeHtml("#proScorePanelHost", professionalModelScorePanel(score));
  setNodeHtml("#proScoreGapRadar", professionalScoreGapRadar(score.score_gap_radar || []));
  setNodeHtml("#proScoreLearningBridge", professionalScoreLearningBridge(score, view));
  setNodeHtml("#proScoreAiQuality", professionalScoreAiQualityPanel(score.ai_research_quality || {}));
  setNodeHtml("#proScoreTrend", professionalScoreTrendPanel(score.score_trend || {}));
  setNodeHtml("#proScoreEvidenceGates", professionalScoreEvidenceGates(score.evidence_requirements || {}));
  const actions = roadmap.next_best_actions || [];
  const items = roadmap.items || score.missing_to_95 || [];
  const roadmapHtml = `
    <div class="proScoreActionGrid">
      ${actions.slice(0, 5).map((item, index) => `
        <article>
          <span>${index + 1}</span>
          <strong>${C.escapeHtml(item.title_zh || item.key || "改进项")}</strong>
          <p>${C.escapeHtml(item.action_zh || item.detail_zh || item.reason_zh || "继续补齐证据。")}</p>
          <em>${C.escapeHtml(item.estimated_score_gain == null ? "增益待估" : `预计 +${item.estimated_score_gain} 分`)}</em>
        </article>
      `).join("") || `<p>暂无路线图。先积累赛后样本和收盘赔率。</p>`}
    </div>
    ${items.length ? `<details class="detailDrawer"><summary>查看所有缺口</summary>${C.list(items.map((item) => item.message_zh || item.detail_zh || item.title_zh || String(item)))}</details>` : ""}
  `;
  setNodeHtml("#proScoreRoadmap", roadmapHtml);
  const benchmark = score.industry_benchmark_zh || view.industry_benchmark_zh || [];
  setNodeHtml("#proScoreBenchmark", benchmark.length ? C.table(benchmark, [
    { key: "label_zh", label: "基准项" },
    { key: "status_zh", label: "状态" },
    { key: "message_zh", label: "说明" },
  ]) : `<div class="emptyState">暂无行业基准明细。</div>`);
}

function professionalScoreGapRadar(rows = []) {
  if (!rows.length) return `<div class="emptyState">暂无 95 分缺口雷达。先生成模型体检。</div>`;
  const topRows = rows.slice(0, 9);
  return `
    <section class="proScoreGapRadar">
      <div class="proScoreGapRadarHead">
        <span>95 GAP RADAR</span>
        <strong>离高分还差什么</strong>
        <p>不是盲目加模型，而是看哪一块最拖分：数据源、赔率转换、校准、CLV、玩法复盘、冷门偏差、情报覆盖、组合纪律和赛后学习。</p>
      </div>
      <div class="proScoreGapRadarGrid">
        ${topRows.map((row) => {
          const score = Math.max(0, Math.min(100, Number(row.score || 0)));
          const target = Math.max(score, Math.min(100, Number(row.target_score || 82)));
          const gap = Math.max(0, Number(row.gap_to_target || 0));
          return `
            <article data-impact="${C.escapeHtml(row.impact_level || "low")}" style="--score:${score}%;--target:${target}%">
              <header>
                <span>${C.escapeHtml(row.label_zh || row.key || "缺口")}</span>
                <strong>${C.escapeHtml(String(score))}</strong>
              </header>
              <div class="gapRadarTrack">
                <i></i>
                <b></b>
              </div>
              <p>${C.escapeHtml(row.impact_zh || "继续观察。")}</p>
              <em>目标 ${C.escapeHtml(String(row.target_score ?? "N/A"))} · 缺口 ${C.escapeHtml(String(gap))} · 加权缺口 ${C.escapeHtml(String(row.weighted_gap ?? "N/A"))}</em>
              <small>${C.escapeHtml(row.next_step_zh || row.detail_zh || "继续补证据。")}</small>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function professionalScoreLearningBridge(score = {}, view = {}) {
  const evidence = score.learning_evidence || {};
  const roadmap = score.roadmap_to_95 || {};
  const requirements = score.evidence_requirements || {};
  const progress = requirements.sample_progress || {};
  const recentImpact = state.lastLearningImpact || {};
  const actions = roadmap.next_best_actions || [];
  const scoreValue = score.score == null ? "N/A" : `${score.score}/${score.ceiling_score || 95}`;
  const settled = Number(evidence.settled_count || 0);
  const clvSettled = Number(evidence.clv_settled_count || 0);
  const aiReviewed = Number(evidence.ai_hypothesis_reviewed_count || 0);
  const aiSupported = Number(evidence.ai_hypothesis_supported_count || 0);
  const aiFailed = Number(evidence.ai_hypothesis_failed_count || 0);
  const aiSupportRate = evidence.ai_hypothesis_supported_rate == null ? "暂无" : fmtPct(evidence.ai_hypothesis_supported_rate);
  const playBest = evidence.play_type_best || {};
  const playWeakest = evidence.play_type_weakest || {};
  const playSummary = evidence.play_type_summary_zh || "玩法复盘样本不足，暂不能证明哪类玩法长期更可靠。";
  const playBiasRadar = (score.score_gap_radar || []).find((row) => row.key === "play_bias_control") || {};
  const primaryGap = actions[0]?.title_zh || (clvSettled < 20 ? "补收盘赔率 CLV" : settled < 30 ? "补赛后结果样本" : "补真实情报覆盖");
  const primaryAction = actions[0]?.action_zh || "保存赛前观察，赛后回填比分和收盘赔率，让模型用真实样本证明自己。";
  return `
    <div class="proScoreLearningHero">
      <div>
        <span>当前模型体检</span>
        <strong>${C.escapeHtml(scoreValue)}</strong>
        <p>${C.escapeHtml(score.summary_zh || "职业模型分会被真实数据、赛后样本、CLV 和情报覆盖共同限制。")}</p>
      </div>
      <div>
        <span>第一优先级</span>
        <strong>${C.escapeHtml(primaryGap)}</strong>
        <p>${C.escapeHtml(primaryAction)}</p>
      </div>
    </div>
    <div class="proScoreLearningSteps">
      <article>
        <b>1</b>
        <strong>固定赛前观察</strong>
        <p>把今天的单关、2串1、3串1纸面候选和拒绝原因保存下来，避免赛后回忆偏差。</p>
        <button type="button" class="secondary" data-proscore-action="snapshot">保存今日观察</button>
      </article>
      <article>
        <b>2</b>
        <strong>准备赛后复盘</strong>
        <p>自动生成比分模板和收盘赔率模板。长期靠 Brier、Log Loss、ROI、CLV 判断模型有没有进步。</p>
        <button type="button" class="secondary" data-proscore-action="pack">准备复盘材料</button>
      </article>
      <article>
        <b>3</b>
        <strong>填写赛果与收盘赔率</strong>
        <p>赛后补比分；如果能补收盘赔率，就能检查是否跑赢市场终盘，这是接近职业模型的硬指标。</p>
        <button type="button" class="primary" data-proscore-action="results">去填写赛果</button>
      </article>
    </div>
    <div class="proScoreLearningEvidence">
      <span>已结算样本：${C.escapeHtml(String(settled))}</span>
      <span>CLV 样本：${C.escapeHtml(String(clvSettled))}</span>
      <span>AI 假设复盘：${C.escapeHtml(String(aiReviewed))}</span>
      <span>AI 支持率：${C.escapeHtml(aiSupportRate)}</span>
      <span>玩法复盘：${C.escapeHtml(String(evidence.play_type_reliable_count || 0))} 类可参考</span>
      <span>数据源：${C.escapeHtml(view.provider_used || "auto")}</span>
      <span>目标：先让样本闭环稳定，再调模型权重</span>
    </div>
    <div class="proScorePlayTypeBridge">
      <strong>玩法是否真的有效？</strong>
      <p>${C.escapeHtml(playSummary)}</p>
      <div>
        <span>最佳：${C.escapeHtml(playBest.label_zh || "待累计")} · ROI ${C.escapeHtml(fmtSignedPct(playBest.paper_roi))}</span>
        <span>最弱：${C.escapeHtml(playWeakest.label_zh || "待累计")} · ROI ${C.escapeHtml(fmtSignedPct(playWeakest.paper_roi))}</span>
        <span>弱玩法：${C.escapeHtml(String(evidence.play_type_weak_count || 0))}</span>
        <span>偏置纠偏：${C.escapeHtml(playBiasRadar.score == null ? "待检查" : `${playBiasRadar.score}/${playBiasRadar.target_score || 84}`)}</span>
      </div>
      <em>${C.escapeHtml(playBiasRadar.next_step_zh || "如果某玩法长期 ROI、Brier 或命中率偏弱，优化器会自动降权，不再机械重复同一玩法。")}</em>
    </div>
    <div class="proScoreAiReviewBridge">
      <strong>AI/DS 研究怎么证明有用？</strong>
      <p>${C.escapeHtml(evidence.ai_hypothesis_summary_zh || "赛后保存学习后，系统会把 AI 当时的单关、2串1、3串1、被拒组合解释逐条复盘。")}</p>
      <div>
        <span>支持 ${C.escapeHtml(String(aiSupported))}</span>
        <span>失败 ${C.escapeHtml(String(aiFailed))}</span>
        <span>待累计 ${C.escapeHtml(String(Math.max(0, aiReviewed ? aiReviewed - aiSupported - aiFailed : 0)))}</span>
      </div>
      <em>只有长期“假设被支持 + CLV 不拖后腿”，AI 摘要才会真正提高职业模型证据分。</em>
    </div>
    <div class="proScoreSampleImpact">
      <div>
        <span>下一档：${C.escapeHtml(progress.gate_level ? `${progress.gate_level} · ${progress.gate_label_zh || ""}` : "待计算")}</span>
        <strong>${C.escapeHtml(progress.next_action_zh || "继续补赛后结果和收盘赔率。")}</strong>
      </div>
      <div class="proScoreSampleMeters">
        <label>
          <b>赛后结果</b>
          <i style="--score:${Number(progress.settled_progress_pct || 0)}%"></i>
          <em>${C.escapeHtml(String(progress.settled_current ?? settled))}/${C.escapeHtml(String(progress.settled_target || "N/A"))}</em>
        </label>
        <label>
          <b>CLV</b>
          <i style="--score:${Number(progress.clv_progress_pct || 0)}%"></i>
          <em>${C.escapeHtml(String(progress.clv_current ?? clvSettled))}/${C.escapeHtml(String(progress.clv_target || "N/A"))}</em>
        </label>
      </div>
      ${recentImpact.saved ? `
        <p class="proScoreRecentImpact">
          ${C.escapeHtml(`刚刚新增：${recentImpact.summary || recentImpact.detail || "赛后学习样本"}。${recentImpact.next || "刷新模型体检后会重新计算门槛进度。"}`)}
        </p>
      ` : ""}
    </div>
  `;
}

function professionalScoreEvidenceGates(requirements = {}) {
  const rows = requirements.rows || [];
  if (!rows.length) return `<div class="emptyState">暂无证据门槛。先生成模型体检。</div>`;
  return `
    <div class="proScoreGateSummary">
      <strong>${C.escapeHtml(requirements.summary_zh || "下一道证据门槛待计算。")}</strong>
      <p>${C.escapeHtml(requirements.note_zh || "职业级模型需要长期赛后样本、CLV 和情报覆盖。")}</p>
    </div>
    <div class="proScoreGateGrid">
      ${rows.map((row) => `
        <article class="${row.passed ? "isPassed" : "isBlocked"}">
          <header>
            <span>${C.escapeHtml(String(row.level))}</span>
            <div>
              <strong>${C.escapeHtml(row.label_zh || "证据门槛")}</strong>
              <em>${C.escapeHtml(row.status_zh || "未达标")}</em>
            </div>
          </header>
          <p>${C.escapeHtml(row.message_zh || "")}</p>
          <div class="proScoreGateChecks">
            ${(row.checks || []).slice(0, 5).map((check) => `
              <i class="${check.passed ? "pass" : "fail"}">
                <b>${C.escapeHtml(check.label_zh || check.key || "检查项")}</b>
                <span>${C.escapeHtml(String(check.current ?? "N/A"))} / ${C.escapeHtml(String(check.target ?? "N/A"))}</span>
              </i>
            `).join("")}
          </div>
        </article>
      `).join("")}
    </div>
  `;
}

function professionalScoreTrendPanel(trend = {}) {
  const rows = trend.rows || [];
  if (!rows.length) {
    return `<div class="emptyState">暂无 7 天 / 30 天模型分趋势。先保存赛后学习样本。</div>`;
  }
  const directionLabel = trend.direction === "up" ? "近期改善" : trend.direction === "down" ? "近期走弱" : "稳定累计";
  return `
    <div class="proScoreTrendHero" data-direction="${C.escapeHtml(trend.direction || "flat")}">
      <span>${C.escapeHtml(directionLabel)}</span>
      <strong>${C.escapeHtml(trend.summary_zh || "继续累计样本。")}</strong>
      <p>趋势分只用于判断模型学习质量，不代表任何单场结果。</p>
    </div>
    <div class="proScoreTrendGrid">
      ${rows.map((row) => `
        <article>
          <header>
            <span>${C.escapeHtml(row.label_zh || row.window || "窗口")}</span>
            <strong>${C.escapeHtml(String(row.estimated_score ?? "N/A"))}</strong>
          </header>
          <div class="miniMeter"><i style="--score:${Math.max(0, Math.min(100, Number(row.estimated_score || 0)))}%"></i></div>
          <div class="trendMetrics">
            <b>样本 ${C.escapeHtml(String(row.settled_count ?? 0))}</b>
            <b>CLV ${C.escapeHtml(String(row.clv_settled_count ?? 0))}</b>
            <b>Brier ${C.escapeHtml(row.brier_score == null ? "N/A" : String(row.brier_score))}</b>
            <b>ROI ${C.escapeHtml(fmtSignedPct(row.paper_roi))}</b>
          </div>
          <p>${C.escapeHtml(row.message_zh || "")}</p>
        </article>
      `).join("")}
    </div>
  `;
}

function professionalScoreAiQualityPanel(ai = {}) {
  if (!Object.keys(ai).length) return `<div class="emptyState">暂无 AI 研究质量记录。先生成今日观察或自动研究。</div>`;
  const cards = [
    { label: "AI研究分", value: ai.score == null ? "N/A" : `${ai.score}/100`, help: ai.summary_zh || "AI 只做解释、质检和复盘，不直接改概率。" },
    { label: "DS状态", value: ai.ds_completed ? "已完成" : "未完成", help: "DS 未完成时自动回退本地摘要。" },
    { label: "Token", value: ai.token_total || "N/A", help: "用于对账 AI 研究是否真实参与。" },
    { label: "结构化笔记", value: ai.structured_note_count ?? 0, help: "结构化笔记越完整，赛后越能验证 AI 判断质量。" },
    { label: "可验证假设", value: ai.verifiable_hypothesis_count ?? 0, help: "每条假设都应该能用赛果、CLV 或被拒组合复盘验证。" },
    { label: "赛后已复盘", value: ai.reviewed_hypothesis_count ?? 0, help: "不是 AI 写了就算，必须回填赛果后检验。" },
    { label: "假设支持率", value: ai.supported_hypothesis_rate == null ? "暂无" : fmtPct(ai.supported_hypothesis_rate), help: "支持率低时，AI 摘要只作解释，不提高模型自信。" },
    { label: "研究档案", value: ai.archive_saved ? "已保存" : "未确认", help: "未归档的 AI 摘要无法稳定进入学习闭环。" },
  ];
  const reviewed = Number(ai.reviewed_hypothesis_count || 0);
  const supported = Number(ai.supported_hypothesis_count || 0);
  const failed = Number(ai.failed_hypothesis_count || 0);
  const pending = Math.max(0, Number(ai.verifiable_hypothesis_count || 0) - reviewed);
  const hypotheses = ai.verifiable_hypotheses || [];
  return `
    <div class="proScoreAiQuality">
      ${C.cards(cards)}
      <div class="proScoreAiReviewPanel">
        <div>
          <span>POSTMATCH AI AUDIT</span>
          <strong>${reviewed ? `已复盘 ${C.escapeHtml(String(reviewed))} 条 AI 假设` : "等待赛后验证"}</strong>
          <p>${C.escapeHtml(reviewed ? "AI 研究质量现在会读取赛后支持/失败记录，而不是只看 token 消耗。" : "保存赛后学习后，这里会显示 DS/本地 AI 当时判断是否被赛果和 CLV 支持。")}</p>
        </div>
        <div class="aiReviewPills">
          <b>支持 ${C.escapeHtml(String(supported))}</b>
          <b>失败 ${C.escapeHtml(String(failed))}</b>
          <b>待验证 ${C.escapeHtml(String(pending))}</b>
        </div>
      </div>
      ${hypotheses.length ? `
        <details class="detailDrawer" open>
          <summary>查看可验证假设</summary>
          ${C.table(hypotheses, [
            { key: "label_zh", label: "类型" },
            { key: "target", label: "目标" },
            { key: "hypothesis_zh", label: "AI假设" },
            { key: "validation_rule_zh", label: "赛后验证" },
          ])}
        </details>
      ` : ""}
      <div class="noteBox">
        ${C.list([
          ai.summary_zh || "AI 研究质量待评估。",
          ...(ai.evidence_zh || []),
          ...(ai.issues_zh || []),
          ai.next_step_zh || "让 AI 输出可复盘假设，而不是泛泛解释。",
          ai.disclaimer || "AI 研究不改写概率、不绕过门控。",
        ])}
      </div>
    </div>
  `;
}

document.addEventListener("click", (event) => {
  const target = event.target && event.target.closest ? event.target.closest("#proScoreBtn, #tab-proscore") : null;
  if (!target) return;
  window.setTimeout(() => loadProfessionalModelScore(), 0);
});

document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest("[data-proscore-action]") : null;
  if (!button) return;
  event.preventDefault();
  const action = button.dataset.proscoreAction;
  if (action === "snapshot") {
    saveLearningObservationSnapshot();
    return;
  }
  if (action === "pack") {
    prepareDailyLearningPack();
    return;
  }
  if (action === "results") {
    jumpToView("learning");
    renderLearningQuickForm();
  }
});

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
function providerName(provider) {
  const text = String(provider || "auto").toLowerCase();
  if (text.includes("sporttery")) return "竞彩足球真实数据";
  if (text.includes("mock")) return "示例数据";
  if (text.includes("cache")) return "缓存数据";
  if (text.includes("auto")) return "自动数据源";
  return provider || "自动数据源";
}

function endpoint(path, params = {}) {
  const url = new URL(`${apiBase()}${path}`);
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== "") url.searchParams.set(key, val);
  });
  return url.toString();
}

async function request(path, params = {}, label = "请求", timeoutMs = 20000) {
  setStatus("Loading", `${label}进行中`);
  const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
  const timer = controller ? window.setTimeout(() => controller.abort(), timeoutMs) : null;
  try {
    const response = await fetch(endpoint(path, params), controller ? { signal: controller.signal } : undefined);
    const payload = await response.json();
    state.lastRaw = payload;
    renderRaw(payload);
    renderWarnings(payload.warnings || payload.data?.warnings || []);
    setStatus(payload.ok ? "OK" : "Error", label);
    return payload;
  } catch (error) {
    const timedOut = error && (error.name === "AbortError" || String(error.message || "").includes("aborted"));
    const payload = timedOut
      ? { ok: false, error: { code: "request_timeout", message: "完整模型读取较慢，已保留当前可用结果。" }, warnings: ["完整模型超过等待时间。页面会保留最近一次结果；可以稍后重试，或直接生成今日观察。"] }
      : { ok: false, error: { code: "connection_error", message: "本地 API 连接失败，请确认服务已启动。" }, warnings: ["本地 API 可能尚未启动，或端口被占用。"] };
    state.lastRaw = payload;
    renderRaw(payload);
    renderWarnings(payload.warnings);
    setStatus(timedOut ? "Ready" : "Offline", timedOut ? "保留当前结果" : "连接失败");
    return payload;
  } finally {
    if (timer) window.clearTimeout(timer);
  }
}

async function postRequest(path, body = {}, label = "保存") {
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
function renderWarnings(warnings = []) {
  const panel = qs("#warningsPanel");
  if (panel) panel.style.display = "none";
  if (qs("#warningsList")) qs("#warningsList").innerHTML = C.warnings(warnings);
}
function switchView(name) {
  state.currentView = name;
  document.querySelectorAll(".tab").forEach((tab) => {
    const isActive = tab.dataset.view === name;
    tab.classList.toggle("isActive", isActive);
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
    if (isActive) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  });
  document.querySelectorAll(".view").forEach((view) => {
    const isVisible = view.id === `view-${name}`;
    view.classList.toggle("isVisible", isVisible);
    view.hidden = !isVisible;
    view.setAttribute("aria-hidden", isVisible ? "false" : "true");
  });
  syncNavigationState(name);
}

function jumpToView(name) {
  switchView(name);
  focusView(name);
  maybeAutoLoadView(name);
}

function maybeAutoLoadView(name) {
  if (name === "missinginfo" && !state.missingInfoView) {
    window.setTimeout(() => loadMissingInfo(), 0);
  }
  if (name === "scoregoals" && !state.scoreGoalsView) {
    window.setTimeout(() => loadScoreGoals(), 0);
  }
  if (name === "proscore" && !state.proScoreView) {
    window.setTimeout(() => loadProfessionalModelScore(), 0);
  }
}

function syncNavigationState(name) {
  const labNav = qs(".labNav");
  const isPrimary = ["today", "learning", "operation"].includes(name);
  if (labNav) {
    labNav.open = !isPrimary;
    labNav.classList.toggle("isActiveGroup", !isPrimary);
  }
  document.querySelectorAll("[data-jump-view]").forEach((button) => {
    const isActiveStep = button.dataset.jumpView === name;
    button.classList.toggle("isActiveStep", isActiveStep);
    button.setAttribute("aria-pressed", isActiveStep ? "true" : "false");
  });
  const quickRefresh = qs("#todayQuickRefreshBtn");
  if (quickRefresh) {
    const isTodayStep = name === "today";
    quickRefresh.classList.toggle("isActiveStep", isTodayStep);
    quickRefresh.setAttribute("aria-pressed", isTodayStep ? "true" : "false");
  }
  const quickStatus = qs("#quickActionStatus");
  if (quickStatus) quickStatus.textContent = `当前：${quickActionLabel(name)}`;
}

function focusView(name) {
  const workspace = qs(".productWorkspace");
  const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (workspace && workspace.scrollIntoView) workspace.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
  const targetView = qs(`#view-${name}`);
  if (targetView && targetView.focus) {
    if (!targetView.hasAttribute("tabindex")) targetView.setAttribute("tabindex", "-1");
    targetView.focus({ preventScroll: true });
  }
}

function quickActionLabel(name) {
  const labels = {
    today: "重新读取比赛",
    bestparlay: "组合审核",
    missinginfo: "情报覆盖",
    learning: "赛后学习",
  };
  return labels[name] || "页面查看";
}

function refreshTodayFromRail() {
  jumpToView("today");
  return loadToday({ forceRefresh: true, useFastPreview: true });
}

function tableOrEmpty(rows, columns, message = "暂无数据") {
  return rows && rows.length ? C.table(rows, columns) : `<div class="emptyState">${C.escapeHtml(message)}</div>`;
}

function setAiAutoStatus(status = "idle", title = "自动研究待启动", body = "打开后会自动读取下一可售日比赛，再自动尝试 DS Pro 研究；若不可用则改用本地研究摘要。") {
  const strip = qs("#aiAutoStatusStrip");
  if (!strip) return;
  const resolvedStatus = status === "idle" ? "ds-auto" : status;
  strip.dataset.status = resolvedStatus;
  const label = status === "running" ? "研究中" : status === "done" ? "已完成" : status === "fallback" ? "本地摘要" : status === "error" ? "待检查" : "自动模式";
  strip.innerHTML = `<span>${C.escapeHtml(label)}</span><strong>${C.escapeHtml(title)}</strong><p>${C.escapeHtml(body)}</p>`;
}

function loadingTopCard(title, body = "正在自动读取数据，稍等几秒。") {
  return `
    <div class="loadingTopCard">
      <div class="loadingDot"></div>
      <strong>${C.escapeHtml(title)}</strong>
      <p>${C.escapeHtml(body)}</p>
    </div>
  `;
}

const TODAY_LOADING_STEPS = [
  { percent: 10, label: "启动今日观察", detail: "准备读取下一可售日。" },
  { percent: 24, label: "查找可售比赛", detail: "扫描今天到未来几天的赛程。" },
  { percent: 42, label: "读取赔率和数据源", detail: "确认比赛、赔率和数据源状态。" },
  { percent: 60, label: "计算可信度", detail: "检查情报缺口和纪律门控。" },
  { percent: 76, label: "审核单关和组合", detail: "先看单关，再判断 2串1 / 3串1 是否过门控。" },
  { percent: 90, label: "生成 Top 卡片", detail: "整理单关、组合、总进球和比分倾向。" },
  { percent: 100, label: "流程完成", detail: "候选与纪律结论已拿到，准备展示首页。 " },
];

const OPTIMIZER_LOADING_STEPS = [
  { percent: 8, label: "启动赛前优化", detail: "读取筛选条件、风险档位和目标日期。" },
  { percent: 22, label: "请求赛事与赔率", detail: "确认下一可售场次、官方赔率和数据源状态。" },
  { percent: 38, label: "加载模型与校准", detail: "融合市场概率、模型概率、去水与可信度信息。" },
  { percent: 58, label: "执行纪律门控", detail: "按相关性、风险等级与情报完整度过滤组合资格。" },
  { percent: 75, label: "构建观察池", detail: "生成单关、2串1、3串1 及拒绝列表。" },
  { percent: 92, label: "生成顶部摘要", detail: "整理 Top 信号、候选风险和拒绝原因。" },
  { percent: 100, label: "完成", detail: "赛前优化结果已就绪，即将展示。"},
];

function todayProgressMarkup(stepIndex = 0) {
  const safeIndex = Math.max(0, Math.min(stepIndex, TODAY_LOADING_STEPS.length - 1));
  const current = TODAY_LOADING_STEPS[safeIndex];
  const visibleSteps = TODAY_LOADING_STEPS.slice(0, 7);
  return `
    <div id="todayLoadingProgress" class="todayLoadingProgress isNova" style="--progress:${current.percent}%">
      <div class="todayProgressHeader">
        <span>生成进度</span>
        <strong>${C.escapeHtml(current.label)}</strong>
        <em>${C.escapeHtml(String(current.percent))}%</em>
      </div>
      <div class="todayProgressNovaWrap" aria-hidden="true">
        <div class="todayProgressNovaRail">
          <span class="todayProgressNovaGlow"></span>
          <span class="todayProgressNovaFill" style="--progress:${current.percent}%"></span>
          <span class="todayProgressNovaShimmer"></span>
          ${[0, 1, 2, 3].map((_, index) => `
            <i class="todayProgressNovaDot" style="--dot-angle:${index * 90}deg"></i>
          `).join("")}
        </div>
      </div>
      <div class="todayProgressSteps todayProgressStepsNova" aria-label="今日观察生成阶段">
        ${visibleSteps.map((step, index) => `
          <b class="${index < safeIndex ? "isDone" : index === safeIndex ? "isActive" : ""}" data-index="${index}">
            <em>${index + 1}</em>
            ${C.escapeHtml(step.label)}
          </b>
        `).join("")}
      </div>
      <p class="todayProgressDetail">${C.escapeHtml(current.detail)}</p>
    </div>
  `;
}

function stopTodayProgressTicker() {
  if (state.todayProgressTimer) {
    window.clearInterval(state.todayProgressTimer);
    state.todayProgressTimer = null;
  }
}

function updateTodayProgress(stepIndex) {
  const target = qs("#todayLoadingProgress");
  if (!target) return;
  const safeIndex = Math.max(0, Math.min(stepIndex, TODAY_LOADING_STEPS.length - 1));
  const current = TODAY_LOADING_STEPS[safeIndex];
  target.style.setProperty("--progress", `${current.percent}%`);
  const fill = target.querySelector(".todayProgressNovaFill");
  if (fill) fill.style.setProperty("--progress", `${current.percent}%`);
  const title = target.querySelector(".todayProgressHeader strong");
  const percent = target.querySelector(".todayProgressHeader em");
  const body = target.querySelector("p");
  if (title) title.textContent = current.label;
  if (percent) percent.textContent = `${current.percent}%`;
  if (body) body.textContent = current.detail;
  target.querySelectorAll(".todayProgressSteps b").forEach((node, index) => {
    node.classList.toggle("isDone", index < safeIndex);
    node.classList.toggle("isActive", index === safeIndex);
  });
  target.classList.toggle("isAlmost", current.percent >= 80 && current.percent < 100);
  target.classList.toggle("isDoneState", current.percent >= 100);
}

function startTodayProgressTicker() {
  stopTodayProgressTicker();
  state.todayProgressStartedAt = Date.now();
  const schedule = [
    { ms: 0, step: 0 },
    { ms: 1200, step: 1 },
    { ms: 2800, step: 2 },
    { ms: 5200, step: 3 },
    { ms: 8500, step: 4 },
    { ms: 13000, step: 5 },
    { ms: 21000, step: 6 },
  ];
  let lastStep = 0;
  updateTodayProgress(0);
  state.todayProgressTimer = window.setInterval(() => {
    const elapsed = Date.now() - state.todayProgressStartedAt;
    const next = schedule.slice().reverse().find((item) => elapsed >= item.ms) || schedule[0];
    if (next.step !== lastStep) {
      lastStep = next.step;
      updateTodayProgress(next.step);
    }
  }, 650);
}

function optimizerProgressMarkup(stepIndex = 0) {
  const safeIndex = Math.max(0, Math.min(stepIndex, OPTIMIZER_LOADING_STEPS.length - 1));
  const current = OPTIMIZER_LOADING_STEPS[safeIndex];
  const visibleSteps = OPTIMIZER_LOADING_STEPS.slice(0, 7);
  return `
    <div id="optimizerLoadingProgress" class="todayLoadingProgress isNova" style="--progress:${current.percent}%">
      <div class="todayProgressHeader">
        <span>OPTIMIZER</span>
        <strong>${C.escapeHtml(current.label)}</strong>
        <em>${C.escapeHtml(String(current.percent))}%</em>
      </div>
      <div class="todayProgressNovaWrap" aria-hidden="true">
        <div class="todayProgressNovaRail">
          <span class="todayProgressNovaGlow"></span>
          <span class="todayProgressNovaFill" style="--progress:${current.percent}%"></span>
          <span class="todayProgressNovaShimmer"></span>
          ${[0, 90, 180, 270].map((angle) => `<i class="todayProgressNovaDot" style="--dot-angle:${angle}deg"></i>`).join("")}
        </div>
      </div>
      <div class="todayProgressSteps todayProgressStepsNova" aria-label="赛前优化进度">
        ${visibleSteps.map((step, index) => `
          <b class="${index < safeIndex ? "isDone" : index === safeIndex ? "isActive" : ""}" data-index="${index}">
            <em>${index + 1}</em>
            ${C.escapeHtml(step.label)}
          </b>
        `).join("")}
      </div>
      <p class="todayProgressDetail">${C.escapeHtml(current.detail)}</p>
    </div>
  `;
}

function updateOptimizerProgress(stepIndex) {
  const target = qs("#optimizerLoadingProgress");
  if (!target) return;
  const safeIndex = Math.max(0, Math.min(stepIndex, OPTIMIZER_LOADING_STEPS.length - 1));
  const current = OPTIMIZER_LOADING_STEPS[safeIndex];
  target.style.setProperty("--progress", `${current.percent}%`);
  const fill = target.querySelector(".todayProgressNovaFill");
  if (fill) fill.style.setProperty("--progress", `${current.percent}%`);
  const title = target.querySelector(".todayProgressHeader strong");
  const percent = target.querySelector(".todayProgressHeader em");
  const body = target.querySelector(".todayProgressDetail");
  if (title) title.textContent = current.label;
  if (percent) percent.textContent = `${current.percent}%`;
  if (body) body.textContent = current.detail;
  target.querySelectorAll(".todayProgressSteps b").forEach((node, index) => {
    node.classList.toggle("isDone", index < safeIndex);
    node.classList.toggle("isActive", index === safeIndex);
  });
  target.classList.toggle("isAlmost", current.percent >= 85 && current.percent < 100);
  target.classList.toggle("isDoneState", current.percent >= 100);
}

function startOptimizerProgressTicker() {
  stopOptimizerProgressTicker();
  state.optimizerProgressStartedAt = Date.now();
  const schedule = [
    { ms: 0, step: 0 },
    { ms: 1200, step: 1 },
    { ms: 2600, step: 2 },
    { ms: 4700, step: 3 },
    { ms: 7600, step: 4 },
    { ms: 11500, step: 5 },
    { ms: 18800, step: 6 },
  ];
  let lastStep = 0;
  updateOptimizerProgress(0);
  state.optimizerProgressTimer = window.setInterval(() => {
    const elapsed = Date.now() - state.optimizerProgressStartedAt;
    const next = schedule.slice().reverse().find((item) => elapsed >= item.ms) || schedule[0];
    if (next.step !== lastStep) {
      lastStep = next.step;
      updateOptimizerProgress(next.step);
    }
  }, 450);
}

function stopOptimizerProgressTicker() {
  if (state.optimizerProgressTimer) {
    window.clearInterval(state.optimizerProgressTimer);
    state.optimizerProgressTimer = null;
  }
}


function workflowScoreItems(view) {
  if (!view) {
    return [
      { label: "数据源", score: 20, detail: "等待读取比赛", next: "先拿到真实可售比赛。" },
      { label: "Top信号", score: 15, detail: "等待候选生成", next: "等待赔率与模型生成 Top 信号。" },
      { label: "组合纪律", score: 15, detail: "等待可信度门控", next: "等待可信度和被拒原因。" },
      { label: "AI研究", score: 10, detail: "等待自动研究", next: "系统会自动尝试 DS Pro；不可用时改用本地研究摘要。" },
      { label: "赛后学习", score: 55, detail: "入口已准备", next: "赛后录入结果和收盘赔率可继续加分。" },
    ];
  }
  if (view.long_run_score && Array.isArray(view.long_run_score.items)) {
    const memory = aiMemoryForDate(view.selected_date || view.date);
    const learningImpact = state.lastLearningImpact || {};
    return view.long_run_score.items.map((item) => {
      if (item.label === "AI研究") {
        if (memory) {
          return {
            ...item,
            score: aiMemoryLongRunScore(memory, item.score),
            detail: aiMemoryDetail(memory),
            next: aiMemoryNext(memory),
          };
        }
        return {
          ...item,
          score: workflowClampScore(Math.min(Number(item.score ?? 35), 45)),
          detail: aiTodayMissingDetail(view),
          next: aiTodayMissingNext(view),
        };
      }
      if (item.label === "赛后学习" && learningImpact.saved) {
        return {
          ...item,
          score: Math.max(workflowClampScore(item.score), learningImpact.score_after || 72),
          detail: learningImpact.detail || "刚刚保存赛后学习样本",
          next: learningImpact.next || "继续累计比分、收盘赔率和被拒组合复盘。",
        };
      }
      return item;
    });
  }
  const singles = view.top_singles || [];
  const parlay2 = view.top_2x1 || view.top_2x1_display || [];
  const parlay3 = view.top_3x1 || view.top_3x1_display || [];
  const gate = view.credibility_gate || view.credibility_audit?.credibility_gate || {};
  const providerUsed = String(view.provider_used || "");
  const sourceScore = workflowClampScore(
    (view.matches_count || 0) > 0
      ? providerUsed.includes("mock")
        ? 45
        : (view.source_health?.reliability_score ?? view.data_source_status?.reliability_score ?? 88)
      : 15
  );
  const signalScore = workflowClampScore(
    Math.min(100, (singles.length ? 46 : 0)
      + Math.min(18, singles.length * 6)
      + ((view.top_total_goals || []).length ? 16 : 0)
      + ((view.top_scores || []).length ? 12 : 0)
      + ((view.rejected_combos || view.best_parlay_summary?.rejected_combos || []).length ? 8 : 0))
  );
  const gateName = String(gate.combo_gate || "");
  const hasComboContext = Boolean(parlay2.length || parlay3.length || gate.combo_gate || view.best_parlay_summary?.no_combo_reason);
  const comboScore = workflowClampScore(
    gateName === "open" ? 92
      : gateName === "restricted" ? 78
      : gateName === "closed" ? 70
      : hasComboContext ? 62
      : 25
  );
  const memory = aiMemoryForDate(view.selected_date || view.date);
  const aiStatus = todayAiStatusKey(view);
  const aiScore = workflowClampScore(
    memory
      ? aiMemoryLongRunScore(memory, 78)
      : aiStatus === "done" ? 78
        : aiStatus === "cached" ? 68
        : aiStatus === "ready" ? 45
        : aiStatus === "fallback" ? 35
        : 28
  );
  const learningHistory = view.learning_history_summary || view.learning_summary || {};
  const settledCount = Number(learningHistory.settled_count || learningHistory.sample_count || 0);
  const learningImpact = state.lastLearningImpact || {};
  const learningScore = workflowClampScore(learningImpact.saved ? (learningImpact.score_after || 72) : settledCount > 30 ? 88 : settledCount > 5 ? 72 : 58);
  return [
    { label: "数据源", score: sourceScore, detail: sourceScore >= 80 ? `${view.provider_used || "auto"} · ${view.matches_count || 0} 场` : "未拿到高可靠真实可售比赛", next: "优先保持 Sporttery 主数据稳定，并记录 fallback/缓存状态。" },
    { label: "Top信号", score: signalScore, detail: singles.length ? `单关 ${singles.length} 条，含进球/比分参考` : "暂无单关候选", next: "补赔率覆盖、校准样本和临场复核，让 Top 信号更少但更硬。" },
    { label: "组合纪律", score: comboScore, detail: gate.label_zh || gate.reason_zh || "等待门控结论", next: "不要强行串联；先提高单腿可信度、降低相关性和长冷风险。" },
    { label: "AI研究", score: aiScore, detail: memory ? aiMemoryDetail(memory) : aiTodayMissingDetail(view), next: memory ? aiMemoryNext(memory) : aiTodayMissingNext(view) },
    { label: "赛后学习", score: learningScore, detail: learningImpact.saved ? (learningImpact.detail || "刚刚保存赛后学习样本") : settledCount ? `已结算样本 ${settledCount} 条` : "赛后可对照结果继续校准", next: learningImpact.saved ? (learningImpact.next || "继续累计比分、收盘赔率和被拒组合复盘。") : "长期提升靠赛后比分、收盘赔率、CLV 和概率校准样本。" },
  ];
}

function workflowClampScore(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.max(0, Math.min(100, Math.round(num)));
}

function todayAiStatus(view = {}) {
  return view.ai_research_status || {};
}

function todayAiStatusKey(view = {}) {
  const ai = todayAiStatus(view);
  return String(ai.status || "");
}

function todayAiStatusSummary(view = {}) {
  const ai = todayAiStatus(view);
  return ai.summary_zh || view.ai_research_layer?.runtime_notice_zh || view.ai_research_layer?.display_status_zh || view.ai_research_layer?.fallback_reason || view.llm_status?.status_detail_zh || "当前还没有自动研究记录。";
}

function aiMemoryForDate(date, allowFallback = false) {
  const rows = readAiResearchMemory();
  const key = String(date || "");
  const exact = rows.find((row) => row.selected_date === key);
  return exact || (allowFallback ? rows[0] || null : null);
}

function aiTodayMissingDetail(view = {}) {
  const status = todayAiStatusKey(view);
  if (status === "running") return "今日 DS Pro 正在研究；完成并保存后才计入今日 AI 分。";
  if (status === "done") return "今日已有 DS Pro 研究记录；请对照被拒原因、Top 覆盖和赛后学习点。";
  if (status === "cached") return "今日研究已保留最近一次成功的 DS 结果；可以先看结论，再决定是否稍后刷新。";
  if (status === "ready") return "今日尚无 DS Pro 复核记录；历史学习趋势不会代替今日判断。";
  if (status === "fallback") return "今日已自动尝试 DS，但当前临时回退为本地摘要；可继续先看纪律和情报缺口。";
  if (status === "not_configured") return "DS 还未配置完成；当前先用本地解释层，不影响概率和纪律门控。";
  return "今日未完成 AI 复核；先显示赔率、模型和纪律门控结果。";
}

function aiTodayMissingNext(view = {}) {
  const status = todayAiStatusKey(view);
  if (status === "running") return "等待自动研究完成后，再看 Top 覆盖、被拒原因和赛后学习点。";
  if (status === "done") return "保持自动研究开启，接下来重点用赛后结果验证 AI 解释是否真的提高判断质量。";
  if (status === "cached") return "当前可先用缓存研究；如需最新解释，可稍后刷新并留意 Key、额度或网络。";
  if (status === "ready") return "让系统自动跑一次 DS Pro；当天有记录后才提高今日 AI 研究分。";
  if (status === "fallback") return "先看失败原因和本地摘要，再决定是否稍后重试自动研究。";
  return "确认 DS Pro key 和本地服务状态；不可用时继续保留本地解释兜底。";
}

function aiMemoryLongRunScore(memory, fallback = 55) {
  if (!memory) return workflowClampScore(fallback);
  const quality = Number(memory.ai_quality_score);
  const dsCalls = Number(memory.ds_call_count || 0);
  const coverage = parseCoverageRatio(memory.top_coverage);
  let score = Number.isFinite(quality) ? quality : workflowClampScore(fallback);
  if (dsCalls > 0) score += 8;
  if (coverage >= 0.99) score += 8;
  else if (coverage >= 0.5) score += 3;
  else score -= 8;
  if (String(memory.ai_quality_source || "").includes("fallback")) score -= 8;
  return workflowClampScore(Math.max(score, dsCalls > 0 ? 62 : 48));
}

function aiMemoryDetail(memory) {
  if (!memory) return "auto 自动研究完成后会留痕";
  return `${memory.ai_provider || "local"} · ${memory.ai_status || "done"} · 质量 ${memory.ai_quality_grade || "N/A"}/${memory.ai_quality_score ?? "N/A"} · Top ${memory.top_coverage || "0/0"}`;
}

function aiMemoryNext(memory) {
  if (!memory) return "让 DS Pro 自动总结被拒原因、赔率覆盖和赛后学习点。";
  const coverage = parseCoverageRatio(memory.top_coverage);
  if (coverage < 1) return "优先提高 DS 逐场覆盖：让 match_notes 覆盖全部 Top 单关、组合和被拒候选。";
  const quality = Number(memory.ai_quality_score);
  if (Number.isFinite(quality) && quality < 80) return "提升结构化 JSON 质量，减少本地兜底，并赛后对照 AI 判断是否有帮助。";
  return "保持 auto DS 研究，赛后用命中、CLV 和被拒组合复盘检验 AI 解释是否真正有用。";
}

function parseCoverageRatio(text) {
  const match = String(text || "").match(/(\d+)\s*\/\s*(\d+)/);
  if (!match) return 0;
  const got = Number(match[1]);
  const total = Number(match[2]);
  return total > 0 ? got / total : 0;
}

function aiResearchTrendSummary() {
  const rows = readAiResearchMemory().slice(0, 6);
  if (!rows.length) return "";
  const qualityRows = rows.map((row) => Number(row.ai_quality_score)).filter((value) => Number.isFinite(value));
  const avgQuality = qualityRows.length ? Math.round(qualityRows.reduce((sum, value) => sum + value, 0) / qualityRows.length) : null;
  const dsCalls = rows.reduce((sum, row) => sum + Number(row.ds_call_count || 0), 0);
  const coverageRows = rows.map((row) => parseCoverageRatio(row.top_coverage)).filter((value) => Number.isFinite(value) && value >= 0);
  const avgCoverage = coverageRows.length ? Math.round((coverageRows.reduce((sum, value) => sum + value, 0) / coverageRows.length) * 100) : null;
  const fallbackCount = rows.filter((row) => String(row.ai_quality_source || "").includes("fallback")).length;
  const parts = [
    `近 ${rows.length} 次`,
    avgQuality === null ? "质量待累计" : `平均质量 ${avgQuality}/100`,
    avgCoverage === null ? "Top覆盖待累计" : `Top覆盖 ${avgCoverage}%`,
    `DS ${dsCalls} 次`,
  ];
  if (fallbackCount) parts.push(`本地兜底 ${fallbackCount} 次`);
  return parts.join(" · ");
}

function aiResearchTrendDetails(rows = readAiResearchMemory().slice(0, 6)) {
  if (!rows.length) {
    return {
      status: "empty",
      title: "AI 研究趋势待累计",
      message: "刷新下一可售日观察后，auto DS / 本地研究记录会保存在这里。",
      next: "先让 auto 跑出第一份研究摘要。",
    };
  }
  const qualityRows = rows.map((row) => Number(row.ai_quality_score)).filter((value) => Number.isFinite(value));
  const avgQuality = qualityRows.length ? Math.round(qualityRows.reduce((sum, value) => sum + value, 0) / qualityRows.length) : 0;
  const coverageRows = rows.map((row) => parseCoverageRatio(row.top_coverage)).filter((value) => Number.isFinite(value) && value >= 0);
  const avgCoverage = coverageRows.length ? Math.round((coverageRows.reduce((sum, value) => sum + value, 0) / coverageRows.length) * 100) : 0;
  const fallbackCount = rows.filter((row) => String(row.ai_quality_source || "").includes("fallback")).length;
  const dsCalls = rows.reduce((sum, row) => sum + Number(row.ds_call_count || 0), 0);
  const status = avgQuality >= 85 && avgCoverage >= 90 && fallbackCount === 0 ? "good" : avgQuality >= 70 && avgCoverage >= 60 ? "watch" : "needs_work";
  const next = status === "good"
    ? "保持当前 auto DS 流程，赛后重点检验 AI 解释是否真的帮助识别被拒组合和冷门风险。"
    : avgCoverage < 80
      ? "优先提高 Top 覆盖：让 match_notes 覆盖单关、2串1、3串1和被拒组合。"
      : fallbackCount > 0
        ? "减少本地兜底：继续优化 DS 结构化 JSON 输出和短重试。"
        : "继续提升结构化质量，并用赛后结果检验 AI 判断是否有效。";
  const primaryAction = status === "good"
    ? "去赛后检验"
    : avgCoverage < 80
      ? "补 Top 覆盖"
      : fallbackCount > 0
        ? "重跑结构化研究"
        : "重新跑 auto 研究";
  const secondaryAction = status === "good" ? "重新跑 auto 研究" : "去赛后学习";
  const scoreEffects = [];
  if (avgQuality >= 85) scoreEffects.push({ label: "质量加分", text: "结构化质量高，AI研究分更稳。" });
  else scoreEffects.push({ label: "质量拖分", text: "结构化质量不足，会压低 AI研究分。" });
  if (avgCoverage >= 90) scoreEffects.push({ label: "覆盖加分", text: "Top 卡片覆盖完整，首页解释更可信。" });
  else scoreEffects.push({ label: "覆盖拖分", text: "Top 覆盖不足，部分卡片只能用分类/本地解释。" });
  if (fallbackCount > 0) scoreEffects.push({ label: "兜底扣分", text: "出现本地兜底，说明 DS 结构化输出仍不稳定。" });
  if (dsCalls > 0) scoreEffects.push({ label: "DS参与", text: "DS Pro 已参与研究，但仍要看质量和赛后验证。" });
  const todos = [];
  if (avgCoverage < 90) todos.push("补齐 Top 卡片逐场 match_notes，尤其是 2串1、3串1和被拒组合。");
  if (avgQuality < 85) todos.push("提高 DS 结构化 JSON 质量，减少无法解析或字段缺失。");
  if (fallbackCount > 0) todos.push("检查本地兜底原因：DS 未返回 JSON、覆盖补洞失败或字段不完整。");
  if (todos.length < 3) todos.push("赛后录入赛果和收盘赔率，验证 AI 解释是否真的帮到判断。");
  return {
    status,
    title: status === "good" ? "AI 研究趋势稳定" : status === "watch" ? "AI 研究可用但要观察" : "AI 研究仍需补强",
    avgQuality,
    avgCoverage,
    fallbackCount,
    dsCalls,
    count: rows.length,
    metricCards: [
      { label: "平均质量", value: `${avgQuality}/100` },
      { label: "Top覆盖", value: `${avgCoverage}%` },
      { label: "DS调用", value: `${dsCalls}次` },
      { label: "本地兜底", value: `${fallbackCount}次` },
    ],
    scoreEffects,
    todos: todos.slice(0, 3),
    message: `近 ${rows.length} 次平均质量 ${avgQuality}/100，Top 覆盖 ${avgCoverage}%，DS 调用 ${dsCalls} 次，本地兜底 ${fallbackCount} 次。`,
    next,
    primaryAction,
    secondaryAction,
  };
}

function renderWorkflowScore(view, status = "loading") {
  const panel = qs("#workflowScorePanel");
  if (!panel) return;
  const items = workflowScoreItems(view);
  const weights = [0.22, 0.22, 0.20, 0.18, 0.18];
  const score = workflowClampScore(items.reduce((sum, item, index) => sum + workflowClampScore(item.score) * (weights[index] || 0), 0));
  state.currentWorkflowScore = score;
  state.currentWorkflowItems = items.map((item) => ({
    label: item.label || "未知项",
    score: workflowClampScore(item.score),
    detail: item.detail || "",
    next: item.next || "",
  }));
  const label = status === "error" ? "需要检查" : score >= 80 ? "可用" : score >= 60 ? "可观察" : "准备中";
  const weakest = [...items].sort((a, b) => workflowClampScore(a.score) - workflowClampScore(b.score))[0] || {};
  const aiTrend = aiResearchTrendSummary();
  const sortedItems = [...items]
    .sort((a, b) => workflowClampScore(a.score) - workflowClampScore(b.score))
  const backendRoadmap = view?.long_run_score?.score_roadmap;
  const itemByLabel = new Map(items.map((item) => [item.label, item]));
  const syncedBackendRoadmap = Array.isArray(backendRoadmap)
    ? backendRoadmap.map((row) => {
      const current = itemByLabel.get(row.label) || row;
      return { ...row, ...current, score: workflowClampScore(current.score ?? row.score) };
    }).filter((row) => workflowClampScore(row.score) < 90)
      .sort((a, b) => workflowClampScore(a.score) - workflowClampScore(b.score))
    : [];
  const roadmap = syncedBackendRoadmap.length
    ? syncedBackendRoadmap.slice(0, 3)
    : sortedItems.filter((item) => workflowClampScore(item.score) < 90).slice(0, 3);
  const next = status === "error"
    ? "先检查本地服务和数据源。"
    : !view
      ? "等待比赛、赔率和 DS 研究自动完成。"
      : score >= 80
        ? `当前最低分：${weakest.label || "赛后学习"}，下一步：${weakest.next || "继续赛后复盘。"}`
        : `优先补短板：${weakest.label || "数据源"}，${weakest.next || "先补数据和学习样本。"}`;
  const bottleneck = workflowBottleneck(weakest, score, status);
  state.currentWorkflowBottleneck = bottleneck;
  if (view && status !== "loading") rememberWorkflowScore(view, score, weakest);
  const learningImpact = state.lastLearningImpact || {};
  panel.innerHTML = `
    <article class="workflowScoreCard" data-score="${C.escapeHtml(String(score))}">
      <div class="workflowScoreMain">
        <span>LONG-RUN SCORE</span>
        <strong>${C.escapeHtml(String(score))}/100 · ${C.escapeHtml(label)}</strong>
        <p>${C.escapeHtml(next)}</p>
        <div class="workflowBottleneck">
          <b>${C.escapeHtml(bottleneck.title)}</b>
          <span>${C.escapeHtml(bottleneck.impact)}</span>
          <em>${C.escapeHtml(bottleneck.action)}</em>
        </div>
        ${workflowNextActionCard(weakest, bottleneck, score, status)}
        ${renderWorkflowScoreMemory()}
        ${workflowTargetCard(score, weakest, status)}
        ${renderAutoResearchCockpit(view, status)}
        ${learningImpact.saved ? `<div class="workflowImpact">赛后学习已入库：${C.escapeHtml(learningImpact.summary || "比分和收盘赔率已保存到本地学习库。")}</div>` : ""}
        ${state.lastWorkflowAction ? `<div class="workflowActionImpact" data-status="${C.escapeHtml(state.lastWorkflowAction.status || "running")}">刚刚处理：${C.escapeHtml(state.lastWorkflowAction.label)} · ${C.escapeHtml(state.lastWorkflowAction.message)}${workflowScoreDeltaText(state.lastWorkflowAction)}</div>` : ""}
        ${renderWorkflowActionTrend()}
        ${renderWorkflowActionHistory()}
        ${aiTrend ? `<div class="workflowAiTrend">AI研究趋势：${C.escapeHtml(aiTrend)}</div>` : ""}
      </div>
      <div class="workflowScoreItems">
        ${items.map((item) => `
          <div class="workflowScoreItem ${workflowClampScore(item.score) >= 70 ? "isPassed" : "isPending"}">
            <b>${C.escapeHtml(String(workflowClampScore(item.score)))}</b>
            <span>${C.escapeHtml(item.label)}</span>
            <em>${C.escapeHtml(item.detail)}</em>
            <small>${C.escapeHtml(workflowItemNextHint(item))}</small>
            <i>验收：${C.escapeHtml(workflowAcceptanceSignal(item.label))}</i>
          </div>
        `).join("")}
      </div>
      <div class="workflowScoreRoadmap">
        <span>下一步优先级</span>
        ${(roadmap.length ? roadmap : sortedItems.slice(0, 1)).map((item, index) => `
          <article>
            <b>${index + 1}</b>
            <div>
              <strong>${C.escapeHtml(item.label)} · ${C.escapeHtml(String(workflowClampScore(item.score)))}/100</strong>
              <p>${C.escapeHtml(item.next || "继续补齐这个短板。")}</p>
              ${workflowQuickActionButton(item)}
            </div>
          </article>
        `).join("")}
      </div>
    </article>
  `;
}

function renderAutoResearchCockpit(view, status = "loading") {
  const today = view || state.todayView || {};
  const aiMemory = aiMemoryForDate(today.selected_date || today.date, true);
  const latestAi = state.latestAiResearch || {};
  const hasMatches = Number(today.matches_count || today.matches_analyzed || 0) > 0;
  const hasTopSignals = Boolean((today.top_singles || []).length || (today.top_2x1_display || []).length || (today.top_3x1_display || []).length);
  const hasGate = Boolean(today.credibility_gate || today.credibility_audit?.credibility_gate || today.best_parlay_summary);
  const dsDone = Boolean(latestAi.ds_completed || aiMemory?.ds_call_count > 0);
  const localDone = Boolean(latestAi.status || aiMemory);
  const learningDone = Boolean(state.lastLearningImpact?.saved);
  const rows = [
    {
      label: "T+1比赛读取",
      status: hasMatches ? "done" : status === "error" ? "error" : "running",
      text: hasMatches ? `${today.selected_date || "自动日期"} · ${today.matches_count || today.matches_analyzed || 0} 场 · ${today.provider_used || "auto"}` : "正在寻找未来 1-3 天可售比赛。",
    },
    {
      label: "赔率/模型/组合纪律",
      status: hasTopSignals && hasGate ? "done" : hasTopSignals ? "running" : status === "error" ? "error" : "pending",
      text: hasTopSignals ? "Top 单关、2串1/3串1纸面候选和被拒原因已生成。" : "等待 Top 观察和可信度门控。",
    },
    {
      label: "DS Pro研究层",
      status: dsDone ? "done" : localDone ? "fallback" : status === "error" ? "error" : "pending",
      text: dsDone ? "DS Pro 已参与解释、质检和复盘摘要。" : localDone ? "当前使用本地研究摘要；DS Pro 可用时会自动接管。" : "auto 会在候选生成后自动尝试研究层。",
    },
    {
      label: "赛后学习闭环",
      status: learningDone ? "done" : "pending",
      text: learningDone ? "本轮赛后学习样本已保存。" : "赛后录入比分和收盘赔率后，长线评分才会真正变稳。",
    },
  ];
  const weakestItem = workflowWeakestItem(state.currentWorkflowItems);
  const scoreDirective = workflowScoreDrivenDirective(state.currentWorkflowScore, state.currentWorkflowBottleneck, state.currentWorkflowItems);
  const copyText = autoResearchCopySummary(rows, today, latestAi, aiMemory);
  return `
    <div class="autoResearchCockpit">
      <div class="autoResearchHead">
        <span>AUTO RESEARCHER</span>
        <strong>自动研究员模式</strong>
        <p>自动跑 T+1 比赛、赔率/模型、组合纪律、DS Pro 研究摘要和赛后学习闭环；不是单纯切换数据源。</p>
      </div>
      <div class="autoResearchSteps">
        ${rows.map((row, index) => `
          <article data-status="${C.escapeHtml(row.status)}">
            <b>${index + 1}</b>
            <div>
              <strong>${C.escapeHtml(row.label)}</strong>
              <p>${C.escapeHtml(row.text)}</p>
            </div>
          </article>
        `).join("")}
      </div>
      <div class="scoreDrivenDirective" data-level="${C.escapeHtml(scoreDirective.level)}">
        <span>SCORE-DRIVEN MODE</span>
        <strong>${C.escapeHtml(scoreDirective.title)}</strong>
        <p>${C.escapeHtml(scoreDirective.body)}</p>
        <em>${C.escapeHtml(scoreDirective.rule)}</em>
        <u>${C.escapeHtml(scoreDirective.avoid)}</u>
        ${weakestItem ? `<div class="scoreDrivenAction">
          <small>当前短板动作：${C.escapeHtml(weakestItem.label)} · ${C.escapeHtml(weakestItem.next || "先处理这个分项。")}</small>
          ${workflowQuickActionButton(weakestItem)}
        </div>` : ""}
      </div>
      <div class="autoResearchActions">
        <button class="secondary compactButton" type="button" onclick="loadToday()">重新跑完整 auto</button>
        <button class="ghost compactButton workflowCopyBtn" type="button" data-copy-text="${C.escapeHtml(copyText)}" data-copy-ok="auto 研究复盘任务已复制，可交给 DS Pro 继续分析。" data-copy-fail="复制失败，请手动复制。">复制 auto 复盘任务</button>
      </div>
    </div>
  `;
}

function workflowWeakestItem(items = []) {
  const rows = Array.isArray(items) ? items.filter((item) => item && item.label) : [];
  if (!rows.length) return null;
  return rows.slice().sort((a, b) => workflowClampScore(a.score) - workflowClampScore(b.score))[0];
}

function workflowScoreDrivenDirective(score = 0, bottleneck = {}, items = []) {
  const safeScore = workflowClampScore(score);
  const weakest = bottleneck?.title || workflowWeakestItem(items)?.label || "长线评分";
  if (safeScore < 60) {
    return {
      level: "repair",
      title: "先修基础，不急着加复杂模型",
      body: `${weakest} 正在拖累整体分数；auto 会优先补真实比赛、赔率覆盖、DS 解释和赛后学习入口。`,
      rule: "规则：低于 60 只做补基础实验，不扩大组合复杂度。",
      avoid: "先不要做：强行找 2串1/3串1、扩大风险档位、同时改多个参数。",
    };
  }
  if (safeScore < 80) {
    return {
      level: "build",
      title: "进入可用区，按短板做单点实验",
      body: `${weakest} 是下一轮优先项；每次只改一个变量，复核分数是否真的上升。`,
      rule: "规则：60-79 分只做一项实验，避免同时改数据源、AI 和组合纪律。",
      avoid: "先不要做：把高 EV 冷门直接当作强组合核心，或忽略被拒原因。",
    };
  }
  if (safeScore < 90) {
    return {
      level: "optimize",
      title: "开始优化稳定性和赛后学习",
      body: "当前可用，但仍要用赛后结果、CLV、Brier/Log Loss 和 DS 复盘检验是否真有帮助。",
      rule: "规则：80-89 分重点看稳定性，不因单日高 EV 放大组合。",
      avoid: "先不要做：为了提高日内输出数量而牺牲可信度门控。",
    };
  }
  return {
    level: "maintain",
    title: "保持高分，持续小步学习",
    body: "当前长线结构较稳，重点保持数据质量、赛后学习和 DS 复盘覆盖。",
    rule: "规则：90+ 只做小幅迭代，任何回落都暂停同方向加码。",
    avoid: "先不要做：大改模型权重；先用更多赛后样本证明必要性。",
  };
}

function autoResearchCopySummary(rows = [], today = {}, latestAi = {}, aiMemory = null) {
  const topSingle = (today.top_singles || [])[0] || {};
  const top2 = ((today.top_2x1 || []).length ? today.top_2x1 : today.top_2x1_display || [])[0] || {};
  const top3 = (today.top_3x1_display || [])[0] || {};
  const gate = today.credibility_gate || today.credibility_audit?.credibility_gate || {};
  const directive = workflowScoreDrivenDirective(state.currentWorkflowScore, state.currentWorkflowBottleneck, state.currentWorkflowItems);
  const weakest = workflowWeakestItem(state.currentWorkflowItems);
  const scoreTrail = workflowScoreTimelineText();
  const trendDiagnosis = workflowScoreTrendDiagnosis();
  return [
    "JC Edge auto 自动研究员复盘任务",
    `当前长线分：${state.currentWorkflowScore ?? "未知"}/100`,
    `最近分数轨迹：${scoreTrail}`,
    `轨迹诊断：${trendDiagnosis}`,
    `分数驱动策略：${directive.title}；${directive.rule}`,
    `当前不要做：${directive.avoid}`,
    `当前短板动作：${weakest ? `${weakest.label} · ${weakest.next || "先处理这个分项。"}` : "暂无"}`,
    `日期：${today.selected_date || today.date || currentDateParam() || "自动日期"}`,
    `比赛数：${today.matches_count || today.matches_analyzed || "未知"}；数据源：${today.provider_used || providerParam() || "auto"}`,
    `可信度门控：${gate.label_zh || gate.combo_gate || "待评估"}；原因：${gate.reason_zh || today.no_combo_reason || "请结合 Top 信号和被拒原因复盘。"}`,
    `DS状态：${latestAi.ds_completed || Number(aiMemory?.ds_call_count || 0) > 0 ? "DS Pro 已参与" : latestAi.status ? "本地/兜底摘要已生成" : "待运行"}`,
    "auto流水线：",
    ...rows.map((row, index) => `${index + 1}. ${row.label}: ${row.status} · ${row.text}`),
    "Top观察：",
    `单关：${summarizeComboLegs(topSingle)}`,
    `2串1：${summarizeComboLegs(top2)}`,
    `3串1：${summarizeComboLegs(top3)}`,
    "请复盘：1）哪些信号可观察；2）为什么不串或只作纸面候选；3）缺失情报如何影响可信度；4）赛后应该记录哪些学习字段。",
  ].join("\n");
}

function workflowBottleneck(item = {}, totalScore = 0, status = "loading") {
  if (status === "error") {
    return {
      title: "当前瓶颈：本地服务",
      impact: "页面无法稳定读取结果，后面的模型和 AI 研究都会失真。",
      action: "先恢复本地 API 和数据源，再重新读取今日观察。",
    };
  }
  const label = item.label || "数据源";
  const score = workflowClampScore(item.score);
  const low = score < 60 || totalScore < 60;
  const impactByLabel = {
    "数据源": "真实赛程和赔率不稳时，后续概率、EV 和组合判断都会降级。",
    "Top信号": "候选不够硬时，组合只是把弱信号相乘，不会自然变强。",
    "组合纪律": "串联放大不确定性，纪律分低时宁可先不组合。",
    "AI研究": "当天没有 DS Pro 复核时，解释层不能给今日判断加分。",
    "赛后学习": "没有赛后比分、收盘赔率和被拒组合复盘，长期分数很难提升。",
  };
  return {
    title: `当前瓶颈：${label} ${score}/100`,
    impact: impactByLabel[label] || "该项正在拖累整体长期评分。",
    action: low ? (item.next || "优先补齐这个短板，再重新刷新今日观察。") : "短板已不严重，继续累计样本和赛后复盘。",
  };
}

function workflowNextActionCard(item = {}, bottleneck = {}, totalScore = 0, status = "loading") {
  const label = item.label || "数据源";
  const score = workflowClampScore(item.score);
  const actionButton = workflowQuickActionButton(item);
  const expectedLift = workflowExpectedLift(label, score, totalScore, status);
  return `
    <div class="workflowNextActionCard">
      <span>NEXT BEST ACTION</span>
      <strong>${C.escapeHtml(label)}优先处理</strong>
      <p>${C.escapeHtml(bottleneck.action || item.next || "先处理当前最低分项。")}</p>
      <div class="workflowNextActionMeta">
        <em>当前 ${C.escapeHtml(String(score))}/100</em>
        <em>${C.escapeHtml(expectedLift)}</em>
      </div>
      ${actionButton}
    </div>
  `;
}

function workflowTargetCard(score = 0, weakest = {}, status = "loading") {
  const target = status === "error" ? 60 : score < 60 ? 60 : score < 80 ? 80 : score < 90 ? 90 : 100;
  const label = target === 60 ? "先到 60：可观察" : target === 80 ? "冲 80：可用" : target === 90 ? "冲 90：稳定" : "保持 90+：持续学习";
  const gap = Math.max(0, target - workflowClampScore(score));
  const focus = weakest.label || "数据源";
  const message = gap > 0
    ? `还差 ${gap} 分；优先补 ${focus}，不要同时开太多改动。`
    : "已超过当前目标档，重点保持数据质量和赛后学习。";
  const plan = workflowTargetLiftPlan(gap);
  const experiment = workflowTodayExperiment(plan[0], focus);
  const guard = workflowExperimentStreakSummary();
  state.currentWorkflowTarget = { target, label, gap, focus, message, plan, experiment, guard };
  const copySummary = workflowTargetCopySummary(state.currentWorkflowTarget);
  return `
    <div class="workflowTargetCard">
      <span>LONG-RUN TARGET</span>
      <strong>${C.escapeHtml(label)}</strong>
      <p>${C.escapeHtml(message)}</p>
      <div class="workflowTargetBar" aria-label="长期目标进度">
        <i style="width:${C.escapeHtml(String(Math.min(100, Math.max(0, score))))}%"></i>
      </div>
      <div class="workflowTodayExperiment">
        <b>今日只做一个实验：${C.escapeHtml(experiment.title)}</b>
        <small>${C.escapeHtml(experiment.rule)}</small>
        <ol>
          ${experiment.steps.map((step) => `<li>${C.escapeHtml(step)}</li>`).join("")}
        </ol>
        <div class="workflowExperimentActions">
          <button class="secondary compactButton workflowExperimentRecordBtn" type="button">记录今日实验</button>
          <button class="ghost compactButton workflowExperimentReviewBtn" type="button">标记实验已复核</button>
        </div>
      </div>
      ${renderWorkflowExperimentVerdict()}
      ${renderWorkflowExperimentGuard(guard)}
      ${renderWorkflowExperimentQueue(plan)}
      ${plan.length ? `<div class="workflowTargetPlan">${plan.map((item) => `
        <em>${C.escapeHtml(item.label)}：约 +${C.escapeHtml(String(item.lift))} 分 · ${C.escapeHtml(item.action)}<small>验收：${C.escapeHtml(item.acceptance)}</small></em>
      `).join("")}</div>` : ""}
      <button class="ghost compactButton workflowCopyBtn" type="button" data-copy-text="${C.escapeHtml(copySummary)}" data-copy-ok="长线计划已复制，可直接给 DS Pro 继续复盘。" data-copy-fail="长线计划复制失败，请手动复制。">复制长线计划</button>
    </div>
  `;
}

function workflowTargetCopySummary(target = {}) {
  const today = state.todayView || {};
  const observationDate = today.selected_date || today.date || currentDateParam() || "自动日期";
  const providerUsed = today.provider_used || providerParam() || "unknown";
  const matchesCount = today.matches_count ?? today.matches_analyzed ?? "未知";
  const scoreLines = (state.currentWorkflowItems || []).map((item, index) => (
    `${index + 1}. ${item.label}: ${item.score}/100 · ${item.detail || ""} · 下一步：${item.next || ""}`
  ));
  const planLines = (target.plan || []).map((item, index) => (
    `${index + 1}. ${item.label}: 预计 +${item.lift} 分 · ${item.action} · 验收：${item.acceptance || "看分项是否改善"}`
  ));
  const queueLines = (target.plan || []).slice(1, 4).map((item, index) => (
    `${index + 1}. ${item.label}: 预计 +${item.lift} 分 · ${item.action}`
  ));
  const verdict = workflowExperimentVerdictDetails();
  const scoreTrail = workflowScoreTimelineText();
  const trendDiagnosis = workflowScoreTrendDiagnosis();
  return [
    "JC Edge 长线修改计划",
    `生成时间：${new Date().toLocaleString("zh-CN", { hour12: false })}`,
    `观察日期：${observationDate}`,
    `数据源：${providerUsed}；比赛数：${matchesCount}`,
    `当前总分：${state.currentWorkflowScore ?? "未知"}/100`,
    `目标档：${target.label || "未知目标"}；差距：${target.gap ?? "未知"} 分`,
    `当前优先项：${target.focus || "未知项"}`,
    `目标说明：${target.message || ""}`,
    `今日实验：${target.experiment?.title || "先处理最低分项"}；规则：${target.experiment?.rule || "只做一个改动，观察分数变化。"}`,
    `最近实验结论：${verdict.title}；${verdict.body}`,
    `下一轮策略：${verdict.strategy}`,
    `实验连续性：${workflowExperimentStreakSummary().text}`,
    `实验护栏：${workflowExperimentStreakSummary().guard || "无需暂停，继续单点实验。"}`,
    `最近分数轨迹：${scoreTrail}`,
    `轨迹诊断：${trendDiagnosis}`,
    "实验步骤：",
    ...((target.experiment?.steps || []).map((step, index) => `${index + 1}. ${step}`)),
    "分项评分：",
    ...(scoreLines.length ? scoreLines : ["暂无分项评分"]),
    "候选实验队列：",
    ...(queueLines.length ? queueLines : ["暂无候选实验队列；先完成今日实验。"]),
    "建议加分路线：",
    ...(planLines.length ? planLines : ["暂无加分路线；优先保持数据质量和赛后学习。"]),
  ].join("\n");
}

function workflowTodayExperiment(firstPlan = {}, fallbackFocus = "数据源") {
  const label = firstPlan.label || fallbackFocus || "数据源";
  const acceptance = firstPlan.acceptance || "对应分项分数上升，且用户下一步更清楚。";
  return {
    title: label,
    rule: acceptance
      ? `先做 ${label}，完成后只看这个验收信号：${acceptance}`
      : "先做最低分项，完成后刷新 T+1 并观察总分、分项变化和趋势。",
    steps: [
      `执行 ${label} 对应的一键动作或补齐动作。`,
      `刷新 T+1 今日观察，等待长线分数重新记录。`,
      `只检查验收信号：${acceptance}`,
      "如果分项没有改善，复制长线计划给 DS Pro 复盘原因。",
    ],
  };
}

function renderWorkflowExperimentVerdict() {
  const details = workflowExperimentVerdictDetails();
  if (!details.row) return "";
  return `
    <div class="workflowExperimentVerdict" data-status="${C.escapeHtml(details.status)}">
      <b>${C.escapeHtml(details.title)}</b>
      <span>${C.escapeHtml(details.body)}${workflowScoreDeltaText(details.row)}</span>
      <em>${C.escapeHtml(details.strategy)}</em>
      <small>${C.escapeHtml(workflowExperimentStreakSummary().text)}</small>
    </div>
  `;
}

function renderWorkflowExperimentGuard(guard = {}) {
  if (!guard.guard) return "";
  return `
    <div class="workflowExperimentGuard" data-status="${C.escapeHtml(guard.status || "mixed")}">
      <b>实验护栏</b>
      <span>${C.escapeHtml(guard.guard)}</span>
    </div>
  `;
}

function renderWorkflowExperimentQueue(plan = []) {
  const queue = (plan || []).slice(1, 4);
  if (!queue.length) return "";
  return `
    <div class="workflowExperimentQueue">
      <b>候选实验队列</b>
      ${queue.map((item, index) => `
        <span>${index + 1}. ${C.escapeHtml(item.label)} · 约 +${C.escapeHtml(String(item.lift))} 分 · ${C.escapeHtml(item.action)}</span>
      `).join("")}
      <em>今日只做第一项，后续项等复核后再排；避免一次改太多，看不清哪项真正加分。</em>
    </div>
  `;
}

function workflowExperimentVerdictDetails() {
  const review = (state.workflowActionHistory || []).find((row) => row.action === "today_experiment_review");
  const start = (state.workflowActionHistory || []).find((row) => row.action === "today_experiment");
  const row = review || start;
  if (!row) {
    return {
      row: null,
      status: "none",
      title: "暂无实验结论",
      body: "尚未记录今日实验。",
      strategy: "先记录今日实验，再执行单点动作。",
    };
  }
  const delta = Number(row.score_delta);
  const status = review ? delta > 0 ? "up" : delta < 0 ? "down" : "flat" : "pending";
  const title = review ? "最近实验结论" : "实验已记录，等待复核";
  const body = review
    ? row.message || "实验已复核，请查看分数变化。"
    : row.message || "完成动作并刷新后，点击“标记实验已复核”。";
  const strategy = review
    ? delta > 0
      ? "下一轮策略：保留这个做法，继续处理下一低分项。"
      : delta < 0
        ? "下一轮策略：暂停同方向加码，复制长线计划给 DS Pro 复盘为什么回落。"
        : "下一轮策略：缩小变量，只改一个更具体的子项后再复核。"
    : "下一轮策略：先执行实验动作，刷新 T+1，再复核。";
  return { row, status, title, body, strategy };
}

function workflowExperimentStreakSummary() {
  const reviews = (state.workflowActionHistory || [])
    .filter((row) => row.action === "today_experiment_review")
    .slice(0, 3);
  if (!reviews.length) {
    return { status: "none", text: "实验连续性：暂无复核样本。" };
  }
  const ups = reviews.filter((row) => Number(row.score_delta) > 0).length;
  const downs = reviews.filter((row) => Number(row.score_delta) < 0).length;
  const flats = reviews.length - ups - downs;
  if (reviews.length >= 2 && ups === reviews.length) {
    return { status: "up", text: `实验连续性：最近 ${reviews.length} 次都加分，可以保留该类改法。`, guard: "可以继续同方向小步迭代，但仍保持一次只改一个变量。" };
  }
  if (reviews.length >= 2 && downs >= 2) {
    return { status: "down", text: `实验连续性：最近 ${downs} 次回落，建议暂停同方向改动并复盘。`, guard: "暂停同方向加码：先复制长线计划给 DS Pro 复盘，找到回落原因后再继续。" };
  }
  if (flats >= 2) {
    return { status: "flat", text: `实验连续性：最近 ${flats} 次持平，建议缩小实验变量。`, guard: "不要扩大改动范围：把实验拆得更小，只验证一个子项。" };
  }
  return { status: "mixed", text: `实验连续性：近 ${reviews.length} 次中，加分 ${ups} 次、回落 ${downs} 次、持平 ${flats} 次。` };
}

function workflowTargetLiftPlan(gap = 0) {
  const weightsByLabel = {
    "数据源": 0.22,
    "Top信号": 0.22,
    "组合纪律": 0.20,
    "AI研究": 0.18,
    "赛后学习": 0.18,
  };
  const rows = (state.currentWorkflowItems || [])
    .map((item) => {
      const score = workflowClampScore(item.score);
      const reachable = Math.max(0, Math.min(90, score + 20) - score);
      const lift = Math.max(1, Math.round(reachable * (weightsByLabel[item.label] || 0.18)));
      return {
        label: item.label || "未知项",
        score,
        lift,
        action: item.next || "补齐该项短板",
        acceptance: workflowAcceptanceSignal(item.label),
      };
    })
    .filter((item) => item.score < 90 && item.lift > 0)
    .sort((a, b) => (a.score - b.score) || (b.lift - a.lift));
  if (!rows.length || gap <= 0) return [];
  let remaining = gap;
  const selected = [];
  for (const row of rows) {
    if (selected.length >= 3 || remaining <= 0) break;
    selected.push(row);
    remaining -= row.lift;
  }
  return selected;
}

function workflowAcceptanceSignal(label = "") {
  const map = {
    "数据源": "provider_used 清晰、可售比赛数稳定、无异常 fallback。",
    "Top信号": "Top 单关/进球/比分卡片有可读结论，弱信号不被误当强信号。",
    "组合纪律": "2串1/3串1 有通过门控或被拒原因，未通过时显示暂不组合。",
    "AI研究": "DS Pro 或本地研究摘要已归档，包含可验证假设，并能赛后复盘支持/失败。",
    "赛后学习": "赛果、收盘赔率或 CLV 样本被保存，学习页能看到新复盘。",
  };
  return map[label] || "对应分项分数上升，且用户下一步更清楚。";
}

function workflowExpectedLift(label = "", itemScore = 0, totalScore = 0, status = "loading") {
  if (status === "error") return "预期：恢复服务后重新评分";
  if (itemScore >= 80 && totalScore >= 80) return "预期：保持稳定，赛后继续加样本";
  const map = {
    "数据源": "预期：让赔率/赛程基础更稳",
    "Top信号": "预期：减少弱信号进入组合",
    "组合纪律": "预期：减少高赔率假机会",
    "AI研究": "预期：把解释变成可赛后验证的研究假设",
    "赛后学习": "预期：用赛果和收盘赔率提升长期校准",
  };
  return map[label] || "预期：提高长期工作流分数";
}

function workflowItemNextHint(item = {}) {
  const score = workflowClampScore(item.score);
  if (score >= 90) return "已稳定，继续保留样本。";
  if (score >= 70) return item.next ? `稳住：${item.next}` : "已可用，继续复盘。";
  return item.next ? `补强：${item.next}` : "补强：先处理这个短板。";
}

function workflowScoreContextKey(view = {}) {
  return [
    view.selected_date || view.date || currentDateParam() || "auto",
    view.provider_used || providerParam() || "unknown",
    view.matches_count ?? view.matches_analyzed ?? "unknown",
    view.risk_profile || riskProfileParam() || "aggressive",
  ].join("|");
}

function readWorkflowScoreMemory() {
  try {
    const rows = JSON.parse(window.localStorage.getItem(WORKFLOW_SCORE_MEMORY_KEY) || "[]");
    return Array.isArray(rows) ? rows.filter(Boolean).slice(0, 10) : [];
  } catch (error) {
    return [];
  }
}

function writeWorkflowScoreMemory(rows) {
  try {
    window.localStorage.setItem(WORKFLOW_SCORE_MEMORY_KEY, JSON.stringify((rows || []).slice(0, 10)));
  } catch (error) {
    // Browser localStorage may be unavailable; keep the UI usable.
  }
}

function rememberWorkflowScore(view = {}, score = 0, weakest = {}) {
  const key = workflowScoreContextKey(view);
  const row = {
    context_key: key,
    saved_at: new Date().toISOString(),
    score,
    weakest_label: weakest.label || "未知项",
    weakest_score: workflowClampScore(weakest.score),
    date: view.selected_date || view.date || currentDateParam() || "自动日期",
    provider_used: view.provider_used || providerParam() || "unknown",
    matches_count: view.matches_count ?? view.matches_analyzed ?? "未知",
    risk_profile: view.risk_profile || riskProfileParam() || "aggressive",
    items: (state.currentWorkflowItems || []).map((item) => ({
      label: item.label || "未知项",
      score: workflowClampScore(item.score),
    })),
  };
  const rows = readWorkflowScoreMemory().filter((item) => item.context_key !== key);
  writeWorkflowScoreMemory([row, ...rows]);
}

function renderWorkflowScoreMemory() {
  const rows = readWorkflowScoreMemory();
  const current = rows[0] || {};
  const previous = rows[1] || {};
  if (!current.score && current.score !== 0) return "";
  const delta = Number.isFinite(Number(previous.score)) ? Number(current.score) - Number(previous.score) : null;
  const trend = delta === null
    ? "首次记录这个观察窗口"
    : delta > 0
      ? `较上次 +${delta}`
      : delta < 0
        ? `较上次 ${delta}`
        : "较上次持平";
  const status = delta === null ? "new" : delta > 0 ? "up" : delta < 0 ? "down" : "flat";
  const itemDelta = workflowItemDeltaSummary(current.items || [], previous.items || []);
  const response = workflowScoreResponseRule(status, delta);
  const timeline = workflowScoreTimeline(rows);
  const diagnosis = workflowScoreTrendDiagnosis(rows);
  const nextExperiment = workflowNextExperimentSuggestion(diagnosis, current);
  const copyText = workflowScoreMemoryCopySummary(current, previous, trend, itemDelta, diagnosis, response, nextExperiment);
  return `
    <div class="workflowScoreMemory" data-trend="${C.escapeHtml(status)}">
      <b>长期趋势：${C.escapeHtml(trend)}</b>
      <span>${C.escapeHtml(current.date || "自动日期")} · ${C.escapeHtml(current.provider_used || "unknown")} · ${C.escapeHtml(String(current.matches_count ?? "未知"))} 场</span>
      <em>最低项：${C.escapeHtml(current.weakest_label || "未知项")} ${C.escapeHtml(String(current.weakest_score ?? "N/A"))}/100</em>
      ${timeline}
      <u>${C.escapeHtml(diagnosis)}</u>
      <small>${C.escapeHtml(itemDelta)}</small>
      <i>${C.escapeHtml(response)}</i>
      <mark>${C.escapeHtml(nextExperiment)}</mark>
      <button class="secondary compactButton workflowNextExperimentPlanBtn" type="button">记录下一次实验计划</button>
      <button class="ghost compactButton workflowCopyBtn workflowScoreCopyBtn" type="button" data-copy-text="${C.escapeHtml(copyText)}" data-copy-ok="分数轨迹已复制，可交给 DS Pro 复盘。" data-copy-fail="复制失败，请手动复制。">复制分数轨迹</button>
    </div>
  `;
}

function workflowScoreMemoryCopySummary(current = {}, previous = {}, trend = "", itemDelta = "", diagnosis = "", response = "", nextExperiment = "") {
  const reviewQuestions = workflowScoreReviewQuestions(diagnosis, current);
  return [
    "JC Edge 长线分数轨迹复盘",
    `当前记录：${current.date || "自动日期"} · ${current.provider_used || "unknown"} · ${current.matches_count ?? "未知"} 场`,
    `当前分数：${current.score ?? "未知"}/100；最低项：${current.weakest_label || "未知项"} ${current.weakest_score ?? "N/A"}/100`,
    `上次分数：${previous.score ?? "暂无"}/100`,
    `趋势：${trend || "暂无趋势"}`,
    `最近分数轨迹：${workflowScoreTimelineText()}`,
    diagnosis || "轨迹诊断：暂无。",
    itemDelta || "分项变化：暂无。",
    response || "反应规则：先累计记录。",
    nextExperiment || "下一次实验：先记录基线，再做一个小改动。",
    "请按下面问题复盘：",
    ...reviewQuestions.map((question, index) => `${index + 1}. ${question}`),
  ].join("\n");
}

function workflowNextExperimentSuggestion(diagnosis = "", current = {}) {
  const text = String(diagnosis || "");
  const weakest = current.weakest_label || "最低分项";
  if (text.includes("整体改善")) {
    return `下一次实验：保留本次有效做法，只切换到新的最低分项“${weakest}”，不要扩大改动范围。`;
  }
  if (text.includes("回落")) {
    return `下一次实验：暂停加码“${weakest}”，先回看最近一次改动，把变量缩回一个。`;
  }
  if (text.includes("横盘")) {
    return `下一次实验：把“${weakest}”拆成一个更小动作，只验证一个验收信号。`;
  }
  return `下一次实验：先让 auto 再跑一次 T+1，累计到 3 次轨迹后再判断方向。`;
}

function workflowScoreReviewQuestions(diagnosis = "", current = {}) {
  const text = String(diagnosis || "");
  const weakest = current.weakest_label || "当前最低分项";
  if (text.includes("整体改善")) {
    return [
      "这次加分主要来自哪一个动作：数据源、Top信号、组合纪律、AI研究还是赛后学习？",
      "这个动作是否可以保留为日常流程，而不是继续扩大改动范围？",
      `下一轮是否应该转向新的最低分项：${weakest}？`,
    ];
  }
  if (text.includes("回落")) {
    return [
      "最近一次改动是否同时改变了多个变量，导致无法判断回落来源？",
      "是否为了输出更多组合而牺牲了可信度门控或高赔率冷门纪律？",
      `是否应该暂停 ${weakest} 方向的加码，先恢复到上一次较高分配置？`,
    ];
  }
  if (text.includes("横盘")) {
    return [
      "当前实验是否太粗，例如同时改了数据源、AI解释和组合展示？",
      `能否把 ${weakest} 拆成一个更小验收项，只观察一次分数变化？`,
      "是否缺少赛后学习样本，导致页面体验改善但长期分数不动？",
    ];
  }
  return [
    "当前样本是否足够判断趋势？如果不足，先多跑几次 T+1 auto 记录。",
    `最低分项 ${weakest} 的验收标准是否已经被满足？`,
    "下一轮是否只改一个变量，并记录分数变化？",
  ];
}

function workflowScoreTimeline(rows = []) {
  const points = (rows || []).slice(0, 6).reverse();
  if (points.length < 2) return "";
  return `
    <div class="workflowScoreTimeline" aria-label="最近长线分数轨迹">
      ${points.map((row) => {
        const score = workflowClampScore(row.score);
        return `<span style="height:${C.escapeHtml(String(Math.max(12, Math.min(52, score / 2))))}px" title="${C.escapeHtml(`${row.date || "自动日期"} · ${score}/100`)}"><b>${C.escapeHtml(String(score))}</b></span>`;
      }).join("")}
    </div>
  `;
}

function workflowScoreTimelineText(rows = readWorkflowScoreMemory()) {
  const points = (rows || []).slice(0, 6).reverse();
  if (!points.length) return "暂无分数轨迹。";
  return points.map((row) => `${row.date || "自动日期"} ${workflowClampScore(row.score)}/100`).join(" → ");
}

function workflowScoreTrendDiagnosis(rows = readWorkflowScoreMemory()) {
  const points = (rows || []).slice(0, 6).reverse().map((row) => workflowClampScore(row.score));
  if (points.length < 3) return "轨迹诊断：样本还少，先累计至少 3 次刷新/实验记录。";
  const first = points[0];
  const last = points[points.length - 1];
  const deltas = points.slice(1).map((score, index) => score - points[index]);
  const ups = deltas.filter((delta) => delta > 0).length;
  const downs = deltas.filter((delta) => delta < 0).length;
  const flats = deltas.length - ups - downs;
  if (last - first >= 8 && ups >= downs) return "轨迹诊断：整体改善，保留当前 auto + DS + 单点实验节奏。";
  if (first - last >= 8 || downs >= 2) return "轨迹诊断：出现回落，暂停扩大组合和权重调整，先复盘最近一次改动。";
  if (flats >= 2 || Math.abs(last - first) <= 3) return "轨迹诊断：基本横盘，说明实验颗粒太粗，下一轮拆成更小动作。";
  return "轨迹诊断：波动中，继续只改一个变量，并用赛后学习验证。";
}

function workflowScoreResponseRule(status = "new", delta = null) {
  if (status === "up") return "反应规则：这次改动有效，保留做法；下一轮处理新的最低分项。";
  if (status === "down") return "反应规则：分数回落，暂停同方向加码；复制长线计划给 DS Pro 复盘原因。";
  if (status === "flat") return "反应规则：分数持平，说明变量太粗；下一轮只改一个更小的子项。";
  return "反应规则：这是当前窗口基线；先记录，再做单点实验。";
}

function workflowItemDeltaSummary(currentItems = [], previousItems = []) {
  if (!currentItems.length) return "分项变化：暂无分项记录。";
  if (!previousItems.length) {
    return `分项基线：${currentItems.map((item) => `${item.label} ${workflowClampScore(item.score)}`).join("；")}`;
  }
  const previousByLabel = new Map(previousItems.map((item) => [item.label, workflowClampScore(item.score)]));
  const deltas = currentItems
    .map((item) => {
      const current = workflowClampScore(item.score);
      const previous = previousByLabel.get(item.label);
      if (!Number.isFinite(Number(previous))) return null;
      return { label: item.label, delta: current - previous, current };
    })
    .filter(Boolean)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  const changed = deltas.filter((item) => item.delta !== 0).slice(0, 3);
  if (!changed.length) return "分项变化：五项评分暂无明显变化。";
  return `分项变化：${changed.map((item) => `${item.label} ${item.delta > 0 ? "+" : ""}${item.delta}`).join("；")}`;
}

function workflowQuickActionButton(item = {}) {
  const label = item.label || "";
  const actions = {
    "数据源": { action: "refresh_today", text: "重新读取下一可售日比赛" },
    "Top信号": { action: "run_optimizer", text: "重新生成 Top 信号" },
    "组合纪律": { action: "best_parlay", text: "查看组合纪律" },
    "AI研究": { action: "ai_research", text: "运行 DS Pro 自动研究" },
    "赛后学习": { action: "learning_pack", text: "准备赛后学习包" },
  };
  const config = actions[label];
  if (!config) return "";
  return `<button class="secondary compactButton workflowQuickActionBtn" type="button" data-workflow-action="${C.escapeHtml(config.action)}">${C.escapeHtml(config.text)}</button>`;
}

function workflowActionStatusText(action = "") {
  const messages = {
    refresh_today: "正在重新读取 T+1 可售比赛、赔率和情报覆盖。",
    run_optimizer: "正在重新生成 Top 单关、进球/比分和组合观察。",
    best_parlay: "正在打开组合纪律，查看通过门控/未过门控原因。",
    ai_research: "正在启动 DS Pro 自动研究；完成后会写入今日 AI 研究记录。",
    learning_pack: "正在准备赛后学习包，用比分和收盘赔率校准长期分数。",
  };
  return messages[action] || "正在处理当前瓶颈。";
}

function workflowActionLabel(action = "") {
  const labels = {
    refresh_today: "数据源",
    run_optimizer: "Top信号",
    best_parlay: "组合纪律",
    ai_research: "AI研究",
    learning_pack: "赛后学习",
    today_experiment: "今日实验",
    today_experiment_review: "实验复核",
    next_experiment_plan: "下一次实验",
  };
  return labels[action] || "瓶颈动作";
}

function workflowActionDoneText(action = "") {
  const messages = {
    refresh_today: "已完成 T+1 比赛和数据源刷新，请查看分数是否改善。",
    run_optimizer: "已完成 Top 信号生成，请查看单关、进球/比分和组合候选。",
    best_parlay: "已打开组合纪律，请重点看通过/未过门控原因。",
    ai_research: "AI 研究动作已完成，请查看今日 DS/本地研究摘要和 Top 覆盖。",
    learning_pack: "赛后学习包已准备，请继续补比分、收盘赔率和复盘样本。",
  };
  return messages[action] || "当前瓶颈动作已完成。";
}

function recordTodayExperimentStart() {
  const existing = (state.workflowActionHistory || []).find((row) => row.action === "today_experiment" && row.status === "planned");
  if (existing) {
    setStatus("Check", "已有一个待复核的今日实验；请先执行并复核，再记录新的实验。");
    return;
  }
  const target = state.currentWorkflowTarget || {};
  const experiment = target.experiment || {};
  const message = experiment.title
    ? `开始单点实验：${experiment.title}；验收：${experiment.rule || "刷新后看分项变化。"}`
    : "开始单点实验；刷新后观察总分、分项变化和趋势。";
  recordWorkflowAction("today_experiment", message, "planned", {
    score_before: state.currentWorkflowScore,
  });
  if (state.todayView) renderWorkflowScore(state.todayView, "ready");
  setStatus("Ready", "今日实验已记录；完成动作后刷新 T+1 观察看分数变化。");
}

function reviewTodayExperiment() {
  const start = (state.workflowActionHistory || []).find((row) => row.action === "today_experiment" && row.status === "planned");
  if (!start) {
    setStatus("Check", "没有待复核的今日实验；请先记录或开始执行一个实验计划。");
    return;
  }
  const before = Number.isFinite(Number(start.score_before)) ? Number(start.score_before) : Number(start.score_after);
  const after = Number(state.currentWorkflowScore);
  const delta = Number.isFinite(before) && Number.isFinite(after) ? after - before : null;
  const verdict = delta === null
    ? "无法计算分数变化，请先刷新 T+1 今日观察。"
    : delta > 0
      ? `实验有效：长线分数 +${delta}。`
      : delta < 0
        ? `实验回落：长线分数 ${delta}，需要复盘原因。`
        : "实验持平：长线分数未变化，需要看分项是否改善。";
  const target = state.currentWorkflowTarget || {};
  const experiment = target.experiment || {};
  recordWorkflowAction("today_experiment_review", `${verdict} 实验项：${experiment.title || start.label || "未知项"}`, "done", {
    score_before: Number.isFinite(before) ? before : null,
    score_after: Number.isFinite(after) ? after : null,
  });
  closeWorkflowPlannedAction(start.saved_at, "已完成实验复核。", {
    score_after: Number.isFinite(after) ? after : null,
  });
  if (state.todayView) renderWorkflowScore(state.todayView, "ready");
  setStatus(delta !== null && delta < 0 ? "Check" : "Ready", verdict);
}

function recordNextExperimentPlan() {
  const rows = readWorkflowScoreMemory();
  const current = rows[0] || {};
  const diagnosis = workflowScoreTrendDiagnosis(rows);
  const suggestion = workflowNextExperimentSuggestion(diagnosis, current);
  recordWorkflowAction("next_experiment_plan", suggestion, "planned");
  if (state.todayView) renderWorkflowScore(state.todayView, "ready");
  setStatus("Ready", "下一次实验计划已记录；执行时只改一个变量。");
}

function startPlannedExperiment() {
  const existing = (state.workflowActionHistory || []).find((row) => row.action === "today_experiment" && row.status === "planned");
  if (existing) {
    setStatus("Check", "已有今日实验正在等待复核；请先执行并复核它。");
    return;
  }
  const plan = (state.workflowActionHistory || []).find((row) => row.action === "next_experiment_plan" && row.status === "planned");
  if (!plan) {
    setStatus("Check", "还没有可执行的实验计划，请先记录下一次实验计划。");
    return;
  }
  recordWorkflowAction("today_experiment", `开始执行已记录计划：${plan.message || "只改一个变量并刷新 T+1。"}`, "planned", {
    score_before: state.currentWorkflowScore,
  });
  closeWorkflowPlannedAction(plan.saved_at, "已转为今日实验，等待执行和复核。");
  if (state.todayView) renderWorkflowScore(state.todayView, "ready");
  setStatus("Ready", "已把计划转为今日实验；执行动作后刷新 T+1，再标记实验复核。");
}

function closeWorkflowPlannedAction(savedAt = "", message = "计划已处理。", options = {}) {
  if (!savedAt) return;
  state.workflowActionHistory = (state.workflowActionHistory || []).map((row) => {
    if (row.saved_at !== savedAt) return row;
    const after = Number.isFinite(Number(options.score_after)) ? Number(options.score_after) : row.score_after;
    const before = Number.isFinite(Number(row.score_before)) ? Number(row.score_before) : null;
    return {
      ...row,
      status: "done",
      message: `${row.message || ""} ${message}`.trim(),
      score_after: after ?? null,
      score_delta: before !== null && Number.isFinite(Number(after)) ? Number(after) - before : row.score_delta,
    };
  });
  writeWorkflowActionHistory(state.workflowActionHistory);
}

function recordWorkflowAction(action = "", message = "", status = "running", options = {}) {
  const before = Number.isFinite(Number(options.score_before)) ? Number(options.score_before) : null;
  const after = Number.isFinite(Number(options.score_after)) ? Number(options.score_after) : null;
  const label = workflowActionLabel(action);
  const entry = {
    action,
    label,
    message,
    status,
    time: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
    saved_at: new Date().toISOString(),
    score_before: before,
    score_after: after,
    score_delta: before !== null && after !== null ? after - before : null,
  };
  const history = state.workflowActionHistory || [];
  const latest = history[0] || {};
  const shouldUpdateLatest = latest.label === label && latest.status === "running" && status !== "running";
  const nextHistory = shouldUpdateLatest
    ? [{ ...latest, ...entry, time: latest.time || entry.time, score_before: latest.score_before ?? entry.score_before }, ...history.slice(1)]
    : [entry, ...history];
  state.lastWorkflowAction = entry;
  state.workflowActionHistory = nextHistory.slice(0, 6);
  writeWorkflowActionHistory(state.workflowActionHistory);
}

function renderWorkflowActionHistory() {
  const rows = (state.workflowActionHistory || []).slice(1, 3);
  if (!rows.length) return "";
  return `
    <div class="workflowActionHistory">
      <div class="workflowActionHistoryHead">
        <span>最近处理</span>
        <button class="ghost compactButton workflowClearHistoryBtn" type="button">清空</button>
      </div>
      ${rows.map((row) => `<p data-status="${C.escapeHtml(row.status || "running")}">${C.escapeHtml(workflowActionTimeLabel(row))} · ${C.escapeHtml(row.label)} · ${C.escapeHtml(row.message)}${workflowScoreDeltaText(row)}</p>`).join("")}
    </div>
  `;
}

function workflowActionTimeLabel(row = {}) {
  const savedAt = row.saved_at ? new Date(row.saved_at) : null;
  if (!savedAt || Number.isNaN(savedAt.getTime())) return row.time || "--:--";
  const now = new Date();
  const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startSaved = new Date(savedAt.getFullYear(), savedAt.getMonth(), savedAt.getDate()).getTime();
  const hhmm = savedAt.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  if (startSaved === startToday) return `今天 ${hhmm}`;
  if (startSaved === startToday - 24 * 60 * 60 * 1000) return `昨天 ${hhmm}`;
  return `${savedAt.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" })} ${hhmm}`;
}

function renderWorkflowActionTrend() {
  const recent = (state.workflowActionHistory || []).slice(0, 6);
  if (recent.length < 2) return "";
  const scoreRows = recent.filter((row) => row.status === "done" && !["next_experiment_plan", "today_experiment"].includes(row.action));
  const failedRows = recent.filter((row) => row.status === "error");
  const plannedRows = recent.filter((row) => row.status === "planned");
  const failedCount = failedRows.length;
  const retryAction = failedRows[0]?.action || "";
  const deltas = scoreRows.map((row) => Number(row.score_delta)).filter((value) => Number.isFinite(value));
  if (!deltas.length && !failedCount && plannedRows.length) {
    const plannedSummary = workflowTrendCopySummary({
      label: "已有实验计划",
      recent,
      scoreSummary: "计划已记录，尚未执行完成动作",
      failedCount: 0,
      next: "顺序：先点“开始执行计划”，完成对应动作并刷新 T+1，再点“执行后复核”。",
    });
    return `
      <div class="workflowActionTrend" data-trend="planned">
        <b>已有实验计划</b>
        <span>最近记录了 ${C.escapeHtml(String(plannedRows.length))} 个计划，尚未形成可计算的分数变化。</span>
        <em>先执行计划，刷新 T+1，再用实验复核判断是否真的加分。</em>
        <div class="workflowTrendActions">
          <button class="secondary compactButton workflowStartPlannedExperimentBtn" type="button">开始执行计划</button>
          <button class="ghost compactButton workflowExperimentReviewBtn" type="button">执行后复核</button>
          <button class="secondary compactButton workflowCopyBtn" type="button" data-copy-text="${C.escapeHtml(plannedSummary)}" data-copy-ok="计划摘要已复制，可交给 DS Pro 复盘。" data-copy-fail="计划摘要复制失败，请手动选中文本。">复制计划摘要</button>
        </div>
      </div>
    `;
  }
  if (!deltas.length && !failedCount) return "";
  const total = deltas.reduce((sum, value) => sum + value, 0);
  const avg = deltas.length ? Math.round((total / deltas.length) * 10) / 10 : 0;
  const improved = deltas.filter((value) => value > 0).length;
  const label = failedCount && avg <= 0 ? "最近需要复查" : avg > 0 ? "最近修分有效" : avg < 0 ? "最近修分回落" : "最近修分持平";
  const next = avg > 0
    ? "继续沿着最低分项处理，优先保留有效动作。"
    : failedCount
      ? "先处理失败动作，再继续叠加新的优化。"
      : avg < 0
      ? "先复查最近失败或降分动作，不要继续盲目叠加。"
      : "需要更多动作样本，或优先处理更低分短板。";
  const scoreSummary = deltas.length
    ? `完成动作平均变化 ${avg > 0 ? "+" : ""}${String(avg)} 分，${improved}/${deltas.length} 次提升`
    : "完成动作暂无可计算分数";
  const trendSummary = workflowTrendCopySummary({ label, recent, scoreSummary, failedCount, next });
  return `
    <div class="workflowActionTrend" data-trend="${avg > 0 ? "up" : avg < 0 || failedCount ? "down" : "flat"}">
      <b>${C.escapeHtml(label)}</b>
      <span>近 ${recent.length} 次中，${C.escapeHtml(scoreSummary)}${failedCount ? `，${failedCount} 次需要检查` : ""}。</span>
      <em>${C.escapeHtml(next)}</em>
      <div class="workflowTrendActions">
        ${retryAction ? `<button class="secondary compactButton workflowQuickActionBtn" type="button" data-workflow-action="${C.escapeHtml(retryAction)}">重试最近失败项</button>` : ""}
        <button class="secondary compactButton workflowCopyBtn" type="button" data-copy-text="${C.escapeHtml(trendSummary)}" data-copy-ok="趋势摘要已复制，可用于复盘或 DS 研究。" data-copy-fail="趋势摘要复制失败，请手动选中文本。">复制趋势摘要</button>
        <button class="ghost compactButton workflowClearHistoryBtn" type="button">重置观察窗口</button>
      </div>
    </div>
  `;
}

function workflowTrendCopySummary({ label = "", recent = [], scoreSummary = "", failedCount = 0, next = "" } = {}) {
  const bottleneck = state.currentWorkflowBottleneck || {};
  const today = state.todayView || {};
  const observationDate = today.selected_date || today.date || currentDateParam() || "自动日期";
  const providerUsed = today.provider_used || providerParam() || "unknown";
  const matchesCount = today.matches_count ?? today.matches_analyzed ?? "未知";
  const riskProfile = today.risk_profile || riskProfileParam() || "aggressive";
  const generatedAt = new Date().toLocaleString("zh-CN", { hour12: false });
  const ai = state.latestAiResearch || {};
  const aiProvider = ai.ai_provider_resolved || ai.ai_provider_requested || ai.provider || ai.ai_summary?.provider || "未运行";
  const aiStatus = ai.ai_summary?.status || ai.status || (ai.ds_completed ? "loaded" : "unknown");
  const dsStatus = ai.ds_completed ? "DS Pro 已完成" : ai.ds_attempted ? "DS Pro 已尝试但未完成" : "DS Pro 未参与/未记录";
  const scoreLines = (state.currentWorkflowItems || []).map((item, index) => (
    `${index + 1}. ${item.label}: ${item.score}/100${item.detail ? ` · ${item.detail}` : ""}${item.next ? ` · 下一步：${item.next}` : ""}`
  ));
  const doneCount = recent.filter((row) => row.status === "done" && !["next_experiment_plan", "today_experiment"].includes(row.action)).length;
  const plannedCount = recent.filter((row) => row.status === "planned" || row.action === "next_experiment_plan").length;
  const runningCount = recent.filter((row) => row.status === "running").length;
  const actionLines = recent.slice(0, 6).map((row, index) => {
    const status = row.status === "done" ? "完成" : row.status === "error" ? "需检查" : row.status === "planned" ? "计划" : "处理中";
    const delta = workflowScoreDeltaPlain(row);
    return `${index + 1}. ${workflowActionTimeLabel(row)} · ${row.label || "未知短板"} · ${status}${delta ? ` · ${delta}` : ""} · ${row.message || ""}`;
  });
  return [
    `生成时间：${generatedAt}`,
    `观察日期：${observationDate}`,
    `数据上下文：数据源 ${providerUsed}，可售/分析比赛 ${matchesCount} 场，风险档位 ${riskProfile}`,
    `AI上下文：${aiProvider} · ${aiStatus} · ${dsStatus}`,
    `当前总分：${state.currentWorkflowScore ?? "未知"}/100`,
    `长线目标：${state.currentWorkflowTarget?.label || "未知目标"}；差距：${state.currentWorkflowTarget?.gap ?? "未知"} 分`,
    "分项评分：",
    ...(scoreLines.length ? scoreLines : ["暂无分项评分"]),
    `当前瓶颈：${bottleneck.title || "未知"}；${bottleneck.impact || "暂无影响说明"}；建议：${bottleneck.action || "继续按最低分项处理。"}`,
    `动作结构：完成 ${doneCount} 次；计划 ${plannedCount} 次；处理中 ${runningCount} 次；需检查 ${failedCount} 次。计划和实验基线不参与平均分变化。`,
    `${label}：近 ${recent.length} 次中，${scoreSummary}${failedCount ? `，${failedCount} 次需要检查` : ""}。`,
    `下一步：${next}`,
    "最近动作：",
    ...actionLines,
  ].join("\n");
}

function workflowScoreDeltaPlain(row = {}) {
  const before = Number(row.score_before);
  const after = Number(row.score_after);
  if (!Number.isFinite(before) || !Number.isFinite(after)) return "";
  const delta = after - before;
  const sign = delta > 0 ? "+" : "";
  return `分数 ${before}→${after} (${delta ? `${sign}${delta}` : "0"})`;
}

function workflowScoreDeltaText(row = {}) {
  const before = Number(row.score_before);
  const after = Number(row.score_after);
  if (!Number.isFinite(before) || !Number.isFinite(after)) return "";
  const delta = after - before;
  const sign = delta > 0 ? "+" : "";
  const status = delta > 0 ? "up" : delta < 0 ? "down" : "flat";
  const label = delta ? `${sign}${delta}` : "0";
  return ` <span class="workflowScoreDelta" data-delta="${status}" title="分数 ${C.escapeHtml(String(before))}→${C.escapeHtml(String(after))}">${C.escapeHtml(label)}</span>`;
}

function workflowActionErrorText(action = "", error = null) {
  const suffix = error && error.message ? `；细节：${error.message}` : "";
  const messages = {
    refresh_today: "重新读取比赛失败，请检查本地服务、数据源 key 或稍后重试",
    run_optimizer: "Top 信号生成失败，请先确认比赛和赔率数据是否已读到",
    best_parlay: "组合纪律读取失败，请先刷新今日观察再重试",
    ai_research: "DS Pro 自动研究未完成，请检查 key、本地服务状态或稍后重试",
    learning_pack: "赛后学习包准备失败，请确认赛果/收盘赔率样本是否存在",
  };
  return `${messages[action] || "当前瓶颈动作未完成"}${suffix}`;
}

async function workflowRunQuickAction(action = "") {
  if (action === "refresh_today") return runOneClickObservation();
  if (action === "run_optimizer") return runOptimizer(true);
  if (action === "best_parlay") return runOneClickObservation();
  if (action === "ai_research") return loadAiComboResearch();
  if (action === "learning_pack") return prepareDailyLearningPack();
  setStatus("Ready", "未识别的瓶颈动作，已保持当前页面。");
  return null;
}

function clearWorkflowActionHistory() {
  state.lastWorkflowAction = null;
  state.workflowActionHistory = [];
  writeWorkflowActionHistory([]);
  if (state.todayView) renderWorkflowScore(state.todayView, "ready");
  setStatus("Ready", "已清空最近处理历史，长线趋势将从下一次动作重新累计。");
}

async function copyTextToClipboard(text = "") {
  const value = String(text || "").trim();
  if (!value) return false;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(value);
    return true;
  }
  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "readonly");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  const ok = document.execCommand("copy");
  document.body.removeChild(textarea);
  return ok;
}

function renderScanCalendar(view) {
  const panel = qs("#scanCalendarPanel");
  if (!panel) return;
  const attempts = view?.attempts || view?.source_health?.attempts || [];
  const selected = view?.selected_date || view?.date || "";
  if (!attempts.length) {
    panel.innerHTML = `
      <div class="scanCalendarCard isLoading">
        <span>SCAN</span>
        <strong>正在扫描未来比赛窗口</strong>
        <p>会完整查看 T+1 到 T+3 窗口，选第一个有可售比赛的日期作为主观察日。</p>
      </div>
    `;
    return;
  }
  const windowInfo = view.source_health?.scan_window || view.scan_window || {};
  panel.innerHTML = `
    <div class="scanCalendarHead">
      <span>DATE SCAN</span>
      <strong>未来窗口日历</strong>
      <p>${C.escapeHtml(windowInfo.selection_rule || "完整扫描未来窗口，选择第一个有可售比赛的日期。")}</p>
    </div>
    <div class="scanCalendarGrid">
      ${attempts.map((item) => {
        const count = Number(item.matches_count || 0);
        const status = count > 0 ? "available" : String(item.status || "empty");
        const selectedClass = item.date === selected ? " isSelected" : "";
        const label = count > 0 ? `${count} 场` : "暂无";
        const provider = item.provider_used || item.provider || "unknown";
        return `
          <article class="scanDay scanDay-${C.escapeHtml(status)}${selectedClass}">
            <span>${C.escapeHtml(item.date || "日期待定")}</span>
            <strong>${C.escapeHtml(label)}</strong>
            <p>${C.escapeHtml(provider)} · ${C.escapeHtml(status)}</p>
            ${item.date === selected ? `<em>主观察日</em>` : `<em>参考日</em>`}
          </article>
        `;
      }).join("")}
    </div>
  `;
}


function renderExternalSignalsStrip(view) {
  const panel = qs("#externalSignalsStrip");
  if (!panel) return;
  const status = view?.external_signals_status || {};
  if (!view) {
    panel.innerHTML = `
      <article class="externalSignalsCard isLoading">
        <span>INTEL</span>
        <strong>等待情报覆盖审计</strong>
        <p>如果高级设置里填写了本地情报 JSON，首页会显示已提供字段和匹配情况。</p>
      </article>
    `;
    return;
  }
  const supplied = status.supplied_fields_zh || status.supplied_fields || [];
  const matched = Number(status.matched_count || 0);
  const total = Number(status.matches_count || 0);
  const loaded = status.load_status === "loaded" && status.source_type === "user_json";
  const quality = !loaded ? "notProvided" : matched > 0 ? "matched" : "unmatched";
  const title = !loaded ? "本地情报未接入" : matched > 0 ? "本地情报已匹配部分比赛" : "本地情报已读取但未匹配当前比赛";
  const body = !loaded
    ? "伤停、首发、天气、新闻和战意保持未知；系统不会编造。"
    : matched > 0
      ? `已识别字段：${supplied.join("、") || "暂无"}；匹配 ${matched}/${total || "?"} 场。`
      : `已读取 ${status.path_label || "情报 JSON"}，但没有匹配当前主观察日；可检查 match_no / 队名 / 日期。`;
  const missing = Array.isArray(view.missing_signals) ? view.missing_signals.slice(0, 6) : [];
  panel.innerHTML = `
    <article class="externalSignalsCard ${quality}">
      <span>INTEL COVERAGE</span>
      <strong>${C.escapeHtml(title)}</strong>
      <p>${C.escapeHtml(body)}</p>
      <div class="externalSignalsTags">
        ${(supplied.length ? supplied : ["伤停", "首发", "天气", "新闻", "战意"].filter(Boolean)).slice(0, 8).map((item) => `<em class="${supplied.length ? "isSupplied" : "isMissing"}">${C.escapeHtml(item)}</em>`).join("")}
      </div>
      ${missing.length ? `<small>仍影响信心：${C.escapeHtml(missing.join("、"))}</small>` : ""}
    </article>
  `;
}


function renderTodayTimeoutState(payload = {}) {
  stopTodayProgressTicker();
  renderWorkflowScore(null, "slow");
  renderScanCalendar(null);
  renderExternalSignalsStrip(null);
  const message = payload.error?.message || "首页预读没有在等待时间内完成。";
  setAiAutoStatus("fallback", "先进入赛前优化", "首页不再卡死等待数据源；点击“生成今日观察”会直接生成单关、2串1、3串1纸面候选。");
  setTodayQuickActionStatus("当前：首页预读未完成，建议直接生成今日观察");
  setNodeHtml("#todayOneLook", actionableTodayFallback(message));
  const fallbackMap = {
    "#todaySingles": ["先生成今日观察", "下一步直接生成每日单关、2串1、3串1纸面候选，不等待首页完整扫描。"],
    "#todayParlay2": ["2串1候选待生成", "赛前优化会给候选榜和拒绝原因，未过门控也会留下赛后复盘样本。"],
    "#todayParlay3": ["3串1候选待生成", "只作为高风险纸面候选，不包装成强观察。"],
    "#todayTotalGoals": ["进球倾向待生成", "进入比分/进球数页或生成今日观察后更新。"],
    "#todayScores": ["比分参考待生成", "比分只作倾向参考，等待模型矩阵返回。"],
  };
  Object.entries(fallbackMap).forEach(([selector, [title, body]]) => {
    const target = qs(selector);
    if (target) target.innerHTML = `<div class="emptyState"><strong>${C.escapeHtml(title)}</strong><p>${C.escapeHtml(body)}</p></div>`;
  });
}

function actionableTodayFallback(message = "") {
  return `
    <section class="todayActionFallback">
      <div>
        <span>FAST PATH</span>
        <strong>先跑赛前优化，不等首页预读</strong>
        <p>${C.escapeHtml(message || "数据源预读较慢时，首页不再停在空状态。赛前优化会直接产出每日单关、2串1、3串1纸面候选。")}</p>
      </div>
      <div class="todayFallbackSteps">
        <article><b>1</b><strong>单关</strong><p>先看赔率是否覆盖模型概率。</p></article>
        <article><b>2</b><strong>2串1</strong><p>每天给纸面候选，检查同向和相关性。</p></article>
        <article><b>3</b><strong>3串1</strong><p>只作高波动复盘，不包装成强结论。</p></article>
      </div>
      <button type="button" class="primary" id="todayFallbackOptimizerBtn">生成今日观察</button>
    </section>
  `;
}

function renderTodayLoadingState() {
  renderWorkflowScore(null, "loading");
  renderScanCalendar(null);
  renderExternalSignalsStrip(null);
  setAiAutoStatus("running", "自动研究下一可售日比赛中", "先找今日到未来几天的可售比赛，随后自动尝试 DeepSeek Pro 研究摘要。若暂不可用，会改用本地研究摘要。");
  safeClearNode("#todayOneLook");
  setTodayQuickActionStatus("当前：正在读取下一可售比赛与赔率，结果返回后会自动更新。");
  const loadingMap = {
    "#todaySingles": ["Top 单关读取中", "先筛单关，再判断是否能做组合。"],
    "#todayParlay2": ["2串1纪律读取中", "组合需要同时命中，会先过可信度和相关性折扣。"],
    "#todayParlay3": ["3串1纸面候选读取中", "只作为高风险纸面候选，不自动升级为强观察。"],
    "#todayTotalGoals": ["总进球倾向读取中", "用于判断节奏，不替代胜平负观察。"],
    "#todayScores": ["比分倾向读取中", "比分波动较高，只显示模型倾向。"],
  };
  Object.entries(loadingMap).forEach(([selector, [title, body]]) => {
    const target = qs(selector);
    if (target) target.innerHTML = loadingTopCard(title, body);
  });
  const box = qs("#aiComboResearchBox");
  if (box) {
    box.innerHTML = `
      <div class="aiRunningCard">
        <span>自动研究队列</span>
        <strong>等待 auto 自动研究</strong>
        <p>比赛与候选回来后会自动触发，无需再手动点第二次。</p>
      </div>
    `;
  }
}


function signalCards(rows, kind = "single", message = "暂无观察信号") {
  if (!rows || !rows.length) return `<div class="emptyState">${C.escapeHtml(message)}</div>`;
  return `<div class="signalCardGrid">${rows.slice(0, 4).map((row, index) => {
    const isCombo = kind === "combo";
    const isScore = kind === "score";
    const isTotalGoals = kind === "total_goals";
    const title = isCombo
      ? (row.legs || row.match || "组合观察")
      : (isScore || isTotalGoals)
        ? [row.match || "模型倾向", row.direction || ""].filter(Boolean).join(" · ")
        : (row.match || "观察信号");
    const tag = isCombo ? (row.status || row.type || "组合") : `${row.play_type || "玩法"} · ${row.direction || "方向"}`;
    const reason = isCombo ? (row.discipline_summary_zh || row.reject_reason || row.reason || "通过组合纪律筛选。") : (row.recommended_action_zh || row.selection_reason || "查看概率、EV 和风险。");
    const decision = isCombo ? (row.combo_decision_label_zh || row.status || "") : (row.decision_label_zh || row.signal_category_zh || "");
    const comboReview = isCombo ? comboMatchdayReview(row) : null;
    const learningScores = !isCombo && row.learning_scores ? row.learning_scores : null;
    const metrics = isCombo
      ? [
          ["组合赔率", row.odds],
          ["盈亏线", row.break_even_prob || "N/A"],
          ["组合概率", row.model_prob],
          ["安全边际", row.safety_margin || "N/A"],
          ["判断", row.combo_decision_label_zh || row.risk_level],
        ]
      : [
          ["赔率", row.official_odds],
          ["盈亏线", row.break_even_prob || "N/A"],
          ["校准概率", row.calibrated_prob || row.model_prob],
          ["安全边际", row.safety_margin || "N/A"],
          ["判断", row.safety_margin_label_zh || row.signal_category_zh || "观察"],
        ];
    return `
      <article class="signalCard ${isCombo && isComboRejected(row) ? "isRejected" : ""}">
        <div class="signalHead">
          <strong>${C.escapeHtml(title)}</strong>
          <span>${C.escapeHtml(tag)}</span>
        </div>
        ${decision ? `<div class="coachDecision">${C.escapeHtml(decision)}</div>` : ""}
        ${!isCombo && row.signal_category_zh ? `<div class="signalTypeLine">${C.escapeHtml(row.signal_category_zh)} · ${C.escapeHtml(row.odds_bucket_zh || "")}</div>` : ""}
        <div class="metricStrip">${metrics.map(([label, value]) => `
          <div><span>${C.escapeHtml(label)}</span><b>${C.escapeHtml(value ?? "N/A")}</b></div>
        `).join("")}</div>
        ${!isCombo && row.odds_coach_verdict_zh ? `<p class="coachActionLine">${C.escapeHtml(row.odds_coach_verdict_zh)}</p>` : ""}
        ${learningScores ? `<div class="learningScoreStrip">
          <strong>${C.escapeHtml(learningScores.verdict_zh || "机器学习结论：待评估")}</strong>
          <div><span>赔率价值</span><b>${C.escapeHtml(learningScores.odds_value_score ?? "N/A")}</b></div>
          <div><span>历史学习</span><b>${C.escapeHtml(learningScores.history_score ?? "N/A")}</b></div>
          <div><span>CLV价格</span><b>${C.escapeHtml(learningScores.clv_score ?? "N/A")}</b></div>
          <div><span>临场复核</span><b>${C.escapeHtml(learningScores.matchday_review_score ?? "N/A")}</b></div>
          <div><span>串联资格</span><b>${C.escapeHtml(learningScores.parlay_fit_score ?? "N/A")}</b></div>
        </div>` : ""}
        ${!isCombo && row.learning_score_summary_zh ? `<p class="edgeCoachLine">${C.escapeHtml(row.learning_score_summary_zh)}</p>` : ""}
        <p class="reasonLine">${C.escapeHtml(reason)}</p>
        ${isCombo && row.combo_action_zh ? `<p class="coachActionLine">${C.escapeHtml(row.combo_action_zh)}</p>` : ""}
        ${isCombo && row.combo_value_reading_zh ? `<p class="edgeCoachLine">${C.escapeHtml(row.combo_value_reading_zh)}</p>` : ""}
        ${isCombo && row.combo_parlay_policy_zh ? `<p class="mutedLine">串联纪律：${C.escapeHtml(row.combo_parlay_policy_zh)}</p>` : ""}
        ${isCombo && comboReview ? `<div class="oddsReviewMini comboOddsReview">
          <strong>组合赔率复核</strong>
          <p>${C.escapeHtml(comboReview.message_zh)}</p>
          <span>保留观察最低组合赔率：${C.escapeHtml(comboReview.keepMinText)}</span>
          <span>失去覆盖低于：${C.escapeHtml(comboReview.noValueBelowText)}</span>
          <span>反向漂移警戒：${C.escapeHtml(comboReview.reverseWatchText)}</span>
          <div class="matchdayReviewTool">
            <input inputmode="decimal" placeholder="填最新组合赔率，如 3.50" aria-label="临场组合赔率">
            <button type="button" class="matchdayReviewBtn"
              data-keep-min="${C.escapeHtml(comboReview.keepMin)}"
              data-no-value-below="${C.escapeHtml(comboReview.noValueBelow)}"
              data-reverse-watch="${C.escapeHtml(comboReview.reverseWatch)}"
              data-target="${C.escapeHtml(title)}-${index}">复核组合</button>
            <div class="matchdayReviewResult">输入赛日前最新组合赔率后，判断继续观察、降级或跳过。</div>
          </div>
        </div>` : ""}
        ${!isCombo && row.decision_action_zh ? `<p class="coachActionLine">${C.escapeHtml(row.decision_action_zh)}</p>` : ""}
        ${!isCombo && row.decision_reason_zh ? `<p class="mutedLine">${C.escapeHtml(row.decision_reason_zh)}</p>` : ""}
        ${!isCombo && row.parlay_policy_zh ? `<p class="mutedLine">串联纪律：${C.escapeHtml(row.parlay_policy_zh)}</p>` : ""}
        ${!isCombo && row.recommended_use_zh ? `<p class="mutedLine">${C.escapeHtml(row.recommended_use_zh)}</p>` : ""}
        ${!isCombo && row.odds_reading_zh ? `<p class="edgeCoachLine">${C.escapeHtml(row.odds_reading_zh)}</p>` : ""}
        ${!isCombo && row.calibration_message_zh ? `<p class="mutedLine">${C.escapeHtml(row.calibration_message_zh)}</p>` : ""}
        ${!isCombo && row.probability_bin_message_zh ? `<p class="mutedLine">${C.escapeHtml(row.probability_bin_message_zh)}</p>` : ""}
        ${!isCombo && row.ml_learning_note_zh ? `<p class="mutedLine">${C.escapeHtml(row.ml_learning_note_zh)}</p>` : ""}
        ${!isCombo && row.next_review_zh ? `<p class="mutedLine">${C.escapeHtml(row.next_review_zh)}</p>` : ""}
        ${!isCombo && row.matchday_review_zh ? `<div class="oddsReviewMini">
          <strong>赛日赔率复核</strong>
          <p>${C.escapeHtml(row.matchday_review_zh)}</p>
          <span>保留观察最低赔率：${C.escapeHtml(row.matchday_keep_min_odds || "N/A")}</span>
          <span>失去覆盖低于：${C.escapeHtml(row.matchday_no_value_below_odds || "N/A")}</span>
          <span>反向漂移警戒：${C.escapeHtml(row.matchday_reverse_drift_watch_odds || "N/A")}</span>
          <div class="matchdayReviewTool">
            <input inputmode="decimal" placeholder="填临场赔率，如 2.10" aria-label="临场赔率">
            <button type="button" class="matchdayReviewBtn"
              data-keep-min="${C.escapeHtml(row.matchday_keep_min_odds || "")}"
              data-no-value-below="${C.escapeHtml(row.matchday_no_value_below_odds || "")}"
              data-reverse-watch="${C.escapeHtml(row.matchday_reverse_drift_watch_odds || "")}"
              data-target="${C.escapeHtml(title)}-${index}">复核动作</button>
            <div class="matchdayReviewResult">输入赛日前最新赔率后，判断继续观察、降级或跳过。</div>
          </div>
        </div>` : ""}
        ${!isCombo && row.user_priority_zh ? `<p class="mutedLine">${C.escapeHtml(row.user_priority_zh)}</p>` : ""}
        ${!isCombo && longshotText(row) ? `<p class="warningLine">${C.escapeHtml(longshotText(row))}</p>` : ""}
        ${!isCombo && row.reliability_explanation_zh ? `<p class="mutedLine">${C.escapeHtml(row.reliability_explanation_zh)}</p>` : ""}
        ${!isCombo && row.opposing_factors ? `<p class="mutedLine">${C.escapeHtml(row.opposing_factors)}</p>` : ""}
      </article>`;
  }).join("")}</div>`;
}

function todayCompactCards(rows, kind = "single", message = "暂无观察信号", sharedMissing = []) {
  if (!rows || !rows.length) return `<div class="emptyState">${C.escapeHtml(message)}</div>`;
  return `<div class="todayCompactGrid">${rows.slice(0, 3).map((row) => {
    const isCombo = kind === "combo";
    const isScore = kind === "score";
    const isTotalGoals = kind === "total_goals";
    const title = isCombo ? (row.legs || row.match || "组合观察") : (row.match || "观察信号");
    const tag = isCombo
      ? (isComboRejected(row) ? "候选待复核" : "纸面组合")
      : isTotalGoals
        ? `总进球 · ${row.direction || "节奏"}`
        : isScore
          ? `比分 · ${row.direction || "倾向"}`
          : `${row.play_type || "玩法"} · ${row.direction || "方向"}`;
    const odds = displayValue(isCombo ? row.odds : (row.official_odds || row.odds), "未接入赔率");
    const probability = displayValue(row.calibrated_prob || row.model_prob || row.observation_confidence, "暂不能计算");
    const probabilityLabel = isCombo ? "组合概率" : (isScore || isTotalGoals) ? "模型概率" : "校准概率";
    const margin = displayValue(row.safety_margin || row.edge || row.ev, "暂不能计算");
    const marginLabel = isScore ? "可信状态" : isTotalGoals ? "节奏优势" : "安全余量";
    const verdict = isCombo
      ? (row.combo_decision_label_zh || comboStatusLabel(row) || "候选待复核")
      : isScore
        ? (row.confidence_label_zh || row.signal_category_zh || "高波动参考")
        : isTotalGoals
          ? (row.confidence_label_zh || row.signal_category_zh || "节奏参考")
          : (row.decision_label_zh || row.signal_category_zh || row.confidence_label_zh || "待复核");
    const miniMetrics = isScore
      ? [
          ["模型概率", probability],
          ["可信状态", margin],
          ["用途", "比分倾向"],
        ]
      : isTotalGoals
        ? [
            ["模型概率", probability],
            ["节奏优势", margin],
            ["用途", "进球节奏"],
          ]
        : isCombo
          ? [
              ["组合赔率", odds],
              [probabilityLabel, probability],
              ["纪律状态", verdict],
            ]
          : [
              ["赔率", odds],
              [probabilityLabel, probability],
              [marginLabel, margin],
            ];
    const why = isCombo
      ? (row.play_diversity_reason_zh || row.discipline_summary_zh || row.combo_action_zh || row.reject_reason || "组合需要同时命中，优先看风险纪律。")
      : (row.odds_coach_verdict_zh || row.decision_reason_zh || row.recommended_action_zh || "看赔率是否覆盖校准概率。");
    const next = isCombo
      ? (row.combo_parlay_policy_zh || row.combo_action_zh || "不通过时不要强行组合。")
      : (row.next_review_zh || row.parlay_policy_zh || row.recommended_use_zh || "赛日前复核赔率、首发、伤停和天气。");
    const tags = reasonTags(`${why} ${next} ${row.reject_reason || ""}`);
    const rowMissing = Array.isArray(row.missing_signals_zh)
      ? row.missing_signals_zh
      : Array.isArray(row.missing_signals)
        ? row.missing_signals
        : [];
    const gapList = rowMissing.length ? rowMissing : (Array.isArray(sharedMissing) ? sharedMissing : []);
    const gapText = gapList.length ? `关键缺口：${gapList.slice(0, 4).join("、")}` : "";
    const comboChecklist = isCombo ? comboUpgradeChecklist(row) : "";
    const marketAudit = marketAuditMiniPanel(row);
    const primaryReason = shortText(why, isCombo ? 58 : 66);
    const nextAction = shortText(next || "赛日前复核赔率、首发、伤停和天气。", 52);
    return `
      <article class="todayCompactCard kind-${C.escapeHtml(kind)} ${isCombo && isComboRejected(row) ? "isRejected" : ""}">
        <div class="todayCardTop">
          <span>${C.escapeHtml(tag)}</span>
          <b>${C.escapeHtml(verdict)}</b>
        </div>
        <strong>${C.escapeHtml(title)}</strong>
        <div class="todayMiniMetrics">
          ${miniMetrics.map(([label, value]) => `<div><span>${C.escapeHtml(label)}</span><b>${C.escapeHtml(value)}</b></div>`).join("")}
        </div>
        ${tags.length ? `<div class="reasonTags miniTags">${tags.slice(0, 3).map((tag) => `<em>${C.escapeHtml(tag)}</em>`).join("")}</div>` : ""}
        ${marketAudit}
        ${comboChecklist}
        <p class="compactReason">${C.escapeHtml(primaryReason)}</p>
        ${isCombo && row.play_type_mix_zh ? `<p class="mutedLine">${C.escapeHtml(`玩法结构：${row.play_type_mix_zh}`)}</p>` : ""}
        ${gapText ? `<p class="mutedLine">${C.escapeHtml(gapText)}</p>` : ""}
        <em class="compactNext">${C.escapeHtml(nextAction)}</em>
      </article>
    `;
  }).join("")}</div>`;
}

function marketAuditMiniPanel(row = {}) {
  const summary = row.market_audit_zh || row.market_probability_audit?.message_zh || "";
  const bias = row.market_bias_zh || row.market_bias_audit?.outcome_message_zh || row.market_bias_audit?.message_zh || "";
  const shift = row.market_method_shift_zh || (row.market_bias_audit?.outcome_method_shift != null ? fmtPct(row.market_bias_audit.outcome_method_shift) : "");
  const warning = row.market_audit_warning_zh || "";
  if (!summary && !bias && !shift && !warning) return "";
  const riskText = [summary, bias, shift ? `方法分歧 ${shift}` : ""].filter(Boolean).join(" · ");
  const status = /冷门|分歧|不稳定|异常|较厚/.test(`${summary} ${bias} ${warning}`) ? "watch" : "ok";
  return `
    <div class="marketAuditMini" data-status="${C.escapeHtml(status)}">
      <b>赔率审计</b>
      <span>${C.escapeHtml(riskText || "市场概率基准已检查")}</span>
      ${warning ? `<em>${C.escapeHtml(shortText(warning, 72))}</em>` : ""}
    </div>
  `;
}

function displayValue(value, fallback = "暂不能计算") {
  if (value === undefined || value === null || value === "") return fallback;
  const text = String(value);
  return text === "N/A" || text === "NaN" || text === "undefined" ? fallback : text;
}

function comboUpgradeChecklist(row = {}) {
  const quality = row.best_parlay_quality || {};
  const hasQuality = Object.keys(quality).length > 0;
  const reason = row.reject_reason || row.discipline_summary_zh || row.opposing_factors_zh || "";
  const checks = [
    { key: "ev_pass", label: "赔率价值", fallbackPass: !/EV 不足|Edge 不足|优势偏薄|安全边际/.test(reason), fix: "等待赔率或模型边际更清楚。" },
    { key: "confidence_pass", label: "可信度", fallbackPass: !/可信度|信心/.test(reason), fix: "补齐伤停、首发、天气和新闻后再评估。" },
    { key: "correlation_pass", label: "相关性", fallbackPass: !/相关性/.test(reason), fix: "避开同赛事、同方向或高度相关的腿。" },
    { key: "play_diversity_pass", label: "玩法分散", fallbackPass: !/玩法过于集中|同类腿/.test(reason), fix: "混合胜平负、让球和其他玩法，避免同类信号扎堆。" },
    { key: "risk_pass", label: "风险", fallbackPass: !/风险|very_high|高风险/.test(reason), fix: "降低腿数，优先保留单关或低风险 2串1。" },
    { key: "information_pass", label: "情报覆盖", fallbackPass: !/情报|伤停|首发|天气|新闻/.test(reason), fix: "先补情报覆盖，不把未知当优势。" },
    { key: "hit_rate_pass", label: "命中门槛", fallbackPass: !/命中概率|纪律门槛/.test(reason), fix: "组合概率需要覆盖组合赔率和纪律门槛。" },
  ].map((item) => {
    const pass = hasQuality && quality[item.key] !== undefined ? Boolean(quality[item.key]) : item.fallbackPass;
    return { ...item, pass };
  });
  const blockers = checks.filter((item) => !item.pass);
  const firstBlocker = blockers[0];
  const status = quality.final_status || (row.daily_candidate ? "daily_candidate" : isComboSelected(row) ? "selected" : blockers.length ? "rejected" : "watch");
  const statusZh = status === "selected"
    ? "可观察"
    : status === "daily_candidate"
      ? "纸面候选"
      : status === "no_combo"
        ? "暂无组合"
        : status === "rejected"
          ? "未过门控"
          : "待复核";
  const fixText = firstBlocker ? firstBlocker.fix : "赛日前逐腿复核赔率、首发、伤停和天气。";
  return `
    <div class="comboUpgradePanel" data-status="${C.escapeHtml(status)}">
      <div class="comboUpgradeHead">
        <span>${C.escapeHtml(statusZh)}</span>
        <b>${C.escapeHtml(firstBlocker ? `卡在：${firstBlocker.label}` : "暂未发现硬阻断")}</b>
      </div>
      <div class="comboCheckGrid">
        ${checks.slice(0, 6).map((item) => `
          <i class="${item.pass ? "pass" : "fail"}">${C.escapeHtml(item.label)}</i>
        `).join("")}
      </div>
      <em>${C.escapeHtml(fixText)}</em>
    </div>
  `;
}


function preflightPromptCard(title, body, action = "生成今日观察", target = "optimizer") {
  const attr = target === "scoregoals"
    ? "data-run-scoregoals=\"1\""
    : target === "optimizer"
      ? "data-run-optimizer=\"single\""
      : `data-jump-view="${C.escapeHtml(target)}"`;
  return `
    <div class="preflightPromptCard">
      <span>预筛完成</span>
      <strong>${C.escapeHtml(title)}</strong>
      <p>${C.escapeHtml(body)}</p>
      <button type="button" class="primary" ${attr}>${C.escapeHtml(action)}</button>
    </div>
  `;
}

function renderTodayTopSections(view) {
  if (!view) return;
  const sharedMissing = Array.isArray(view.missing_signals)
    ? view.missing_signals
    : Array.isArray(view.critical_gap_list_zh)
      ? view.critical_gap_list_zh.map((line) => String(line || "").split("：")[0]).filter(Boolean)
      : [];
  if (view.lightweight_homepage) {
    const matchCount = view.matches_count ?? 0;
    const source = providerName(view.provider_used || view.data_source_status?.provider_used || "auto");
    const preflightText = `已确认 ${matchCount} 场可售比赛，使用${source}。完整候选需要生成今日观察。`;
    if (qs("#todaySingles")) qs("#todaySingles").innerHTML = preflightPromptCard("等待完整模型排序", `${preflightText} 单关要看赔率去水、模型概率、校准概率和冷门惩罚。`, "生成今日观察", "optimizer");
    if (qs("#todayParlay2")) qs("#todayParlay2").innerHTML = preflightPromptCard("先不判断 2串1", `${preflightText} 组合必须等单腿质量、相关性折扣和可信度门控一起返回。`, "查看组合审核", "bestparlay");
    if (qs("#todayParlay3")) qs("#todayParlay3").innerHTML = preflightPromptCard("3串1默认高风险", "完整模型未运行前，不展示高风险组合候选，避免用户把空结果误读成机会。", "查看拒绝原因", "bestparlay");
    if (qs("#todayTotalGoals")) qs("#todayTotalGoals").innerHTML = preflightPromptCard("进球数待比分矩阵", "总进球需要 Poisson/xG 与赔率输入，快速预筛阶段只确认比赛，不给节奏结论。", "分析进球数", "scoregoals");
    if (qs("#todayScores")) qs("#todayScores").innerHTML = preflightPromptCard("比分只作倾向参考", "比分波动最高，必须等比分矩阵生成后再展示 Top 5，不用空表吓用户。", "查看比分倾向", "scoregoals");
    return;
  }
  if (qs("#todaySingles")) {
    qs("#todaySingles").innerHTML = todayCompactCards(view.top_singles || [], "single", "当前没有通过纪律筛选的单关观察。若无 Edge，显示无观察价值。", sharedMissing);
  }
  const parlay2Selected = view.top_2x1 || [];
  const parlay2Display = parlay2Selected.length ? parlay2Selected : (view.top_2x1_display || []);
  const parlay2Intro = parlayDecisionPanel({
    title: parlay2Selected.length ? "最推荐 2串1 通过纪律" : "最推荐 2串1 纸面候选",
    status: parlay2Selected.length ? "可观察" : "纸面候选",
    reason: view.top_2x1_empty_explanation || view.no_combo_reason || view.credibility_gate?.reason_zh || "2串1 需要多场同时命中，风险纪律会更严格。",
    action: parlay2Selected.length ? "逐腿复核赔率、伤停、首发和天气。" : "每天仍输出最推荐候选，用于赛后学习和比较，不等于已通过门控。",
  });
  if (qs("#todayParlay2")) {
    qs("#todayParlay2").innerHTML = parlay2Intro + todayCompactCards(parlay2Display, "combo", "当前没有可排序的 2串1 纸面候选。", sharedMissing);
  }
  if (qs("#todayParlay3")) {
    const parlay3Display = view.top_3x1_display || [];
    const parlay3Intro = parlayDecisionPanel({
      title: "最推荐 3串1 纸面候选",
      status: "高风险候选",
      reason: view.top_3x1_empty_explanation || "3串1 每天只作最高风险纸面候选，默认不升级为强观察。",
      action: "每天输出用于复盘组合放大效应；优先看联合概率、相关性和单腿弱点。",
    });
    qs("#todayParlay3").innerHTML = parlay3Intro + todayCompactCards(parlay3Display, "combo", "当前暂无通过门控的 3串1 候选；高风险项默认不升级。", sharedMissing);
  }
  if (qs("#todayTotalGoals")) {
    qs("#todayTotalGoals").innerHTML = todayCompactCards(view.top_total_goals || [], "total_goals", "当前没有总进球观察。 ", sharedMissing);
  }
  if (qs("#todayScores")) {
    qs("#todayScores").innerHTML = todayCompactCards(view.top_scores || [], "score", "当前没有比分观察。 ", sharedMissing);
  }
  if (qs("#todayRejectedParlay2")) {
    qs("#todayRejectedParlay2").innerHTML = rejectedComboCards(view.top_rejected_2x1 || [], "当前暂无 2串1 被拒复盘项。");
  }
  if (qs("#todayRejectedParlay3")) {
    qs("#todayRejectedParlay3").innerHTML = rejectedComboCards(view.top_rejected_3x1 || [], "当前暂无 3串1 被拒复盘项。");
  }
}

function parlayDecisionPanel({ title, status, reason, action }) {
  return `
    <div class="parlayDecisionPanel">
      <span>${C.escapeHtml(status || "组合纪律")}</span>
      <strong>${C.escapeHtml(title || "组合纪律")}</strong>
      <p>${C.escapeHtml(reason || "组合需要同时命中，先看可信度和风险。")}</p>
      <em>${C.escapeHtml(action || "先保留纸面候选，赛日前再复核。")}</em>
    </div>
  `;
}

function rejectedComboCards(rows, message = "当前没有被拒组合。") {
  if (!rows || !rows.length) return `<div class="emptyState">${C.escapeHtml(message)}</div>`;
  return `<div class="rejectedComboGrid">${rows.slice(0, 6).map((row) => {
    const title = row.legs || row.match || "组合候选";
    const reason = row.reject_reason || row.reason || row.discipline_summary_zh || "未通过组合纪律。";
    const tags = reasonTags(reason);
    const quality = comboRejectQuality(row, reason);
    return `
      <article class="rejectedComboCard">
        <div class="rejectedComboHead">
          <span>${C.escapeHtml(row.type || "组合")}</span>
        <b>${C.escapeHtml(row.combo_decision_label_zh || comboStatusLabel(row) || "候选待复核")}</b>
        </div>
        <strong>${C.escapeHtml(title)}</strong>
        <div class="rejectedComboMetrics">
          <div><span>组合赔率</span><b>${C.escapeHtml(row.odds || "N/A")}</b></div>
          <div><span>组合概率</span><b>${C.escapeHtml(row.model_prob || "N/A")}</b></div>
          <div><span>盈亏线</span><b>${C.escapeHtml(row.break_even_prob || "N/A")}</b></div>
          <div><span>安全边际</span><b>${C.escapeHtml(row.safety_margin || row.edge || "N/A")}</b></div>
        </div>
        <div class="rejectQuality">
          ${quality.map((item) => `
            <div class="${item.pass ? "pass" : "fail"}">
              <span>${C.escapeHtml(item.label)}</span>
              <b>${C.escapeHtml(item.pass ? "通过" : "未过")}</b>
            </div>
          `).join("")}
        </div>
        ${tags.length ? `<div class="reasonTags miniTags">${tags.map((tag) => `<em>${C.escapeHtml(tag)}</em>`).join("")}</div>` : ""}
        <p>${C.escapeHtml(shortText(reason, 150))}</p>
        ${row.play_diversity_reason_zh ? `<p class="mutedLine">${C.escapeHtml(row.play_diversity_reason_zh)}</p>` : ""}
        <em>${C.escapeHtml(row.discipline_summary_zh || "组合不是赔率越高越好，必须同时通过命中概率、相关性、可信度和赛前情报纪律。")}</em>
      </article>
    `;
  }).join("")}</div>`;
}

function comboRejectQuality(row, reason) {
  const text = String(reason || "");
  const risk = String(row.risk_level || "").toLowerCase();
  return [
    { label: "EV/Edge", pass: !/EV 不足|Edge 不足|优势偏薄/.test(text) },
    { label: "可信度", pass: !/可信度|信心|情报/.test(text) },
    { label: "相关性", pass: !/相关性/.test(text) },
    { label: "玩法分散", pass: !/玩法过于集中|同类腿/.test(text) },
    { label: "风险", pass: !/风险|very_high|高风险/.test(text) && !["high", "very_high"].includes(risk) },
  ];
}

function aiHintForTodayCard(row, isCombo, kind = "single") {
  const memory = state.latestAiResearch || {};
  const source = memory.provider === "deepseek" || memory.ds_completed ? "DS Pro提示" : "研究提示";
  const contextual = aiContextHintForKind(kind, memory, row);
  const odds = parseNumberLike(isCombo ? row.odds : (row.official_odds || row.odds));
  const status = String(row.status || "");
  const play = String(row.play_type || row.direction || "");
  if (isCombo && status.includes("未过门控")) {
    return {
      label: source,
      text: contextual || "这类组合先看被拒原因：可信度门控、单腿纪律、相关性和组合命中率，任何一项不过都不升级为强观察。",
    };
  }
  if (isCombo) {
    return {
      label: source,
      text: contextual || "组合只在每一腿都有价值、相关性可控、组合概率覆盖赔率时才保留；赛日前还要复核赔率漂移。",
    };
  }
  if (Number.isFinite(odds) && odds >= 6) {
    return {
      label: source,
      text: contextual || "这是高赔率冷门观察，波动很大；可单独跟踪，不适合作为串联核心，除非赛前情报和收盘赔率继续支持。",
    };
  }
  if (kind === "score" || /比分/.test(play)) {
    return {
      label: source,
      text: contextual || "比分属于高波动倾向，只用于理解节奏和比分矩阵，不当作强信号。",
    };
  }
  if (kind === "total_goals" || /总进球/.test(play)) {
    return {
      label: source,
      text: contextual || "总进球更适合判断比赛节奏；若官方赔率缺失，只看模型概率，不计算 EV。",
    };
  }
  return {
    label: source,
    text: contextual || (memory.body ? shortText(memory.body, 96) : "先看赔率是否覆盖校准概率，再看情报完整度和赛日赔率复核。"),
  };
}

function aiContextHintForKind(kind, memory, row = {}) {
  const structured = memory.structured_notes || {};
  const matchedNote = structuredMatchNote(row, structured);
  if (matchedNote) return matchedNote;
  const structuredNote = structuredNoteForKind(kind, structured);
  if (structuredNote) return structuredNote;
  const cards = Array.isArray(memory.cards) ? memory.cards : [];
  const byKicker = (needles) => {
    const found = cards.find((card) => needles.some((needle) => String(card.kicker || card.title || "").includes(needle)));
    return found ? shortText(found.body || found.title || "", 110) : "";
  };
  if (kind === "combo") return byKicker(["组合", "纪律"]);
  if (kind === "total_goals") return findAiLine(memory.full_text, ["总进球", "进球节奏", "节奏"], byKicker(["今日", "结论"]));
  if (kind === "score") return findAiLine(memory.full_text, ["比分", "比分倾向"], "比分属于高波动倾向，只作节奏参考。");
  return byKicker(["最强", "单关", "观察"]) || findAiLine(memory.full_text, ["优先单关", "最强观察", "Top 单关"], "");
}

function structuredMatchNote(row, structured) {
  const rows = Array.isArray(structured.match_notes) ? structured.match_notes : [];
  if (!rows.length) return "";
  const candidates = [
    row.match,
    row.legs,
    row.label_zh,
    row.home_team && row.away_team ? `${row.home_team} vs ${row.away_team}` : "",
  ].filter(Boolean);
  const keys = candidates.map(noteKey);
  const found = rows.find((note) => {
    const target = String(note.target || "");
    const noteKeyValue = String(note.key || noteKey(target));
    return keys.some((key) => key && (noteKeyValue.includes(key) || key.includes(noteKeyValue))) || candidates.some((value) => value && target.includes(String(value)));
  });
  if (!found) return "";
  const prefix = found.role_zh ? `${found.role_zh}：` : "";
  return shortText(`${prefix}${found.note_zh || found.usage_zh || ""}`, 116);
}

function noteKey(text) {
  return String(text || "").toLowerCase().split("").filter((ch) => /[a-z0-9]/.test(ch) || /[\u4e00-\u9fff]/.test(ch)).join("").slice(0, 80);
}

function structuredNoteForKind(kind, structured) {
  const pick = (key) => {
    const rows = Array.isArray(structured[key]) ? structured[key] : [];
    const first = rows[0] || {};
    return first.note_zh ? shortText(first.note_zh, 116) : "";
  };
  if (kind === "combo") return pick("combo_notes");
  if (kind === "total_goals") return pick("total_goals_notes");
  if (kind === "score") return pick("score_notes");
  return pick("single_notes");
}

function findAiLine(text, patterns, fallback = "") {
  const lines = String(text || "").split(/\n+/).map((line) => line.replace(/[*#`>-]/g, "").trim()).filter(Boolean);
  for (const pattern of patterns) {
    const found = lines.find((line) => line.includes(pattern));
    if (found) return shortText(found.replace(/^[:：\s]+/, ""), 110);
  }
  return fallback;
}

function shortText(text, max = 80) {
  const value = String(text || "").replace(/\s+/g, " ").trim();
  return value.length > max ? `${value.slice(0, max)}…` : value;
}

function comboMatchdayReview(row) {
  const odds = parseNumberLike(row.odds);
  const prob = parseProbabilityLike(row.model_prob);
  if (!Number.isFinite(odds) || odds <= 1 || !Number.isFinite(prob) || prob <= 0) return null;
  const noValueBelow = 1 / prob;
  const desiredMargin = prob < 0.20 ? 0.05 : 0.035;
  const keepMin = prob > desiredMargin ? 1 / (prob - desiredMargin) : noValueBelow;
  const reverseWatch = odds * (prob < 0.20 ? 1.15 : 1.10);
  return {
    keepMin: keepMin.toFixed(4),
    noValueBelow: noValueBelow.toFixed(4),
    reverseWatch: reverseWatch.toFixed(4),
    keepMinText: keepMin.toFixed(2),
    noValueBelowText: noValueBelow.toFixed(2),
    reverseWatchText: reverseWatch.toFixed(2),
    message_zh: `组合需要同时命中。当前组合概率约 ${fmtPct(prob)}，组合赔率至少要高于 ${noValueBelow.toFixed(2)} 才覆盖盈亏线；低于 ${keepMin.toFixed(2)} 时安全边际偏薄。`,
  };
}

function parseNumberLike(value) {
  if (typeof value === "number") return value;
  const text = String(value || "").replace(/[,，¥￥]/g, "").trim();
  const match = text.match(/-?\d+(\.\d+)?/);
  return match ? Number.parseFloat(match[0]) : NaN;
}

function parseProbabilityLike(value) {
  if (typeof value === "number") return value > 1 ? value / 100 : value;
  const text = String(value || "").trim();
  const parsed = parseNumberLike(text);
  if (!Number.isFinite(parsed)) return NaN;
  return text.includes("%") || parsed > 1 ? parsed / 100 : parsed;
}

function evaluateMatchdayOdds(button) {
  const wrap = button.closest(".matchdayReviewTool");
  if (!wrap) return;
  const input = wrap.querySelector("input");
  const output = wrap.querySelector(".matchdayReviewResult");
  const current = Number.parseFloat((input && input.value || "").trim());
  const keepMin = Number.parseFloat(button.dataset.keepMin || "");
  const noValueBelow = Number.parseFloat(button.dataset.noValueBelow || "");
  const reverseWatch = Number.parseFloat(button.dataset.reverseWatch || "");
  if (!output) return;
  if (!Number.isFinite(current) || current <= 1) {
    output.textContent = "请输入大于 1.00 的临场赔率。";
    output.dataset.status = "wait";
    return;
  }
  if (Number.isFinite(noValueBelow) && current < noValueBelow) {
    output.textContent = `复核结果：跳过。当前赔率 ${current.toFixed(2)} 已低于失去覆盖线 ${noValueBelow.toFixed(2)}，校准概率不再覆盖赔率。`;
    output.dataset.status = "stop";
    return;
  }
  if (Number.isFinite(keepMin) && current < keepMin) {
    output.textContent = `复核结果：降级为弱观察。当前赔率 ${current.toFixed(2)} 低于保留观察线 ${keepMin.toFixed(2)}，安全边际变薄。`;
    output.dataset.status = "downgrade";
    return;
  }
  if (Number.isFinite(reverseWatch) && current >= reverseWatch) {
    output.textContent = `复核结果：警惕反向漂移。当前赔率 ${current.toFixed(2)} 已高于 ${reverseWatch.toFixed(2)}，如果没有新增情报支持，应降级观察。`;
    output.dataset.status = "watch";
    return;
  }
  output.textContent = `复核结果：可继续观察。当前赔率 ${current.toFixed(2)} 尚未触发降级线，但仍要复核伤停、首发、天气和新闻面。`;
  output.dataset.status = "keep";
}

function intelligenceLabel(value) {
  const map = {
    news: "新闻面",
    injuries: "伤停",
    injury: "伤停",
    lineup: "首发",
    lineups: "首发",
    weather: "天气",
    motivation: "战意",
    travel: "旅行疲劳",
    neutral_ground: "中立场",
    tournament_importance: "赛事重要性",
    match_city: "比赛城市",
  };
  return map[String(value || "").trim()] || String(value || "").trim();
}
function formatMissingSignals(value) {
  if (!value) return "";
  const items = Array.isArray(value) ? value : String(value).split(/[,，、]/);
  const labels = items.map(intelligenceLabel).filter(Boolean);
  return labels.length ? `缺失情报：${Array.from(new Set(labels)).slice(0, 6).join("、")}` : "";
}

function scoreGoalCards(rows, kind = "total", message = "暂无模型观察") {
  if (!rows || !rows.length) return `<div class="emptyState">${C.escapeHtml(message)}</div>`;
  return `<div class="scoreGoalGrid">${rows.slice(0, 6).map((row) => {
    const title = row.match || "比赛";
    const tag = row.direction || row.play_type || "观察";
    const probability = row.model_prob || row.observation_confidence || "N/A";
    const status = row.ev_status_zh || row.odds_status_zh || "仅模型概率";
    const action = row.recommended_action_zh || (kind === "score" ? "只作比分倾向参考" : "观察比赛节奏");
    const reliability = row.reliability_label_zh || row.confidence_label_zh || "谨慎";
    const explanation = row.reliability_explanation_zh || row.why_zh || row.selection_reason || "该项由 Poisson/xG + Dixon-Coles 概率矩阵推导。";
    const missing = formatMissingSignals(row.missing_signals || row.missing_signals_zh);
    return `
      <article class="scoreGoalCard">
        <div class="signalHead">
          <strong>${C.escapeHtml(title)}</strong>
          <span>${C.escapeHtml(tag)}</span>
        </div>
        <div class="scoreHeroMetric">
          <div><span>模型概率</span><b>${C.escapeHtml(probability)}</b></div>
          <div><span>赔率 / EV</span><b>${C.escapeHtml(status)}</b></div>
          <div><span>可信度</span><b>${C.escapeHtml(reliability)}</b></div>
        </div>
        <p class="reasonLine">${C.escapeHtml(action)}</p>
        <p class="mutedLine">${C.escapeHtml(explanation)}</p>
        ${missing ? `<p class="mutedLine">${C.escapeHtml(missing)}</p>` : ""}
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
  { key: "break_even_prob", label: "盈亏线" },
  { key: "model_prob", label: "组合概率" },
  { key: "safety_margin", label: "安全边际" },
  { key: "combo_decision_label_zh", label: "组合判断" },
  { key: "market_prob", label: "市场概率" },
  { key: "ev", label: "EV" },
  { key: "edge", label: "Edge" },
  { key: "risk_level", label: "风险" },
  { key: "status", label: "状态" },
  { key: "reject_reason", label: "被拒原因" },
  { key: "discipline_summary_zh", label: "纪律拆解" },
];

function mergeTodayWithOptimizer(view = {}) {
  const out = { ...(view || {}) };
  const opt = state.optimizerView || {};
  const optBest = opt.best_parlay_summary || {};
  const optLanes = opt.daily_output_lanes || optBest.daily_output_lanes || [];
  const hasOptLanes = Array.isArray(optLanes) && optLanes.some((lane) => lane && lane.status !== "empty" && !String(lane.target_zh || "").includes("暂无可排序"));
  if (hasOptLanes) {
    out.best_parlay_summary = { ...(out.best_parlay_summary || {}), ...optBest, daily_output_lanes: optLanes };
    out.daily_output_lanes = optLanes;
    out.optimizer = { ...(out.optimizer || {}), ...opt };
  }
  return out;
}


async function runOneClickObservation() {
  if (state.oneClickObservationRunning) {
    setTodayQuickActionStatus("当前：已经在生成今日观察，请稍等。");
    return;
  }
  const originView = state.currentView || "today";
  state.oneClickObservationRunning = true;
  setStatus("Run", "正在生成今日观察：比赛、优化、组合、比分会一起刷新。");
  setTodayQuickActionStatus("当前：一键生成中，正在读取比赛与候选。");
  startTodayProgressTicker();
  try {
    await loadToday({ forceRefresh: true, useFastPreview: false });
    await runOptimizerWithProgress(false, { stayOnCurrentView: true });
    await loadBestParlay({ stayOnCurrentView: true });
    await loadScoreGoals({ stayOnCurrentView: true });
    if (state.todayView) renderToday(state.todayView);
    switchView(originView);
    setStatus("Ready", "今日观察已生成：单关、2串1、3串1、比分/进球数已同步。");
    setTodayQuickActionStatus("当前：今日观察已生成，候选已同步到各板块。");
  } catch (error) {
    setStatus("Check", `一键生成未完整完成：${error && error.message ? error.message : "未知错误"}`);
    if (state.todayView) renderToday(state.todayView);
    switchView(originView);
  } finally {
    state.oneClickObservationRunning = false;
    stopTodayProgressTicker();
  }
}

async function loadToday(options = {}) {
  const forceRefresh = Boolean(options.forceRefresh);
  const useFastPreview = options.useFastPreview !== false;
  const requestToken = `${Date.now()}_${Math.random().toString(16).slice(2)}`;
  state.todayLoadToken = requestToken;
  const preserveCurrent = forceRefresh && state.todayView;
  if (preserveCurrent) {
    setAiAutoStatus("running", "正在后台刷新", "先保留当前可读结果，不清空页面；新数据回来后再替换。");
    setTodayQuickActionStatus("当前：后台刷新中，页面不会清空。");
  } else {
    renderTodayLoadingState();
  }
  let lightweightRendered = false;
  if (useFastPreview) {
    const fastPayload = await request("/api/view/next-available", {
      provider: providerParam(),
      date: currentDateParam(),
      bankroll: bankrollParam(),
      risk_profile: riskProfileParam(),
      external_signals: externalSignalsParam(),
      fast: "1",
    }, "快速扫描下一可售日比赛", 7000);
    if (state.todayLoadToken !== requestToken) return;
    if (fastPayload.ok) {
      try {
        renderToday(fastPayload.data);
        renderResearchArchiveStatus(fastPayload.data?.research_archive_status || state.latestResearchArchive || {});
        lightweightRendered = Boolean(fastPayload.data?.lightweight_homepage);
        setAiAutoStatus("fallback", "首页快速扫描完成", "已先确认最近可售比赛和数据源，正在补齐完整概率、组合纪律和研究摘要。");
      } catch (_error) {
        lightweightRendered = false;
      }
    }
  }
  let settled = false;
  const watchdog = window.setTimeout(() => {
    if (settled || state.todayLoadToken !== requestToken) return;
    if (lightweightRendered) {
      setAiAutoStatus("fallback", "完整读取后台继续", "已保留快速结果，完整赔率、组合纪律和情报融合本次较慢；你可以先看结果，再稍后刷新。");
      setTodayQuickActionStatus("当前：已显示快速结果，完整读取后台继续");
      return;
    }
    if (state.todayView) {
      setAiAutoStatus("fallback", "刷新仍在后台等待", "已保留最近一次可读结果；可以直接进入赛前优化生成候选。");
      setTodayQuickActionStatus("当前：保留最近一次结果，刷新仍在等待。");
      return;
    }
    renderTodayTimeoutState({ error: { code: "homepage_watchdog", message: "首页读取超过等待时间，已先显示可操作状态。" } });
  }, forceRefresh ? 18000 : 12000);
  const payload = await request("/api/view/next-available", {
    provider: providerParam(),
    date: currentDateParam(),
    bankroll: bankrollParam(),
    risk_profile: riskProfileParam(),
    external_signals: externalSignalsParam(),
    refresh: forceRefresh ? "1" : "0",
  }, forceRefresh ? "生成今日观察" : "读取今日观察", forceRefresh ? 24000 : 18000);
  if (state.todayLoadToken !== requestToken) return;
  settled = true;
  window.clearTimeout(watchdog);
  stopTodayProgressTicker();
  if (payload.ok) {
    try {
      renderToday(payload.data);
      renderResearchArchiveStatus(payload.data?.research_archive_status || state.latestResearchArchive || {});
      if (payload.data?.lightweight_homepage) {
        setAiAutoStatus("fallback", "首页轻量扫描完成", "已确认下一可售日比赛和数据源；完整模型、组合纪律和 DS 研究请进入赛前优化或组合审核后再运行。");
      } else {
        setAiAutoStatus("running", "比赛读取完成，准备自动研究", "Top 观察已更新；下一步会自动调用 DeepSeek Pro 生成研究摘要。");
        maybeAutoRunAiResearch(payload.data);
      }
    } catch (error) {
      renderTodayTimeoutState({ error: { code: "render_error", message: `页面渲染遇到问题：${error && error.message ? error.message : "未知错误"}` } });
    }
  } else {
    if (lightweightRendered) {
      setAiAutoStatus("fallback", "已保留快速结果", "完整读取本次较慢或失败，页面先保留快速结果；你可以继续进入赛前优化，或稍后再刷新。");
      setStatus("Check", payload.error?.message || "快速结果已保留，完整读取稍慢。");
      switchView("today");
      return;
    }
    if (state.todayView) {
      setAiAutoStatus("fallback", "刷新未完成，保留旧结果", "本次完整读取后台继续或失败，页面保留最近一次可用观察。");
      setTodayQuickActionStatus("当前：本次刷新未完成，已保留最近一次可用观察。");
      switchView("today");
      return;
    }
    renderTodayTimeoutState(payload);
  }
  switchView("today");
}

function aiProviderParam() {
  const mode = value("#explainMode", "auto");
  return mode === "auto" ? "auto" : mode;
}

function aiRunParam() {
  const mode = value("#explainMode", "auto");
  return mode === "local" ? "" : "1";
}

function maybeAutoRunAiResearch(view) {
  const mode = value("#explainMode", "auto");
  if (mode !== "auto") return;
  const key = `${view?.selected_date || view?.date || "auto"}:${view?.matches_count || 0}:${view?.provider_used || "unknown"}`;
  if (state.autoAiResearchKey === key) return;
  state.autoAiResearchKey = key;
  setAiAutoStatus("running", "DeepSeek Pro 自动研究中", "正在读取 Top 单关、每日 2串1 / 3串1候选和被拒原因，完成后会自动保存研究记录。");
  const box = qs("#aiComboResearchBox");
  if (box) {
    box.innerHTML = `
      <div class="aiRunningCard">
        <span>DS Pro 自动研究</span>
        <strong>正在进入 auto AI 研究层</strong>
        <p>后端会自动判断 DS Pro 是否可用；可用就调用 DS Pro，不可用就改用本地研究摘要。AI 只做解释和复盘，不改概率和组合筛选。</p>
      </div>
    `;
  }
  window.setTimeout(() => loadAiComboResearch(), 250);
}

async function loadAiComboResearch() {
  const explainMode = value("#explainMode", "auto");
  const aiProvider = aiProviderParam();
  const runAi = aiRunParam();
  const box = qs("#aiComboResearchBox");
  setAiAutoStatus("running", runAi ? "自动 AI 研究中" : "正在生成本地研究包", runAi ? "后端会自动选择 DS Pro 或本地研究摘要；AI 只做解释和学习摘要。" : "本地模式不会消耗 token。");
  if (box) {
    box.innerHTML = `
      <div class="aiRunningCard">
        <span>${runAi ? "DS Pro 自动研究" : "本地研究"}</span>
        <strong>${runAi ? "自动 AI 研究中" : "正在生成本地研究包"}</strong>
        <p>${runAi ? "后端会自动判断 DS Pro 是否可用；可用时才消耗 token 做长分析，否则改用本地研究摘要。AI 不参与概率、EV、候选筛选或组合决策。" : "本地模式不会消耗 token。"}</p>
      </div>
    `;
  }
  const payload = await request("/api/view/ai-combo-research", {
    provider: providerParam(),
    date: state.todayView?.selected_date || currentDateParam(),
    bankroll: bankrollParam(),
    risk_profile: riskProfileParam(),
    external_signals: externalSignalsParam(),
    ai_provider: aiProvider,
    run: runAi,
    refresh: "1",
  }, runAi ? "自动生成 AI 组合研究摘要" : "生成本地组合研究包", runAi ? 150000 : 45000);
  if (payload.ok) {
    const data = payload.data || {};
    renderAiComboResearch(data);
    await autoArchiveResearch(data);
    const dsDone = Boolean(data.ds_completed || data.reused_from_cached_ds);
    if (!dsDone && runAi) {
      setAiAutoStatus("fallback", "DS 未完成，本地研究已保留", data.display_status_zh || data.fallback_reason || "本轮 DS 没有返回可用摘要，系统已保留本地研究包并进入赛后学习。可稍后重试 DS，不影响候选票展示。");
    }
    return;
  }
  setAiAutoStatus("fallback", "AI 研究仍在等待，本地结果已保留", payload.error?.message || "AI 长分析本次没有在前台等待时间内完成，候选票和本地研究摘要仍可用。");
  if (box) {
    box.innerHTML = `
      <div class="emptyState">
        AI 长分析没有在前台等待时间内完成：${C.escapeHtml(payload.error?.message || "候选票和本地研究摘要仍可用，可稍后重试 DS。")}
      </div>
    `;
  }
}

async function autoArchiveResearch(aiResearchView = {}) {
  const runAi = aiRunParam();
  const dsAlreadyDone = Boolean(aiResearchView.ds_completed || aiResearchView.reused_from_cached_ds);
  const archiveRunAi = dsAlreadyDone ? runAi : "";
  setAiAutoStatus("running", "正在保存研究档案", dsAlreadyDone ? "DS 研究摘要已生成，正在复用缓存写入赛前研究档案。" : "本地研究摘要已生成，正在写入赛前研究档案；不重复触发 DS。 ");
  const payload = await request("/api/learning/auto-archive-research", {
    provider: providerParam(),
    date: state.todayView?.selected_date || currentDateParam(),
    bankroll: bankrollParam(),
    risk_profile: riskProfileParam(),
    external_signals: externalSignalsParam(),
    ai_provider: dsAlreadyDone ? aiProviderParam() : "local",
    run_ai: archiveRunAi,
  }, "自动保存赛前研究档案", 120000);
  if (!payload.ok) {
    renderResearchArchiveStatus({
      status: "error",
      summary_zh: payload.error?.message || "研究档案保存失败，可稍后点击重新跑 AI 研究。",
    });
    setAiAutoStatus("fallback", "研究摘要已生成，档案保存待重试", payload.error?.message || "自动存档未完成，研究摘要仍显示在页面。");
    return;
  }
  const saved = payload.data || {};
  state.latestResearchArchive = saved;
  applyLearningPackPaths(saved);
  renderResearchArchiveStatus(saved);
  const usedDs = Boolean(saved.ds_completed || aiResearchView.ds_completed);
  setAiAutoStatus(
    usedDs ? "done" : "fallback",
    usedDs ? "DS 研究已存档" : "本地研究已存档",
    `${saved.summary_zh || "研究档案已保存。"} ${saved.token_total ? `本次记录 token ${saved.token_total}。` : "本轮未记录外部 token；候选票和本地研究仍已进入学习档案。"}`
  );
}

function applyLearningPackPaths(saved = {}) {
  const obsInput = qs("#learningObservationsPath");
  const resultsInput = qs("#learningResultsPath");
  const closingInput = qs("#learningClosingOddsPath");
  if (obsInput && saved.observations_path) obsInput.value = saved.observations_path;
  if (resultsInput && saved.results_path) resultsInput.value = saved.results_path;
  if (closingInput && saved.closing_odds_path) closingInput.value = saved.closing_odds_path;
  if (saved.observations_path) {
    state.lastLearningPack = {
      observations_path: saved.observations_path,
      results_path: saved.results_path,
      closing_odds_path: saved.closing_odds_path,
      observations_count: saved.observations_count,
      rejected_combo_count: saved.rejected_combo_count,
      summary_zh: saved.summary_zh,
    };
    updateLearningFlowStatus();
  }
}

function renderResearchArchiveStatus(status = {}) {
  const data = status.archive ? status : (status.research_archive_status || status);
  const latest = data.latest || {};
  const path = data.path || data.latest_path || latest.path || "";
  const observationsPath = data.observations_path || latest.observations_path || "";
  const resultsPath = data.results_path || latest.results_path || "";
  const closingPath = data.closing_odds_path || latest.closing_odds_path || "";
  const archiveStatus = data.status || (path ? "saved" : "empty");
  const dsStatus = data.ai_status || data.ds_status || latest.ds_status || "unknown";
  const tokenTotal = data.token_total ?? latest.token_total ?? "N/A";
  const savedAt = data.created_at || latest.created_at || "";
  const clvFollowup = data.clv_followup || latest.clv_followup || {};
  const clvPending = data.clv_pending_count ?? latest.clv_pending_count ?? clvFollowup.pending_count ?? 0;
  const clvPriorityRows = clvFollowup.priority_rows || latest.clv_priority_rows || [];
  const title = archiveStatus === "saved" || archiveStatus === "available"
    ? "赛前研究档案已保存"
    : archiveStatus === "error"
      ? "赛前研究档案待重试"
      : "赛前研究档案待生成";
  const body = data.summary_zh || (path ? "本次 T+1 研究已进入本地档案，赛后可回填比分和收盘赔率。" : "AI/本地研究完成后会自动保存。");
  const html = `
    <section class="researchArchiveCard status-${C.escapeHtml(archiveStatus)}">
      <div>
        <span>RESEARCH ARCHIVE</span>
        <strong>${C.escapeHtml(title)}</strong>
        <p>${C.escapeHtml(body)}</p>
      </div>
      <div class="archiveMetaGrid">
        <article><b>${C.escapeHtml(dsStatus)}</b><em>DS 状态</em></article>
        <article><b>${C.escapeHtml(String(tokenTotal))}</b><em>token</em></article>
        <article><b>${C.escapeHtml(data.observations_count ?? latest.observations_count ?? "N/A")}</b><em>观察项</em></article>
        <article><b>${C.escapeHtml(String(clvPending))}</b><em>CLV待填</em></article>
      </div>
      ${clvFollowup.summary_zh ? `<p class="archivePath">CLV：${C.escapeHtml(clvFollowup.summary_zh)}</p>` : ""}
      ${clvPriorityRows.length ? `<details class="detailDrawer archiveMiniDrawer"><summary>查看优先回填收盘赔率</summary>${C.table(clvPriorityRows.slice(0, 6), [
        { key: "match", label: "比赛" },
        { key: "play_type", label: "玩法" },
        { key: "direction", label: "方向" },
        { key: "entry_odds", label: "赛前赔率" },
        { key: "closing_odds", label: "收盘赔率" },
        { key: "status_zh", label: "状态" },
      ])}</details>` : ""}
      ${path ? `<p class="archivePath">档案：${C.escapeHtml(path)}</p>` : ""}
      ${savedAt ? `<p class="archivePath">保存时间：${C.escapeHtml(savedAt)}</p>` : ""}
      ${observationsPath ? `<p class="archivePath">赛前观察：${C.escapeHtml(observationsPath)}</p>` : ""}
      ${resultsPath ? `<p class="archivePath">比分模板：${C.escapeHtml(resultsPath)}</p>` : ""}
      ${closingPath ? `<p class="archivePath">收盘赔率模板：${C.escapeHtml(closingPath)}</p>` : ""}
      <div class="archiveActions">
        <button type="button" class="secondary miniLearningBtn" onclick="jumpToView('learning')">去赛后学习</button>
        <button type="button" class="secondary miniLearningBtn" onclick="loadAiComboResearch()">重新研究并存档</button>
      </div>
    </section>
  `;
  ["#researchArchivePanel", "#researchArchiveDetailPanel"].forEach((selector) => {
    const target = qs(selector);
    if (target) target.innerHTML = html;
  });
}


const AI_RESEARCH_MEMORY_KEY = "jcEdgeAiResearchMemoryV1";
const WORKFLOW_ACTION_MEMORY_KEY = "jcEdgeWorkflowActionHistoryV1";
const WORKFLOW_SCORE_MEMORY_KEY = "jcEdgeWorkflowScoreMemoryV1";

function aiResearchDate(view) {
  const packet = view.research_packet || {};
  return packet.selected_date || packet.date || view.selected_date || currentDateParam() || "待定日期";
}

function summarizeComboLegs(candidate) {
  if (!candidate) return "暂无";
  return candidate.legs || candidate.match || candidate.label_zh || candidate.reason_zh || "暂无";
}

function readAiResearchMemory() {
  try {
    const raw = window.localStorage.getItem(AI_RESEARCH_MEMORY_KEY);
    const rows = raw ? JSON.parse(raw) : [];
    return Array.isArray(rows) ? rows.map(normalizeAiMemoryRecord) : [];
  } catch (error) {
    return [];
  }
}

function normalizeAiMemoryRecord(row) {
  const record = row && typeof row === "object" ? row : {};
  return {
    schema_version: record.schema_version || "ai_memory_v1",
    saved_at: record.saved_at || "",
    selected_date: record.selected_date || "待定日期",
    provider_used: record.provider_used || "unknown",
    ai_provider: record.ai_provider || "local",
    ai_status: record.ai_status || "unknown",
    run_ai: Boolean(record.run_ai),
    ds_call_count: Number(record.ds_call_count || 0),
    ai_quality_grade: record.ai_quality_grade || "N/A",
    ai_quality_score: record.ai_quality_score ?? "N/A",
    ai_quality_source: record.ai_quality_source || "unknown",
    top_coverage: record.top_coverage || "0/0",
    top_coverage_message: record.top_coverage_message || "",
    cache_key: record.cache_key || `${record.selected_date || "unknown"}|${record.ai_provider || "local"}`,
    headline: record.headline || "今日研究摘要",
    best_single: record.best_single || "暂无",
    daily_2x1: record.daily_2x1 || "暂无",
    daily_3x1: record.daily_3x1 || "暂无",
    summary_preview: record.summary_preview || "",
  };
}

function writeAiResearchMemory(rows) {
  try {
    window.localStorage.setItem(AI_RESEARCH_MEMORY_KEY, JSON.stringify(rows.slice(0, 12).map(normalizeAiMemoryRecord)));
  } catch (error) {
    // Browser localStorage may be unavailable; skip without blocking the app.
  }
}

function readWorkflowActionHistory() {
  try {
    const raw = window.localStorage.getItem(WORKFLOW_ACTION_MEMORY_KEY);
    const rows = raw ? JSON.parse(raw) : [];
    return Array.isArray(rows) ? rows.map(normalizeWorkflowActionRecord).map(normalizePersistedWorkflowActionRecord).filter((row) => row.label) : [];
  } catch (error) {
    return [];
  }
}

function normalizeWorkflowActionRecord(row) {
  const record = row && typeof row === "object" ? row : {};
  const before = Number(record.score_before);
  const after = Number(record.score_after);
  const delta = Number(record.score_delta);
  const label = String(record.label || "");
  return {
    action: String(record.action || workflowActionFromLabel(label)),
    label,
    message: String(record.message || ""),
    status: ["running", "done", "error", "planned"].includes(record.status) ? record.status : "running",
    time: String(record.time || ""),
    saved_at: String(record.saved_at || ""),
    score_before: Number.isFinite(before) ? before : null,
    score_after: Number.isFinite(after) ? after : null,
    score_delta: Number.isFinite(delta) ? delta : null,
  };
}

function workflowActionFromLabel(label = "") {
  const actions = {
    "数据源": "refresh_today",
    "Top信号": "run_optimizer",
    "组合纪律": "best_parlay",
    "AI研究": "ai_research",
    "赛后学习": "learning_pack",
    "下一次实验": "next_experiment_plan",
  };
  return actions[label] || "";
}

function normalizePersistedWorkflowActionRecord(row = {}) {
  if (row.status !== "running") return row;
  return {
    ...row,
    status: "error",
    message: "上次页面刷新或关闭前未确认完成，请按需重试。",
  };
}

function writeWorkflowActionHistory(rows) {
  try {
    window.localStorage.setItem(WORKFLOW_ACTION_MEMORY_KEY, JSON.stringify((rows || []).slice(0, 6).map(normalizeWorkflowActionRecord)));
  } catch (error) {
    // Browser localStorage may be unavailable; skip without blocking the app.
  }
}

function saveAiResearchMemory(view, text) {
  const packet = view.research_packet || {};
  const ai = view.ai_summary || {};
  const qualityAudit = (view.structured_notes || {}).quality_audit || {};
  const costLedger = view.ai_cost_ledger || {};
  const topCoverage = qualityAudit.top_card_coverage || {};
  const selectedDate = aiResearchDate(view);
  const aiProvider = ai.provider || view.ai_provider || packet.ai_provider || "local";
  const aiStatus = view.ds_status || ai.ds_status || ai.status || view.ai_status || packet.ai_status || "unknown";
  const cacheKey = `${selectedDate}|${packet.provider_used || view.provider_used || "unknown"}|${aiProvider}`;
  const cards = buildAiBriefCards(view, text);
  const record = {
    schema_version: "ai_memory_v2",
    saved_at: new Date().toLocaleString("zh-CN", { hour12: false }),
    selected_date: selectedDate,
    provider_used: packet.provider_used || view.provider_used || "unknown",
    ai_provider: aiProvider,
    ai_status: aiStatus,
    run_ai: Boolean(view.run_ai || packet.run_ai),
    ds_call_count: costLedger.deepseek_call_count ?? 0,
    ai_quality_grade: qualityAudit.grade || "N/A",
    ai_quality_score: qualityAudit.score ?? "N/A",
    ai_quality_source: qualityAudit.structured_source || "unknown",
    top_coverage: `${topCoverage.matched_count ?? 0}/${topCoverage.expected_count ?? 0}`,
    top_coverage_message: topCoverage.message_zh || "",
    cache_key: cacheKey,
    headline: cards[0]?.value || "今日研究摘要",
    best_single: summarizeComboLegs(packet.best_single || packet.top_single || packet.daily_single_candidate),
    daily_2x1: summarizeComboLegs(packet.daily_2x1_candidate || packet.best_2x1),
    daily_3x1: summarizeComboLegs(packet.daily_3x1_candidate || packet.best_3x1),
    summary_preview: shortText(text || view.local_summary_zh || view.ai_summary_zh || "", 260),
  };
  const rows = readAiResearchMemory().filter((item) => item.cache_key !== cacheKey);
  writeAiResearchMemory([record, ...rows]);
  renderAiResearchMemory();
  if (state.todayView) renderWorkflowScore(state.todayView, "ready");
  const usedDeepSeek = aiProvider === "deepseek" && aiStatus === "loaded";
  setAiAutoStatus(
    usedDeepSeek ? "done" : "fallback",
    usedDeepSeek ? "DS Pro 研究已完成" : "本地研究摘要已完成",
    usedDeepSeek ? "摘要已进入本地 AI 记录；系统随后会自动保存赛前研究档案。" : "没有使用外部 AI 或外部 AI 不可用；摘要仍会进入本地记录并自动归档。"
  );
}

function renderAiResearchMemory() {
  const panel = qs("#aiResearchMemoryPanel");
  if (!panel) return;
  const rows = readAiResearchMemory();
  if (!rows.length) {
    panel.innerHTML = `<div class="researchMemoryEmpty">每日 AI 研究记录会在刷新后自动保存在本浏览器，用于赛后对照学习。</div>`;
    return;
  }
  const trend = aiResearchTrendDetails(rows.slice(0, 6));
    panel.innerHTML = `
    <div class="researchMemoryHead">
      <div><span>本地记录</span><strong>每日 AI 研究记录</strong></div>
      <em>仅保存在本机浏览器，最多保留 12 条。</em>
    </div>
    <article class="aiTrendCard ${C.escapeHtml(trend.status || "watch")}">
      <span>AI 学习趋势</span>
      <strong>${C.escapeHtml(trend.title || "AI 研究趋势")}</strong>
      <p>${C.escapeHtml(trend.message || "")}</p>
      ${Array.isArray(trend.metricCards) ? `
        <div class="aiTrendMetrics">
          ${trend.metricCards.map((metric) => `
            <article>
              <span>${C.escapeHtml(metric.label)}</span>
              <b>${C.escapeHtml(metric.value)}</b>
            </article>
          `).join("")}
        </div>
      ` : ""}
      ${Array.isArray(trend.scoreEffects) && trend.scoreEffects.length ? `
        <div class="aiTrendEffects">
          ${trend.scoreEffects.slice(0, 4).map((effect) => `
            <div>
              <b>${C.escapeHtml(effect.label)}</b>
              <span>${C.escapeHtml(effect.text)}</span>
            </div>
          `).join("")}
        </div>
      ` : ""}
      ${Array.isArray(trend.todos) && trend.todos.length ? `
        <ul class="aiTrendTodos">
          ${trend.todos.map((todo) => `<li>${C.escapeHtml(todo)}</li>`).join("")}
        </ul>
      ` : ""}
      <em>${C.escapeHtml(trend.next || "")}</em>
      <div class="aiTrendActions">
        <button type="button" class="secondary" onclick="${trend.status === "good" ? "jumpToView('learning')" : "loadAiComboResearch()"}">${C.escapeHtml(trend.primaryAction || "重新跑 auto 研究")}</button>
        <button type="button" class="ghost" onclick="${trend.status === "good" ? "loadAiComboResearch()" : "jumpToView('learning')"}">${C.escapeHtml(trend.secondaryAction || "去赛后学习")}</button>
      </div>
    </article>
    <div class="researchMemoryGrid">${rows.slice(0, 3).map((row) => `
      <article class="researchMemoryCard">
        <div><span>${C.escapeHtml(row.selected_date || "待定日期")}</span><b>${C.escapeHtml(row.ai_provider || "local")} · ${C.escapeHtml(row.ai_status || "unknown")}</b></div>
        <strong>${C.escapeHtml(row.headline || "今日研究摘要")}</strong>
        <p>${C.escapeHtml(row.summary_preview || "暂无摘要")}</p>
        <div class="researchMemoryMeta">
          <span>DS ${C.escapeHtml(row.ds_call_count ?? 0)} 次</span>
          <span>质量 ${C.escapeHtml(row.ai_quality_grade || "N/A")} / ${C.escapeHtml(row.ai_quality_score ?? "N/A")}</span>
          <span>Top ${C.escapeHtml(row.top_coverage || "0/0")}</span>
        </div>
        <ul>
          <li>单关：${C.escapeHtml(shortText(row.best_single || "暂无", 54))}</li>
          <li>2串1：${C.escapeHtml(shortText(row.daily_2x1 || "暂无", 54))}</li>
          <li>3串1：${C.escapeHtml(shortText(row.daily_3x1 || "暂无", 54))}</li>
        </ul>
        ${row.top_coverage_message ? `<p class="mutedLine">${C.escapeHtml(row.top_coverage_message)}</p>` : ""}
        <em>${C.escapeHtml(row.saved_at || "")} · 赛后可到“赛后学习”对照。</em>
      </article>
    `).join("")}</div>
  `;
}

function renderAiComboResearch(view) {
  const box = qs("#aiComboResearchBox");
  if (!box) return;
  const ai = view.ai_summary || {};
  const aiStatus = view.ai_research_status || (view.llm_status || {}).ai_research_status || {};
  const budget = view.token_budget || {};
  const autoPolicy = view.auto_policy || {};
  const autoPlan = view.auto_execution_plan || {};
  const qualityAudit = (view.structured_notes || {}).quality_audit || {};
  const structuredRetry = ai.structured_retry || {};
  const coverageRetry = ai.structured_coverage_retry || {};
  const costLedger = view.ai_cost_ledger || {};
  const text = ai.text || view.local_summary_zh || "暂无摘要。";
  const briefCards = buildAiBriefCards(view, text);
  state.latestAiResearch = {
    provider: ai.provider || view.ai_provider_resolved || autoPolicy.resolved_provider || "local",
    status: aiStatus.status || view.ds_status || ai.ds_status || ai.status || "unknown",
    ds_completed: Boolean(view.ds_completed || ai.ds_completed || (ai.provider === "deepseek" && ai.status === "loaded")),
    ai_research_status: aiStatus,
    auto_mode: autoPlan.mode || autoPolicy.mode || "local",
    structured_notes: view.structured_notes || {},
    quality_audit: qualityAudit,
    cards: briefCards,
    full_text: text,
    title: briefCards[0]?.title || "今日研究摘要",
    body: briefCards[0]?.body || shortText(text, 180),
  };
  box.innerHTML = `
    <div class="aiBriefGrid">
      ${briefCards.map((card) => `
        <article class="aiBriefCard">
          <span>${C.escapeHtml(card.kicker)}</span>
          <strong>${C.escapeHtml(card.title)}</strong>
          <p>${C.escapeHtml(card.body)}</p>
        </article>
      `).join("")}
    </div>
    <details class="tokenLedger">
      <summary>DeepSeek / auto 研究账本</summary>
      ${autoPolicy.message_zh ? `
        <div>
          <span>auto 解析</span>
          <strong>${C.escapeHtml(autoPolicy.resolved_provider || ai.provider || "local")}</strong>
          <p>${C.escapeHtml(autoPolicy.message_zh || "")}</p>
          <p class="mutedLine">${C.escapeHtml(autoPolicy.scope_zh || "AI 只做解释和复盘，不改写概率、EV 或组合筛选。")}</p>
        </div>
      ` : ""}
      ${Array.isArray(autoPlan.steps) && autoPlan.steps.length ? `
        <div>
          <span>auto 流水线</span>
          <strong>${C.escapeHtml(autoPlan.mode || "auto")}</strong>
          <div class="autoPlanSteps">
            ${autoPlan.steps.map((step) => `
              <article class="autoPlanStep ${C.escapeHtml(step.status || "pending")}">
                <b>${C.escapeHtml(step.name || "自动步骤")}</b>
                <em>${C.escapeHtml(step.status || "unknown")}</em>
                <p>${C.escapeHtml(step.message_zh || "")}</p>
              </article>
            `).join("")}
          </div>
          <p class="mutedLine">${C.escapeHtml(autoPlan.token_policy_zh || "只有 DS Pro 就绪时才消耗 token。")}</p>
        </div>
      ` : ""}
      ${qualityAudit.score !== undefined ? `
        <div>
          <span>AI 结构化质量</span>
          <strong>${C.escapeHtml(qualityAudit.grade || "N/A")} / ${C.escapeHtml(qualityAudit.score)}</strong>
          <p>${C.escapeHtml(qualityAudit.message_zh || "结构化研究质量待评估。")}</p>
          <div class="tokenLedgerGrid">
            <article><span>覆盖项</span><b>${C.escapeHtml(`${qualityAudit.covered_count ?? 0}/${qualityAudit.required_count ?? 0}`)}</b></article>
            <article><span>来源</span><b>${C.escapeHtml(qualityAudit.structured_source || "unknown")}</b></article>
            <article><span>兜底</span><b>${C.escapeHtml(qualityAudit.fallback_used ? "是" : "否")}</b></article>
            <article><span>Top覆盖</span><b>${C.escapeHtml(`${qualityAudit.top_card_coverage?.matched_count ?? 0}/${qualityAudit.top_card_coverage?.expected_count ?? 0}`)}</b></article>
          </div>
          ${qualityAudit.top_card_coverage?.missing_targets?.length ? `
            <p class="mutedLine">未覆盖 Top 项：${C.escapeHtml(qualityAudit.top_card_coverage.missing_targets.slice(0, 4).join("；"))}</p>
          ` : ""}
        </div>
      ` : ""}
      ${structuredRetry.attempted ? `
        <div>
          <span>结构化短重试</span>
          <strong>${C.escapeHtml(structuredRetry.success ? "已补齐" : "已兜底")}</strong>
          <p>${C.escapeHtml(structuredRetry.message_zh || "DS 结构化短重试已执行。")}</p>
        </div>
      ` : ""}
      ${coverageRetry.attempted ? `
        <div>
          <span>Top 覆盖补洞</span>
          <strong>${C.escapeHtml(coverageRetry.success ? "已补洞" : "已兜底")}</strong>
          <p>${C.escapeHtml(coverageRetry.message_zh || "DS Top 覆盖补洞已执行。")}</p>
        </div>
      ` : ""}
      ${costLedger.version ? `
        <div>
          <span>AI 成本账本</span>
          <strong>${C.escapeHtml(`${costLedger.deepseek_call_count ?? 0} 次 DS Pro`)}</strong>
          <p>${C.escapeHtml(costLedger.message_zh || "本次 AI 调用账本已记录。")}</p>
          <div class="tokenLedgerGrid">
            <article><span>调用步骤</span><b>${C.escapeHtml(costLedger.call_count ?? 0)}</b></article>
            <article><span>实际输入</span><b>${C.escapeHtml(costLedger.actual_input_tokens ?? "N/A")}</b></article>
            <article><span>实际输出</span><b>${C.escapeHtml(costLedger.actual_output_tokens ?? "N/A")}</b></article>
            <article><span>实际合计</span><b>${C.escapeHtml(costLedger.actual_total_tokens ?? "N/A")}</b></article>
            <article><span>输入估算</span><b>${C.escapeHtml(costLedger.estimated_input_tokens ?? "N/A")}</b></article>
            <article><span>输出上限/次</span><b>${C.escapeHtml(costLedger.max_output_tokens_per_call ?? "N/A")}</b></article>
            <article><span>预算状态</span><b>${C.escapeHtml(costLedger.within_auto_budget ? "预算内" : "超预算")}</b></article>
            <article><span>单次上界</span><b>${C.escapeHtml(costLedger.per_call_upper_bound_tokens ?? "N/A")}</b></article>
            <article><span>总上界</span><b>${C.escapeHtml(costLedger.estimated_upper_bound_tokens ?? "N/A")}</b></article>
          </div>
          <p class="mutedLine">${C.escapeHtml(costLedger.estimate_policy_zh || "这是 token 上限估算，不是实际账单。")}</p>
          ${Array.isArray(costLedger.calls) && costLedger.calls.length ? `
            <ul class="aiCostCalls">
              ${costLedger.calls.map((call) => `<li><b>${C.escapeHtml(call.step || "step")}</b> · ${C.escapeHtml(call.status || "unknown")} · ${C.escapeHtml(call.reason_zh || "")}</li>`).join("")}
            </ul>
          ` : ""}
        </div>
      ` : ""}
      <div>
        <span>调用状态</span>
        <strong>${C.escapeHtml(aiStatus.label_zh || (view.ds_completed || ai.provider === "deepseek" ? "本次已调用 DeepSeek Pro" : "本次未调用 DeepSeek Pro"))}</strong>
        <p>${C.escapeHtml(aiStatus.summary_zh || view.fallback_reason || ai.fallback_reason || view.auto_mode_semantics_zh || view.token_learning_zh || "自动研究模式会在刷新后自动尝试调用 DeepSeek Pro；本地研究摘要不消耗 token。")}</p>
        ${(view.token_total || ai.token_total) ? `<em>本次真实消耗：输入 ${C.escapeHtml(view.token_in ?? ai.token_in ?? "N/A")} / 输出 ${C.escapeHtml(view.token_out ?? ai.token_out ?? "N/A")} / 合计 ${C.escapeHtml(view.token_total ?? ai.token_total ?? "N/A")} token</em>` : ""}
      </div>
      <div class="tokenLedgerGrid">
        <article><span>预计输入</span><b>${C.escapeHtml(budget.estimated_input_tokens ?? "N/A")}</b></article>
        <article><span>输出上限</span><b>${C.escapeHtml(budget.max_output_tokens ?? "N/A")}</b></article>
        <article><span>最大合计</span><b>${C.escapeHtml(budget.estimated_max_total_tokens ?? "N/A")}</b></article>
        <article><span>缓存键</span><b>${C.escapeHtml(budget.research_cache_key || "local")}</b></article>
      </div>
      <p class="mutedLine">${C.escapeHtml(budget.cost_control_zh || "自动研究模式默认用 DeepSeek Pro 做研究解释；失败时自动改用本地研究摘要。")}</p>
      ${view.no_combo_reason ? `<div class="insightCard">
        <strong>当前为何暂不组合</strong>
        <p>${C.escapeHtml(view.no_combo_reason)}</p>
      </div>` : ""}
      ${(view.latest_daily_summary_zh || (Array.isArray(view.window_learning_summaries_zh) && view.window_learning_summaries_zh.length)) ? `
        <div class="insightCard">
          <strong>赛后学习快照</strong>
          ${view.latest_daily_summary_zh ? `<p>${C.escapeHtml(view.latest_daily_summary_zh)}</p>` : ""}
          ${Array.isArray(view.window_learning_summaries_zh) && view.window_learning_summaries_zh.length ? C.list(view.window_learning_summaries_zh.slice(0, 2)) : ""}
        </div>
      ` : ""}
    </details>
    <details class="fullResearchDrawer">
      <summary>查看完整研究原文</summary>
      <pre class="researchSummary">${C.escapeHtml(text)}</pre>
      <h4>研究边界</h4>
      ${C.list([
        view.safety_zh || "AI 只做研究解释，不参与真实下单。",
        `AI 状态：${aiStatus.label_zh || ai.provider || "local"} / ${aiStatus.status || view.ds_status || ai.ds_status || ai.status || "not_requested"}`,
        view.no_combo_reason ? `暂不组合原因：${view.no_combo_reason}` : "",
        ((view.credibility_gate || {}).reason_zh) ? `可信度门控：${(view.credibility_gate || {}).reason_zh}` : "",
        aiStatus.summary_zh || view.fallback_reason || ai.fallback_reason || "当前没有额外回退说明。",
        (view.research_packet || {}).task_zh || "判断今天是否存在可研究组合。",
      ].filter(Boolean))}
    </details>
  `;
  saveAiResearchMemory(view, text);
  if (state.todayView) {
    renderTodayOneLook(state.todayView);
    renderTodayTopSections(state.todayView);
  }
}

function buildAiBriefCards(view, text) {
  const structured = view.structured_notes || {};
  const structuredCards = buildStructuredAiBriefCards(structured);
  if (structuredCards.length) return structuredCards;
  const packet = view.research_packet || {};
  const findLine = (patterns, fallback) => {
    const lines = String(text || "").split(/\n+/).map((line) => line.replace(/[*#`>-]/g, "").trim()).filter(Boolean);
    for (const pattern of patterns) {
      const found = lines.find((line) => line.includes(pattern));
      if (found) return found.replace(/^[:：\s]+/, "");
    }
    return fallback;
  };
  const bestSingle = packet.best_single?.match || packet.top_single?.match || findLine(["优先单关", "当前“优先”单关", "当前优先单关"], "先看 Top 单关，但需要赔率、情报和校准同时支持。");
  const closestCombo = packet.daily_2x1_candidate?.legs || packet.closest_2x1?.legs || packet.best_2x1?.legs || findLine(["每日 2串1候选", "最接近的 2", "最接近 2串1", "2 串 1"], "若 2串1 未过门控，只保留为被拒复盘对象。");
  const closestCombo3 = packet.daily_3x1_candidate?.legs || packet.best_3x1?.legs || findLine(["每日 3串1候选", "3 串 1", "3串1"], "3串1 只作最高风险纸面候选。");
  const noCombo = view.no_combo_reason || packet.no_combo_reason || findLine(["不强行组合", "不存在任何", "被拒"], "没有通过可信度、赔率覆盖和风险纪律时，不强行拼组合。");
  const missing = findLine(["伤停", "首发", "天气", "新闻"], "临场必须复核伤停、首发、天气、新闻面和赔率漂移。");
  return [
    {
      kicker: "今日结论",
      title: cleanAiTitle(findLine(["核心结论", "今日先给候选，再看等级", "不强行组合", "强观察"], "先看信号，不强行组合")),
      body: noCombo,
    },
    {
      kicker: "最强观察",
      title: cleanAiTitle(bestSingle),
      body: missing,
    },
    {
      kicker: "组合纪律",
      title: "组合纪律",
      body: `2串1：${closestCombo}；3串1：${closestCombo3}`,
    },
  ];
}

function buildStructuredAiBriefCards(structured) {
  if (!structured || !structured.version) return [];
  const single = (structured.single_notes || [])[0] || {};
  const combo = (structured.combo_notes || [])[0] || {};
  return [
    {
      kicker: "今日结论",
      title: cleanAiTitle(structured.daily_summary_zh || "先看信号，不强行组合"),
      body: structured.missing_review_zh || "赛日前继续复核关键情报。",
    },
    {
      kicker: "最强观察",
      title: cleanAiTitle(single.target || "Top 单关"),
      body: single.note_zh || single.usage_zh || "先看赔率覆盖与临场复核。",
    },
    {
      kicker: "组合纪律",
      title: cleanAiTitle(combo.target || "Top 2串1"),
      body: combo.note_zh || combo.usage_zh || "组合必须通过可信度、相关性和风险纪律。",
    },
  ];
}

function cleanAiTitle(text) {
  const value = String(text || "").replace(/^核心结论[:：]?\s*/, "").trim();
  return value.length > 34 ? `${value.slice(0, 34)}…` : value;
}

function buildTodaySignalLight(view, single, combo, combo3) {
  const gate = view.credibility_gate || view.credibility_audit?.credibility_gate || {};
  if (view.lightweight_homepage) {
    const matches = Number(view.matches_count || 0);
    return {
      level: matches > 0 ? "watch" : "wait",
      label: matches > 0 ? "预筛" : "等待",
      title: matches > 0 ? "已找到可售比赛" : "先用赛前优化生成候选",
      body: matches > 0
        ? `已快速确认 ${matches} 场可售比赛，数据源正常；完整概率、组合纪律和情报审计请进入赛前优化或组合审核。`
        : "数据源本轮较慢或暂未返回完整场次；不要停在这里，直接点【生成今日观察】生成单关、2串1、3串1纸面候选，完整数据回来后会自动替换。",
    };
  }
  const score = Number(view.credibility_audit?.credibility_score ?? view.credibility_score ?? gate.score ?? 0);
  const hasSelectedCombo = [combo, combo3].some((row) => row && isComboSelected(row));
  const hasSingle = Boolean(single && (single.match || single.direction));
  if (gate.combo_gate === "open" && hasSelectedCombo && score >= 65) {
    return {
      level: "strong",
      label: "强观察",
        title: "有组合通过纪律",
      body: "先看通过门控组合，再逐腿复核赔率、伤停、首发和天气。",
    };
  }
  if (hasSingle && score >= 50) {
    return {
      level: "watch",
      label: "弱观察",
      title: "先看单关，不强行串联",
      body: gate.reason_zh || "有单关可继续观察，但组合仍需要更高可信度和临场确认。",
    };
  }
  if (hasSingle) {
    return {
      level: "wait",
      label: "等待情报",
      title: "有候选，但可信度不足",
      body: gate.reason_zh || "先补齐伤停、首发、天气、新闻面和终盘赔率，再复核。",
    };
  }
  return {
    level: "pass",
    label: "放弃",
    title: "暂无可用观察",
    body: "没有足够赔率价值或可信度支撑，今天先跳过。",
  };
}

function reasonTags(text) {
  const value = String(text || "");
  const tags = [];
  if (/可信度|信心|情报/.test(value)) tags.push("可信度不足");
  if (/伤停|首发|天气|新闻|战意|旅行/.test(value)) tags.push("情报缺口");
  if (/相关性/.test(value)) tags.push("相关性折扣");
  if (/风险|very_high|高风险/.test(value)) tags.push("风险偏高");
  if (/命中概率|纪律门槛/.test(value)) tags.push("命中率不足");
  if (/EV 不足|Edge 不足|安全边际/.test(value)) tags.push("优势偏薄");
  return Array.from(new Set(tags)).slice(0, 4);
}

function renderTodayOneLook(view) {
  const box = qs("#todayOneLook");
  if (!box) return;
  const finalCard = view.final_decision_card || {};
  const single = (view.top_singles || [])[0] || {};
  const combo = (view.top_parlay_2x1 || view.top_2x1 || view.top_2x1_display || [])[0] || {};
  const combo3 = (view.top_parlay_3x1 || view.top_3x1 || view.top_3x1_display || [])[0] || {};
  const gate = view.credibility_gate || view.credibility_audit?.credibility_gate || {};
  const credibility = view.credibility_audit?.credibility_score ?? view.credibility_score ?? "N/A";
  const missing = view.missing_information || view.missing_signals || view.intelligence_completeness?.missing_items || [];
  const missingText = Array.isArray(missing) ? missing.slice(0, 5).join("、") : String(missing || "伤停、首发、天气、新闻面");
  const comboLabel = combo.legs || combo.match || gate.label_zh || "今日相对2串1候选";
  const comboReason = combo.combo_action_zh || combo.reject_reason || gate.reason_zh || "当前不强行组合，先看单关和临场复核。";
  const signalLight = buildTodaySignalLight(view, single, combo, combo3);
  const topTags = reasonTags(`${comboReason} ${combo3.reject_reason || ""} ${gate.reason_zh || ""}`);
  const aiLayer = view.ai_research_layer || {};
  const aiDigest = state.latestAiResearch || {};
  const aiTitle = aiDigest.title || (aiLayer.runtime_status === "loaded" ? "DS Pro 已参与研究" : (aiLayer.enabled ? "DS Pro 可自动研究" : (aiLayer.status_zh || "本地研究摘要")));
  const aiBody = aiDigest.body || aiLayer.runtime_notice_zh || aiLayer.display_status_zh || aiLayer.message_zh || "DS Pro 可用时会自动总结为什么看、为什么不串、赛后要学习什么；不可用时回退本地摘要。";
  const comboSummary = view.combo_gate_summary_zh || gate.reason_zh || comboReason;
  const dailyLanes = view.best_parlay_summary?.daily_output_lanes
    || view.optimizer?.best_parlay_summary?.daily_output_lanes
    || view.daily_output_lanes
    || [];
  const dailyLanesHtml = dailyOutputLanesPanel(dailyLanes);
  const noComboReason = view.no_combo_reason || gate.reason_zh || comboReason;
  const gateMode = String(gate.combo_gate || "");
  const hasDailyCombo = Boolean((combo && (combo.legs || combo.match)) || (combo3 && (combo3.legs || combo3.match)));
  const strictOpinion = gateMode === "open"
    ? "可以继续看组合，但仍要逐腿复核。"
    : gateMode === "restricted"
      ? "每日输出 2串1 纸面候选，3串1 先当高风险练习。"
      : hasDailyCombo ? "每日候选已输出，先看赔率覆盖和未过门控原因。" : "先别强行串联，把精力放在单关质量和情报补齐。";
  const statusBits = [
    signalLight.title,
    single.match ? `Top 单关：${single.match}` : "",
    gateMode === "open" ? "组合可继续复核" : "",
    gateMode === "restricted" ? "仅低风险 2串1 纸面候选" : "",
    gateMode === "closed" ? "当前暂不强行串联" : "",
    strictOpinion,
  ].filter(Boolean);
  if (view.lightweight_homepage && !dailyLanesHtml && !finalCard.verdict_zh) {
    const matches = Number(view.matches_count || 0);
    box.innerHTML = `
      <section class="todayActionFallback isPreflight">
        <div>
          <span>PRE-FLIGHT</span>
          <strong>${matches > 0 ? `已找到 ${matches} 场可售比赛` : "先跑赛前优化"}</strong>
          <p>${C.escapeHtml(matches > 0 ? "快速预读只确认比赛和数据源。要看真正有用的单关、2串1、3串1，请直接生成今日观察。" : "下一可售日预读暂未返回完整比赛，直接生成今日观察会尝试缓存、真实源和回退候选。")}</p>
        </div>
        <div class="todayFallbackSteps">
          <article><b>1</b><strong>赔率覆盖</strong><p>模型概率必须覆盖赔率盈亏线。</p></article>
          <article><b>2</b><strong>方向分散</strong><p>避免全是主胜/让胜。</p></article>
          <article><b>3</b><strong>赛后验证</strong><p>候选都进入复盘学习。</p></article>
        </div>
        <button type="button" class="primary" id="todayFallbackOptimizerBtn">生成今日观察</button>
      </section>
    `;
  } else if (finalCard.verdict_zh) {
    const blockers = finalCard.main_blockers_zh || [];
    box.innerHTML = `
      <section class="finalDecisionCard level-${C.escapeHtml(finalCard.level || "wait")}">
        <div class="finalDecisionHead">
          <span>FINAL READ</span>
          <strong>${C.escapeHtml(finalCard.verdict_zh || "今日观察待刷新")}</strong>
          <p>${C.escapeHtml(finalCard.why_zh || "先看证据，再看候选，不强行组合。")}</p>
        </div>
        <div class="finalDecisionMetrics">
          <article><span>比赛</span><b>${C.escapeHtml(String(finalCard.matches_count ?? view.matches_count ?? 0))}</b><em>${C.escapeHtml(finalCard.provider_used || view.provider_used || "auto")}</em></article>
          <article><span>可信度</span><b>${C.escapeHtml(finalCard.credibility_score == null ? "N/A" : `${finalCard.credibility_score}`)}</b><em>门控</em></article>
          <article><span>模型分</span><b>${C.escapeHtml(finalCard.professional_score == null ? "N/A" : `${finalCard.professional_score}`)}</b><em>职业审计</em></article>
          <article><span>长期分</span><b>${C.escapeHtml(finalCard.long_run_score == null ? "N/A" : `${finalCard.long_run_score}`)}</b><em>学习闭环</em></article>
        </div>
        <div class="finalDecisionBody">
          <article>
            <span>Top 单关</span>
            <p>${C.escapeHtml(finalCard.single_summary_zh || "暂无单关强信号")}</p>
          </article>
          <article>
            <span>组合态度</span>
            <p>${C.escapeHtml(finalCard.combo_summary_zh || "暂无优秀串联观察")}</p>
          </article>
        </div>
        <div class="finalDecisionBlockers">
          ${(blockers.length ? blockers : ["继续等待更可靠数据和赛后学习样本"]).slice(0, 5).map((item) => `<i>${C.escapeHtml(item)}</i>`).join("")}
        </div>
        <div class="finalDecisionAction">
          <button type="button" class="primary" data-jump-view="optimizer">生成今日观察</button>
          <button type="button" class="secondary" data-jump-view="bestparlay">看组合审核</button>
          <button type="button" class="secondary" data-jump-view="proscore">看模型体检</button>
          <em>${C.escapeHtml(finalCard.next_action_zh || "先刷新今日观察，再看赛前优化。")}</em>
        </div>
      </section>
      ${dailyLanesHtml}
    `;
  } else if (dailyLanesHtml) {
    box.innerHTML = dailyLanesHtml;
  } else {
    box.innerHTML = actionableTodayFallback("当前没有拿到完整首页结果，但不影响直接生成每日候选。");
  }
  setTodayQuickActionStatus(statusBits.join(" · "));
}

function renderToday(view) {
  stopTodayProgressTicker();
  view = mergeTodayWithOptimizer(view || {});
  state.todayView = view;
  const workflow = view.prematch_workflow || {};
  const aiStatus = todayAiStatus(view);
  const aiStatusLabel = aiStatus.label_zh || view.ai_research_layer?.runtime_status_zh || view.ai_research_layer?.status_zh || "待检查";
  const aiStatusSummary = todayAiStatusSummary(view);
  renderLearningPanel(view.learning_panel || {});
  renderSignalCategorySummary(view.top_singles || []);
  const pendingConfirmations = workflow.pending_confirmations || [];
  renderMatchdayChecklist(view.top_singles || [], pendingConfirmations);
  const focusNote = qs(".todayFocusNote");
  if (focusNote) {
    focusNote.innerHTML = `
      <strong>${C.escapeHtml(workflow.stage_label_zh || "下一可售日观察")}</strong>
      ${C.escapeHtml(workflow.headline_zh || "先看 Top 单关，再看每日 2串1 / 3串1 纸面候选；总进球和比分只作节奏/倾向参考。")}
      <br><span>${C.escapeHtml(workflow.combo_policy_zh || "T+1 阶段给候选榜，但不强行升级为最终串联。")}</span>
    `;
  }
  renderTodayOneLook(view);
  renderResearchArchiveStatus(view.research_archive_status || state.latestResearchArchive || {});
  renderWorkflowScore(view, "ready");
  renderScanCalendar(view);
  renderExternalSignalsStrip(view);
  const learningSummary = view.learning_history_summary || view.learning_summary || view.learning_panel?.history_summary || {};
  const proScore = view.professional_model_score || {};
  const proRoadmap = proScore.roadmap_to_95 || {};
  const learningCount = Number(learningSummary.settled_count || learningSummary.sample_count || learningSummary.rows || 0);
  const learningCardValue = learningCount > 0 ? `${learningCount} 条` : "待累计";
  const learningCardHelp = learningSummary.summary_zh || learningSummary.message_zh || "赛后录入赛果和收盘赔率后，用 Brier、Log Loss、ROI 和 CLV 复盘。";
  const windowSummary = view.window_review_summary || view.backtest_window || view.learning_panel?.window_summary || {};
  const windowCardValue = windowSummary.label_zh || windowSummary.status_zh || windowSummary.value || "待复盘";
  const windowCardHelp = windowSummary.summary_zh || windowSummary.message_zh || "区间复盘用于判断最近样本是否稳定，不用单日结果过度外推。";
  const snapshotStatus = view.snapshot_status || view.snapshot_save_status || {};
  const postReview = view.post_match_review_status || {};
  qs("#todayCards").classList.remove("skeletonBlock");
  qs("#todayCards").innerHTML = C.cards([
    { label: "可售比赛", value: `${view.matches_count ?? 0} 场`, help: `${view.selected_date || "自动日期"} · 数据源 ${view.provider_used || "unknown"}` },
    { label: "预观察可信度", value: `${view.credibility_audit?.credibility_score ?? "N/A"}/100`, help: view.credibility_gate?.reason_zh || view.credibility_audit?.reasons?.[0] || "用于判断是否适合组合观察。" },
    { label: "职业模型分", value: proScore.score == null ? "N/A" : `${proScore.score}/${proScore.ceiling_score || 95}`, help: proRoadmap.summary_zh || proScore.summary_zh || "按市场校准、CLV、概率校准、冷门偏差和学习闭环评分。" },
    { label: "情报完整度", value: `${view.intelligence_completeness?.score ?? "N/A"}/100`, help: view.intelligence_completeness?.summary_zh || "伤停、首发、天气、新闻等只做覆盖审计，不编造。" },
    { label: "串联纪律", value: view.credibility_gate?.label_zh || view.credibility_audit?.credibility_gate?.label_zh || "待评估", help: "没有强组合时会显示暂不组合，而不是强行给组合。" },
    { label: "DS研究", value: aiStatusLabel, help: aiStatusSummary },
    { label: "赛前快照", value: snapshotStatus.status_zh || snapshotStatus.status || "待保存", help: snapshotStatus.summary_zh || snapshotStatus.pre_match_path || "T+1 输出会落盘，避免赛后回忆偏差。" },
    { label: "昨日复盘", value: postReview.status_zh || "待复盘", help: postReview.summary_zh || "赛后会对照单关、纸面2串1、纸面3串1和被拒组合。" },
    { label: "赛后学习", value: learningCardValue, help: learningCardHelp },
  ]);
  const homepageCoverageCards = (view.coverage_summary_cards || []).length
    ? view.coverage_summary_cards
    : (view.reliability_summary?.source_cards || view.source_coverage_cards || []).map((row) => ({
      label: row.source || row.label_zh,
      value: row.coverage || row.status || "N/A",
      help: row.message_zh || row.role || "",
    }));
  qs("#todayReliabilityCards").innerHTML = C.cards(homepageCoverageCards.slice(0, 4));
  const homepageCoverageBullets = [
    view.today_focus_summary_zh || "",
    ...((view.critical_gap_list_zh || []).slice(0, 4)),
    ...((view.homepage_missing_actions || []).slice(0, 2)),
  ].filter(Boolean);
  qs("#todaySourceCoverage").innerHTML = homepageCoverageBullets.length
    ? C.list(homepageCoverageBullets)
    : `<div class="sectionHint">今天没有明显情报缺口；更细的逐场覆盖表放在“可信度 / 数据来源”页查看。</div>`;
  const status = view.data_source_status || {};
  const health = view.source_health || {};
  const externalSignals = view.external_signals_status || {};
  qs("#dataSourceStatus").innerHTML = C.list([
    `健康状态：${health.health || status.status || "unknown"}`,
    `可靠性评级：${health.reliability_label_zh || "N/A"}（${health.reliability_score ?? "N/A"}/100）`,
    `说明：${health.message_zh || status.message_zh || "暂无说明"}`,
    `判断建议：${health.decision_guide_zh || "请结合 provider_used、扫描窗口和缺失情报查看。"}`,
    `实际 provider：${health.provider_used || view.provider_used || "unknown"}`,
    `观察阶段：${workflow.stage_label_zh || "下一可售日观察"}`,
    workflow.valid_use_zh || "当前适合做候选筛选和情报缺口整理。",
    `扫描日期：${(health.scanned_dates || []).join("、") || "N/A"}`,
    health.scan_summary_zh || "扫描窗口：N/A",
    `成功次数：${health.successful_attempts ?? 0}/${health.attempt_count ?? 0}`,
    `覆盖审计条目：${(view.coverage_audit_notes || []).length || health.warning_count || 0}`,
    ...(health.source_action_items || []),
    `外部情报：${externalSignals.source_type || "not_provided"}，覆盖 ${externalSignals.matched_count ?? 0}/${externalSignals.matches_count ?? 0} 场`,
    `情报读取状态：${externalSignals.load_status || "not_provided"}，无效条目：${externalSignals.invalid_items ?? 0}`,
    externalSignals.message_zh || "未提供外部情报 JSON。",
    health.recovery_hint_zh || "数据源状态会明确标记，不会把回退数据伪装成 Sporttery。",
    ...((view.coverage_audit_notes || view.coverage_notes || []).slice(0, 4)),
  ]);
  renderTodayTopSections(view);
  const operationEntry = view.operation_entry || {};
  qs("#todayRiskTip").innerHTML = [
    C.list([
      workflow.valid_use_zh || "当前适合做预观察，不适合把组合当作最终结论。",
      workflow.missing_is_expected_zh || "T+1 阶段部分临场信息尚未完整属于正常。",
      view.max_risk_tip || "请先查看数据源状态和缺失情报。",
      operationEntry.summary || "查看模拟走盘可理解历史资金曲线、最大回撤、玩法贡献和为什么赚/亏。",
      operationEntry.disclaimer || "模拟经营不代表未来表现。",
    ]),
    operationEntry.metrics ? `<h4>${C.escapeHtml(operationEntry.title || "回测表现怎么看")}</h4>${C.list(operationEntry.metrics)}` : "",
  ].join("");
  qs("#todayTraderConclusion").innerHTML = C.list([
    workflow.trader_instruction_zh || "先看单关，再看 2串1 是否通过纪律。",
    proScore.summary_zh || "",
    proRoadmap.summary_zh || "",
    ...((proRoadmap.next_best_actions || []).slice(0, 3).map((item) => `95分短板：${item.label_zh || "改进项"}${item.estimated_score_gain ? `（预计 +${item.estimated_score_gain} 分）` : ""}；${item.current_state_zh || item.why_it_matters_zh || ""}`)),
    view.strict_trader_conclusion || view.trader_review?.final_call_zh || "请先刷新今日观察。",
    view.optimizer?.no_combo_reason || view.best_parlay_summary?.no_combo_reason || view.credibility_gate?.reason_zh || "",
    ...(view.trader_review?.conclusions_zh || []),
  ]);
  const pendingHtml = pendingConfirmations.length
    ? C.table(pendingConfirmations, [
      { key: "item", label: "待确认项" },
      { key: "status_zh", label: "状态" },
      { key: "why_zh", label: "为什么重要" },
    ])
    : "";
  const signalStatusHtml = (view.critical_gap_list_zh || []).length
    ? C.list(view.critical_gap_list_zh)
    : C.list((view.missing_signals || []).length ? (view.missing_signals || []).map((item) => `${item}：当前按未知处理。`) : ["当前没有明显缺失情报。"]);
  const gapActionsHtml = (view.homepage_missing_actions || []).length
    ? C.list(view.homepage_missing_actions)
    : `<div class="sectionHint">暂无额外补齐动作；更细的来源、状态和逐场覆盖表，放在“可信度 / 数据来源”页查看。</div>`;
  qs("#todayMissing").innerHTML = [
    pendingHtml ? `<h4>T+1 待确认清单</h4>${pendingHtml}` : "",
    `<h4>${C.escapeHtml(view.coverage_audit_title_zh || "情报覆盖审计")}</h4>`,
    view.intelligence_coverage?.summary_zh ? `<div class="sectionHint">${C.escapeHtml(view.intelligence_coverage.summary_zh)}</div>` : "",
    (view.coverage_audit_notes || []).length ? C.list((view.coverage_audit_notes || []).slice(0, 4)) : "",
    signalStatusHtml,
    `<h4>情报缺口怎么处理</h4><div class="sectionHint">已确认、已检查但未返回、兜底估算、未接入是四种不同状态。系统只会降权，不会编造。更细的逐场覆盖表、来源和状态分层，放在“可信度 / 数据来源”页查看。</div>`,
    gapActionsHtml,
  ].join("");
  renderSignalExplainFromToday(view);
  renderReliabilityFromToday(view);
  renderCredibility(view.credibility_audit || {});
  renderBestParlay(view.best_parlay_summary || {});
  renderTraderReview(view.trader_review || {});
}

function renderMatchdayChecklist(rows, pendingConfirmations = []) {
  const box = qs("#matchdayChecklist");
  if (!box) return;
  const targets = (rows || []).filter((row) => row.matchday_review_zh || row.matchday_keep_min_odds).slice(0, 3);
  const confirmations = pendingConfirmations.length
    ? pendingConfirmations.map((item) => item.item || item.signal || item)
    : ["首发", "伤停", "天气", "终盘赔率", "新闻面"];
  box.innerHTML = `
    <div class="matchdayChecklistHead">
      <span>MATCHDAY CHECK</span>
      <strong>临场复核清单</strong>
      <p>临近开赛前只做一件事：确认赔率还覆盖模型概率，且没有首发、伤停、天气或新闻面的反向变化。</p>
    </div>
    <div class="matchdayConfirmTags">
      ${confirmations.slice(0, 6).map((item) => `<span>${C.escapeHtml(item)}</span>`).join("")}
    </div>
    ${targets.length ? `<div class="matchdayChecklistGrid">${targets.map((row) => `
      <article>
        <strong>${C.escapeHtml(row.match || "观察信号")}</strong>
        <p>${C.escapeHtml(row.play_type || "玩法")} · ${C.escapeHtml(row.direction || "方向")} · 当前赔率 ${C.escapeHtml(row.official_odds || row.odds || "N/A")}</p>
        <div class="checkOddsLine">
          <span>保留观察 ≥ ${C.escapeHtml(row.matchday_keep_min_odds || "N/A")}</span>
          <span>失去覆盖 &lt; ${C.escapeHtml(row.matchday_no_value_below_odds || "N/A")}</span>
          <span>反向漂移 ≥ ${C.escapeHtml(row.matchday_reverse_drift_watch_odds || "N/A")}</span>
        </div>
        <em>${C.escapeHtml(row.next_review_zh || row.matchday_review_zh || "临场复核赔率和情报后再决定是否继续观察。")}</em>
      </article>
    `).join("")}</div>` : `<div class="emptyState">当前没有可生成临场复核阈值的 Top 单关。先看数据源和情报覆盖，再等待临场赔率。</div>`}
  `;
}

function renderSignalCategorySummary(rows) {
  const box = qs("#signalCategorySummary");
  if (!box) return;
  const groups = {
    steady_watch: { title: "稳健观察", desc: "赔率不过高、校准概率更扎实，优先等待情报复核。", rows: [] },
    value_watch: { title: "价值观察", desc: "赔率与模型有差异，但仍要看终盘赔率和情报。", rows: [] },
    longshot_watch: { title: "冷门观察", desc: "赔率高、波动大，只作纸面跟踪，不进串联核心。", rows: [] },
    weak_or_pass: { title: "弱观察/放弃", desc: "优势不足，先不作为核心。", rows: [] },
  };
  (rows || []).forEach((row) => {
    const key = row.signal_category || "weak_or_pass";
    (groups[key] || groups.weak_or_pass).rows.push(row);
  });
  box.innerHTML = `<div class="categoryGrid">${Object.values(groups).map((group) => {
    const top = group.rows[0];
    const sample = top ? `${top.match || ""} ${top.direction || ""}` : "暂无";
    return `<article class="categoryCard">
      <span>${C.escapeHtml(group.title)}</span>
      <strong>${C.escapeHtml(group.rows.length)}</strong>
      <p>${C.escapeHtml(group.desc)}</p>
      <em>${C.escapeHtml(sample)}</em>
    </article>`;
  }).join("")}</div>`;
}

function renderLearningPanel(panel) {
  const box = qs("#learningPanel");
  if (!box) return;
  const cards = C.cards(panel.summary_cards || []);
  const healthCards = C.cards(panel.model_health_cards || []);
  const historyCards = C.cards(panel.history_cards || []);
  const dailyReport = panel.daily_report || {};
  const windowReports = panel.window_reports || [];
  const lessons = C.list(panel.lessons || []);
  const brief = C.list(panel.learning_brief || ["赛后学习会把真实结果反馈到赔率段校准和冷门降权。"]);
  const actions = C.list(panel.model_actions || ["继续累计样本，避免小样本过拟合。"]);
  const oddsLearning = panel.odds_learning || {};
  const learningTodo = panel.learning_todo || {};
  const comboLearning = panel.combo_discipline_learning || {};
  const strategyAdjustments = panel.strategy_adjustments || [];
  const comboLearningRows = comboLearning.status === "tracked" ? [
    { label: "被拒复盘", value: comboLearning.review_count ?? 0, help: "进入赛后学习的被拒组合数量。" },
    { label: "已完整复盘", value: comboLearning.settled_review_count ?? 0, help: "所有腿都匹配到赛果的被拒组合。" },
    { label: "可能过严", value: comboLearning.over_strict_candidate_count ?? 0, help: "被拒但赛后全中的组合，需要复查规则。" },
    { label: "纪律支持", value: comboLearning.discipline_supported_count ?? 0, help: "被拒且赛后未全中的组合。" },
  ] : [];
  const ruleAdjustmentRows = comboLearning.rule_adjustment_summary || [];
  const todoRows = (learningTodo.items || []).map((item) => ({
    label: item.label,
    status: item.status === "done" ? "已完成" : "待补",
    impact_zh: item.impact_zh,
  }));
  const todoHtml = learningTodo.title_zh ? `
    <section class="learningTodoCard">
      <div class="sectionHeading compact">
        <p class="eyebrow">LONG-RUN FIX</p>
        <h4>${C.escapeHtml(learningTodo.title_zh)}</h4>
        <p>${C.escapeHtml(learningTodo.why_it_matters_zh || "赛后学习会让下一次排序更有证据。")}</p>
      </div>
      <div class="scoreMiniGrid">
        <article><span>当前学习分</span><b>${C.escapeHtml(learningTodo.current_score ?? "N/A")}/100</b></article>
        <article><span>下一轮目标</span><b>${C.escapeHtml(learningTodo.target_score_after_next_loop ?? "N/A")}/100</b></article>
        <article><span>已结算样本</span><b>${C.escapeHtml(learningTodo.settled_count ?? 0)}</b></article>
        <article><span>CLV 样本</span><b>${C.escapeHtml(learningTodo.clv_count ?? 0)}</b></article>
      </div>
      <div class="noteBox">${C.escapeHtml(learningTodo.next_action_zh || "先保存观察快照，赛后补比分和收盘赔率。")}</div>
      ${learningTodo.score_persistence_zh ? `<div class="noteBox softNote">${C.escapeHtml(learningTodo.score_persistence_zh)}</div>` : ""}
      ${comboLearning.message_zh ? `<div class="noteBox softNote">${C.escapeHtml(comboLearning.message_zh)}</div>` : ""}
      ${strategyAdjustments.length ? `<h4>下一轮调参建议</h4>${strategyAdjustmentCards(strategyAdjustments)}` : ""}
      ${comboLearningRows.length ? `<div class="contentBox">${C.cards(comboLearningRows)}</div>` : ""}
      ${ruleAdjustmentRows.length ? `
        <h4>可能过严的规则</h4>
        ${tableOrEmpty(ruleAdjustmentRows, [
          { key: "label_zh", label: "规则" },
          { key: "count", label: "出现次数" },
          { key: "suggestion_zh", label: "调整建议" },
        ])}
      ` : ""}
      ${tableOrEmpty(todoRows, [
        { key: "label", label: "要补什么" },
        { key: "status", label: "状态" },
        { key: "impact_zh", label: "为什么有用" },
      ])}
    </section>
  ` : "";
  const oddsRules = C.list(oddsLearning.plain_language_rules || []);
  const parlayRows = (oddsLearning.parlay_examples || []).map((row) => ({
    case_zh: row.case_zh,
    raw_hit_prob: fmtPct(row.raw_hit_prob),
    after_discount_prob: fmtPct(row.after_discount_prob),
    message_zh: row.message_zh,
  }));
  const bucketRows = (oddsLearning.bucket_explanations || []).slice(0, 4).map((row) => ({
    bucket_label_zh: row.bucket_label_zh,
    attempts: row.attempts,
    hits: row.hits,
    bayesian_hit_rate: fmtPct(row.bayesian_hit_rate),
    use_zh: row.use_zh,
  }));
  const rows = panel.rows || [];
  const visibleRows = rows.slice(0, 3).map((row) => ({
    match: row.match,
    direction: row.direction,
    odds: row.odds,
    hit: row.hit === true ? "命中" : row.hit === false ? "未命中" : "未结算",
    category: row.signal_category_zh,
    calibrated_prob: fmtPct(row.calibrated_prob),
    brier_score: fmtNum(row.brier_score),
    log_loss: fmtNum(row.log_loss),
    note: row.calibration?.message_zh || "",
  }));
  box.innerHTML = `
    <details class="learningDrawer" open>
      <summary>模型学习状态：先校准赔率段，再判断能不能串联</summary>
      ${todoHtml}
      ${dailyReport.headline_zh ? `
        <section class="learningDailyReport">
          <div class="sectionHeading compact">
            <p class="eyebrow">DAILY REPORT</p>
            <h4>${C.escapeHtml(dailyReport.headline_zh)}</h4>
            <p>${C.escapeHtml(dailyReport.verdict_zh || "赛后固定复盘输出。")}</p>
          </div>
          <div class="noteBox">${C.list(dailyReport.paragraphs_zh || [])}</div>
          <div class="noteBox softNote">${C.escapeHtml(dailyReport.metrics_line_zh || "命中率 N/A · ROI N/A · Brier N/A · Log Loss N/A · CLV N/A")}</div>
        </section>
      ` : ""}
      ${windowReports.length ? `
        <section class="learningWindowReports">
          <div class="sectionHeading compact">
            <p class="eyebrow">WINDOW REPORTS</p>
            <h4>区间复盘</h4>
            <p>除了单日结果，还要看近 7 天、近 30 天和累计区间。</p>
          </div>
          <div class="signalCardGrid">
            ${windowReports.slice(0, 3).map((report) => `
              <article class="signalCard">
                <div class="signalCardTop">
                  <span>${C.escapeHtml(report.headline_zh || "区间复盘")}</span>
                  <strong>${C.escapeHtml(report.status_zh || "待观察")}</strong>
                </div>
                <p>${C.escapeHtml((report.paragraphs_zh || [])[0] || "")}</p>
                <div class="metricStrip">
                  <span>${C.escapeHtml(report.metrics_line_zh || "命中率 N/A · ROI N/A · Brier N/A · Log Loss N/A")}</span>
                </div>
                <em>${C.escapeHtml(report.next_step_zh || "继续累计样本。")}</em>
              </article>
            `).join("")}
          </div>
        </section>
      ` : ""}
      <h4>模型健康一眼看懂</h4>
      ${healthCards}
      <div class="noteBox">${C.escapeHtml(panel.model_health_zh || "模型仍按保守学习处理。")}</div>
      <div class="learningSplit">
        <div>
          <h4>昨天学到了什么</h4>
          ${cards}
        </div>
        <div>
          <h4>累计学习状态</h4>
          ${historyCards}
        </div>
      </div>
      <h4>当前模型怎么理解这批样本</h4>
      <div class="noteBox">${brief}</div>
      <h4>下一次排序会怎么变</h4>
      <div class="noteBox">${actions}</div>
      <h4>赔率怎么读：给使用者看的版本</h4>
      <div class="noteBox">${oddsRules}</div>
      <div class="learningSplit">
        <div>
          <h4>串联为什么难</h4>
          ${tableOrEmpty(parlayRows, [
            { key: "case_zh", label: "场景" },
            { key: "raw_hit_prob", label: "原始同时命中" },
            { key: "after_discount_prob", label: "折扣后" },
            { key: "message_zh", label: "说明" },
          ], "暂无串联示例。")}
        </div>
        <div>
          <h4>赔率段当前校准</h4>
          ${tableOrEmpty(bucketRows, [
            { key: "bucket_label_zh", label: "赔率段" },
            { key: "attempts", label: "样本" },
            { key: "hits", label: "命中" },
            { key: "bayesian_hit_rate", label: "贝叶斯命中率" },
            { key: "use_zh", label: "模型动作" },
          ], "暂无赔率段样本。")}
        </div>
      </div>
      <h4>昨日观察明细</h4>
      <div class="noteBox">${lessons}</div>
      ${tableOrEmpty(visibleRows, [
        { key: "match", label: "比赛" },
        { key: "direction", label: "方向" },
        { key: "odds", label: "赔率" },
        { key: "hit", label: "结果" },
        { key: "category", label: "类型" },
        { key: "calibrated_prob", label: "校准概率" },
        { key: "brier_score", label: "Brier" },
        { key: "log_loss", label: "Log Loss" },
        { key: "note", label: "学习说明" },
      ], "暂无昨日复盘样本。")}
    </details>
  `;
}

async function loadLearningFeedback() {
  updateLearningFlowStatus();
  const payload = await request("/api/view/learning-feedback", {}, "刷新赛后学习");
  if (payload.ok) renderLearningFeedback(payload.data);
  await loadLearningHistory(false);
  switchView("learning");
}

async function buildLearningFeedbackPreview() {
  updateLearningFlowStatus();
  const payload = await request("/api/view/build-learning-feedback", {
    observations_json: value("#learningObservationsPath", "data/fixtures/observations_20260611_example.json"),
    results_csv: value("#learningResultsPath", "data/fixtures/result_scores_20260611.csv"),
  }, "构建赛后学习反馈");
  if (payload.ok) renderBuiltLearningFeedback(payload.data);
  switchView("learning");
}

async function saveLearningObservationSnapshot() {
  const payload = await request("/api/learning/save-observation-snapshot", {
    provider: providerParam(),
    date: currentDateParam(),
    bankroll: bankrollParam(),
    risk_profile: riskProfileParam(),
  }, "保存今日观察快照");
  if (payload.ok) {
    const saved = payload.data || {};
    const input = qs("#learningObservationsPath");
    if (input && saved.path) input.value = saved.path;
    if (qs("#learningBuildSummary")) {
      qs("#learningBuildSummary").innerHTML = C.list([
        saved.summary_zh || "已保存今日观察快照。",
        `观察项：${saved.observations_count ?? 0} 条。`,
        `保存路径：${saved.path || "data/learning_observations/"}`,
        saved.next_step_zh || "赛后选择赛果 CSV 后保存学习样本。",
      ]);
    }
    updateLearningFlowStatus();
  }
  switchView("learning");
}

async function prepareDailyLearningPack() {
  const payload = await request("/api/learning/prepare-daily-pack", {
    provider: providerParam(),
    date: currentDateParam(),
    bankroll: bankrollParam(),
    risk_profile: riskProfileParam(),
  }, "一键准备学习包");
  if (payload.ok) {
    const pack = payload.data || {};
    state.lastLearningPack = pack;
    const obsInput = qs("#learningObservationsPath");
    const resultsInput = qs("#learningResultsPath");
    const closingInput = qs("#learningClosingOddsPath");
    if (obsInput && pack.observations_path) obsInput.value = pack.observations_path;
    if (resultsInput && pack.results_path) resultsInput.value = pack.results_path;
    if (closingInput && pack.closing_odds_path) closingInput.value = pack.closing_odds_path;
    if (qs("#learningBuildSummary")) {
      qs("#learningBuildSummary").innerHTML = C.list([
        pack.summary_zh || "已准备学习包。",
        `观察项：${pack.observations_count ?? 0} 条；被拒组合复盘：${pack.rejected_combo_count ?? 0} 条；比赛：${pack.matches_count ?? 0} 场；赔率复核项：${pack.closing_rows_count ?? 0} 条。`,
        `观察快照：${pack.observations_path || "N/A"}`,
        `比分模板：${pack.results_path || "N/A"}`,
        `赔率模板：${pack.closing_odds_path || "N/A"}`,
        pack.next_step_zh || "赛后填写模板并保存学习样本。",
      ]);
    }
    updateLearningFlowStatus();
  }
  switchView("learning");
}

async function saveLearningResultTemplate() {
  const payload = await request("/api/learning/save-result-template", {
    observations_json: value("#learningObservationsPath", "data/fixtures/observations_20260611_example.json"),
  }, "生成赛果 CSV 模板");
  if (payload.ok) {
    const saved = payload.data || {};
    const input = qs("#learningResultsPath");
    if (input && saved.path) input.value = saved.path;
    if (qs("#learningBuildSummary")) {
      qs("#learningBuildSummary").innerHTML = C.list([
        saved.summary_zh || "已生成赛果 CSV 模板。",
        `比赛：${saved.matches_count ?? 0} 场。`,
        `保存路径：${saved.path || "data/learning_results/"}`,
        saved.how_to_use_zh || "赛后填写比分后保存学习样本。",
      ]);
    }
    updateLearningFlowStatus();
  }
  switchView("learning");
}

async function saveLearningClosingOddsTemplate() {
  const payload = await request("/api/learning/save-closing-odds-template", {
    observations_json: value("#learningObservationsPath", "data/fixtures/observations_20260611_example.json"),
  }, "生成收盘赔率模板");
  if (payload.ok) {
    const saved = payload.data || {};
    const input = qs("#learningClosingOddsPath");
    if (input && saved.path) input.value = saved.path;
    if (qs("#learningBuildSummary")) {
      qs("#learningBuildSummary").innerHTML = C.list([
        saved.summary_zh || "已生成收盘赔率模板。",
        `观察项：${saved.rows_count ?? 0} 条。`,
        `保存路径：${saved.path || "data/learning_closing_odds/"}`,
        saved.how_to_use_zh || "填写 closing_odds 后复盘 CLV。",
      ]);
    }
    updateLearningFlowStatus();
  }
  switchView("learning");
}

async function reviewLearningClv() {
  updateLearningFlowStatus();
  const payload = await request("/api/view/clv-review", {
    observations_json: value("#learningObservationsPath", "data/fixtures/observations_20260611_example.json"),
    closing_odds: value("#learningClosingOddsPath", ""),
  }, "复盘 CLV");
  if (payload.ok) renderLearningClv(payload.data || {});
  switchView("learning");
}

async function saveLearningClvReview() {
  const payload = await request("/api/learning/save-clv-review", {
    observations_json: value("#learningObservationsPath", "data/fixtures/observations_20260611_example.json"),
    closing_odds: value("#learningClosingOddsPath", ""),
  }, "保存 CLV 复盘样本");
  if (payload.ok) {
    const saved = payload.data || {};
    if (qs("#learningClvSummary")) {
      qs("#learningClvSummary").innerHTML = C.list([
        saved.summary_zh || "已保存 CLV 复盘。",
        `保存路径：${saved.path || "data/learning_clv/"}`,
        saved.privacy_zh || "仅保存在本机。",
      ]);
    }
    renderLearningClv(saved.review || {});
    await loadLearningClvHistory();
  }
  switchView("learning");
}

async function saveDailyLearningResults() {
  updateLearningFlowStatus();
  const payload = await request("/api/learning/save-daily-results", {
    observations_json: value("#learningObservationsPath", "data/fixtures/observations_20260611_example.json"),
    results_csv: value("#learningResultsPath", "data/fixtures/result_scores_20260611.csv"),
    closing_odds: value("#learningClosingOddsPath", ""),
  }, "一键保存赛后学习");
  if (payload.ok) {
    const saved = payload.data || {};
    const feedbackRows = (((saved.feedback || {}).feedback || {}).report || {}).rows || [];
    const clvRows = ((saved.clv || {}).review || {}).rows || [];
    const aiHypothesisReview = ((saved.ai_hypothesis_review || {}).review || {});
    const aiCounts = aiHypothesisReview.summary_counts || {};
    const aiSummary = aiCounts.total
      ? `AI 假设复盘 ${aiCounts.total} 条：支持 ${aiCounts.supported || 0}，失败 ${aiCounts.failed || 0}，待验证 ${aiCounts.needs_more_data || 0}`
      : "AI 假设复盘：暂无可验证假设";
    state.lastLearningImpact = {
      saved: true,
      summary: `赛果样本 ${feedbackRows.length} 条，CLV 复盘 ${clvRows.length} 条，${aiSummary}`,
      detail: saved.summary_zh || "已保存赛后学习。",
      next: clvRows.length
        ? "刷新模型体检后，CLV、样本门槛和 AI 研究质量会重新计算。"
        : "本次未提供收盘赔率；下一步补 CLV，职业模型分上限才更容易打开。",
    };
    if (qs("#learningBuildSummary")) {
      qs("#learningBuildSummary").innerHTML = C.list([
        saved.summary_zh || "已保存赛后学习。",
        `赛果学习：${saved.feedback_path || "N/A"}`,
        saved.clv_path ? `CLV 学习：${saved.clv_path}` : "CLV 学习：未提供收盘赔率 CSV，已跳过。",
        saved.ai_hypothesis_review_path ? `AI 假设复盘：${saved.ai_hypothesis_review_path}` : "AI 假设复盘：暂无可验证假设。",
        aiSummary,
        saved.next_step_zh || "下次打开会自动读取本地样本。",
        "模型体检页已记录本次学习影响；刷新模型体检可查看门槛进度和 AI 研究质量。",
      ]);
    }
    renderBuiltLearningFeedback((saved.feedback || {}).feedback || {});
    if (saved.clv && saved.clv.review) renderLearningClv(saved.clv.review);
    await loadLearningHistory(false);
    await loadLearningClvHistory();
  }
  switchView("learning");
}

function renderLearningClv(view) {
  if (qs("#learningClvSummary")) {
    qs("#learningClvSummary").innerHTML = C.cards([
      { label: "CLV 跟踪", value: view.tracked_count ?? 0, help: "从赛前观察快照读取的可跟踪项。" },
      { label: "已复盘", value: view.settled_count ?? 0, help: "已填写收盘赔率的观察项。" },
      { label: "跑赢收盘", value: view.positive_clv_count ?? 0, help: "赛前赔率高于收盘赔率的项。" },
      { label: "平均 CLV", value: fmtPct(view.average_clv_pct), help: view.summary_zh || "CLV 用于判断是否比市场更早。" },
    ]) + C.list([view.summary_zh || "暂无 CLV 复盘。", view.disclaimer || "CLV 仅用于纸面复盘。"]);
  }
  if (qs("#learningClvRows")) {
    qs("#learningClvRows").innerHTML = tableOrEmpty(view.rows || [], [
      { key: "match", label: "比赛" },
      { key: "play", label: "玩法" },
      { key: "direction", label: "方向" },
      { key: "entry_odds", label: "赛前赔率" },
      { key: "closing_odds", label: "收盘赔率" },
      { key: "label_zh", label: "CLV 判断" },
      { key: "clv_pct", label: "CLV" },
      { key: "message_zh", label: "说明" },
    ], "暂无 CLV 明细。");
  }
}

async function loadLearningClvHistory() {
  const payload = await request("/api/view/clv-history", {}, "刷新累计 CLV");
  if (payload.ok) renderLearningClvHistory(payload.data || {});
}

function renderLearningClvHistory(view) {
  if (qs("#learningClvHistoryCards")) {
    qs("#learningClvHistoryCards").innerHTML = C.cards([
      { label: "CLV 文件", value: view.files_loaded ?? 0, help: "本地保存的 CLV 复盘文件。" },
      { label: "已复盘项", value: view.settled_count ?? 0, help: "已填写收盘赔率的观察项。" },
      { label: "跑赢收盘", value: view.positive_clv_count ?? 0, help: "赛前赔率高于收盘赔率。" },
      { label: "平均 CLV", value: fmtPct(view.average_clv_pct), help: "长期为正才说明价格判断可能有效。" },
    ]);
  }
  if (qs("#learningClvHistoryNotes")) {
    qs("#learningClvHistoryNotes").innerHTML = C.list([
      view.summary_zh || "暂无累计 CLV。",
      view.next_action_zh || "继续累计 CLV 样本。",
      view.disclaimer || "CLV 仅用于纸面复盘。",
    ]);
  }
}

async function saveLearningFeedback() {
  updateLearningFlowStatus();
  const payload = await request("/api/learning/save-feedback", {
    observations_json: value("#learningObservationsPath", "data/fixtures/observations_20260611_example.json"),
    results_csv: value("#learningResultsPath", "data/fixtures/result_scores_20260611.csv"),
  }, "保存赛后学习样本");
  if (payload.ok) {
    const saved = payload.data || {};
    if (qs("#learningBuildSummary")) {
      qs("#learningBuildSummary").innerHTML = C.list([
        saved.summary_zh || "已保存学习样本。",
        `保存路径：${saved.path || "data/learning_feedback/"}`,
        saved.privacy_zh || "仅保存在本机。",
      ]);
    }
    renderBuiltLearningFeedback(saved.feedback || {});
    await loadLearningHistory(false);
  }
  switchView("learning");
}

function updateLearningFlowStatus() {
  const box = qs("#learningFlowStatus");
  if (!box) return;
  const obs = value("#learningObservationsPath", "");
  const results = value("#learningResultsPath", "");
  const closing = value("#learningClosingOddsPath", "");
  const hasSnapshot = Boolean(obs) && !obs.includes("fixtures/observations_");
  const hasResultsTemplate = Boolean(results) && !results.includes("fixtures/result_scores_");
  const hasClosingTemplate = Boolean(closing);
  let next = "先点“保存今日观察”，把今天的 Top 观察固定下来。";
  if (hasSnapshot && !hasResultsTemplate) next = "下一步点“生成比分模板”，赛后只填主客队进球。";
  if (hasSnapshot && hasResultsTemplate && !hasClosingTemplate) next = "可选：点“生成赔率模板”，临场或赛后填写收盘赔率做 CLV 复盘。";
  if (hasSnapshot && hasResultsTemplate && hasClosingTemplate) next = "赛后填好比分和收盘赔率后，先复盘 CLV，再保存学习样本。";
  const pack = state.lastLearningPack || {};
  const packSummary = pack.observations_path ? `
    <div class="flowPackSummary">
      <span>刚刚准备完成</span>
      <strong>${C.escapeHtml(pack.summary_zh || "学习包已生成")}</strong>
      <p>${C.escapeHtml(`观察项 ${pack.observations_count ?? 0} 条，被拒组合复盘 ${pack.rejected_combo_count ?? 0} 条，比赛 ${pack.matches_count ?? 0} 场，赔率复核 ${pack.closing_rows_count ?? 0} 条。`)}</p>
      <small>${C.escapeHtml(`比分模板：${pack.results_path || "N/A"} · 赔率模板：${pack.closing_odds_path || "N/A"}`)}</small>
    </div>
  ` : "";
  box.innerHTML = `
    ${packSummary}
    <div class="flowNext"><span>下一步</span><strong>${C.escapeHtml(next)}</strong></div>
    <div class="flowSteps">
      <span class="${hasSnapshot ? "done" : "todo"}">观察快照</span>
      <span class="${hasResultsTemplate ? "done" : "todo"}">比分模板</span>
      <span class="${hasClosingTemplate ? "done" : "todo"}">赔率模板</span>
      <span class="todo">赛后保存学习</span>
    </div>
  `;
}

function renderLearningQuickForm() {
  const box = qs("#learningQuickRows");
  if (!box) return;
  const sourceRows = learningQuickSourceRows();
  box.innerHTML = `
    <div class="learningQuickGrid">
      ${sourceRows.map((row, index) => `
        <article class="learningQuickRow"
          data-date="${C.escapeHtml(row.date || "")}"
          data-match-id="${C.escapeHtml(row.match_id || "")}"
          data-match-no="${C.escapeHtml(row.match_no || row.match_num || "")}"
          data-match="${C.escapeHtml(row.match || "")}"
          data-home-team="${C.escapeHtml(row.home_team || "")}"
          data-away-team="${C.escapeHtml(row.away_team || "")}"
          data-key="${C.escapeHtml(row.key || "")}"
          data-play-type="${C.escapeHtml(row.play_type || "")}"
          data-direction="${C.escapeHtml(row.direction || "")}"
          data-entry-odds="${C.escapeHtml(row.entry_odds || "")}">
          <div>
            <span>${C.escapeHtml(row.match_num || `观察 ${index + 1}`)}</span>
            <strong>${C.escapeHtml(row.match || "待填写比赛")}</strong>
            <p>${C.escapeHtml(row.note || "赛后填比分；如果有收盘赔率，也一起填，长期用来判断价格是否买早了。")}</p>
          </div>
          <label>主队进球<input data-field="home_goals" inputmode="numeric" placeholder="如 2" aria-label="主队进球"></label>
          <label>客队进球<input data-field="away_goals" inputmode="numeric" placeholder="如 1" aria-label="客队进球"></label>
          <label>收盘赔率<input data-field="closing_odds" inputmode="decimal" placeholder="可选，如 2.12" aria-label="收盘赔率"></label>
        </article>
      `).join("")}
    </div>
    <div class="learningQuickAdvice">
      <strong>下一步怎么用</strong>
      ${C.list([
        "先点“赛前一键准备”生成观察快照、比分模板和赔率模板。",
        "赛后把这里填写的比分同步到比分模板；有收盘赔率时同步到赔率模板。",
        "再点“一键保存赛后学习”，模型会累计命中率、赔率段、CLV 和被拒组合复盘。",
      ])}
    </div>
  `;
  if (qs("#learningBuildSummary")) {
    qs("#learningBuildSummary").innerHTML = C.list([
      "已生成普通模式填写表。",
      "这一步先帮你明确要填哪些信息；保存学习仍会使用本地模板文件，避免误写和数据丢失。",
      "长期目标：把比分、收盘赔率和被拒组合复盘都纳入学习闭环。",
    ]);
  }
  switchView("learning");
}

function learningQuickSourceRows() {
  const today = state.todayView || {};
  const rows = [];
  const pushRow = (row, note) => {
    if (!row || rows.length >= 6) return;
    const match = row.match || row.legs || ((row.home_team || row.away_team) ? `${row.home_team || ""} vs ${row.away_team || ""}` : "");
    const playType = row.play_type || row.type || "";
    const direction = row.direction || row.outcome_label || "";
    rows.push({
      date: row.date || today.selected_date || today.date || "",
      match_id: row.match_id || "",
      match_no: row.match_no || row.match_num || row.number || "",
      match_num: row.match_num || row.match_no || row.match_id || row.number || "",
      match: match || "待填写比赛",
      home_team: row.home_team || "",
      away_team: row.away_team || "",
      key: row.key || [row.match_id || row.match_no || row.match || match, playType, row.outcome_key || direction].map((item) => String(item || "").trim()).join("|"),
      play_type: playType,
      direction,
      entry_odds: row.official_odds || row.odds || row.combo_odds || "",
      note,
    });
  };
  (today.top_singles || []).slice(0, 3).forEach((row) => pushRow(row, "Top 单关观察：赛后重点记录比分和收盘赔率。"));
  (today.top_rejected_2x1 || []).slice(0, 2).forEach((row) => pushRow(row, "被拒 2串1：赛后也要复盘，验证拒绝是否正确。"));
  if (!rows.length) {
    rows.push({
      match_num: "示例",
      match: "主队 vs 客队",
      note: "先刷新今日观察或准备赛后学习包，再按真实比赛填写。",
    });
  }
  return rows;
}

async function saveLearningQuickResults() {
  const rows = Array.from(document.querySelectorAll(".learningQuickRow")).map((el) => {
    const input = (field) => {
      const node = el.querySelector(`[data-field="${field}"]`);
      return node && node.value !== undefined ? String(node.value).trim() : "";
    };
    return {
      date: el.dataset.date || "",
      match_id: el.dataset.matchId || "",
      match_no: el.dataset.matchNo || "",
      match: el.dataset.match || "",
      home_team: el.dataset.homeTeam || "",
      away_team: el.dataset.awayTeam || "",
      key: el.dataset.key || "",
      play_type: el.dataset.playType || "",
      direction: el.dataset.direction || "",
      entry_odds: el.dataset.entryOdds || "",
      home_goals: input("home_goals"),
      away_goals: input("away_goals"),
      closing_odds: input("closing_odds"),
    };
  }).filter((row) => row.home_goals !== "" && row.away_goals !== "");
  if (!rows.length) {
    if (qs("#learningBuildSummary")) {
      qs("#learningBuildSummary").innerHTML = C.list([
        "还没有可保存的比分。",
        "请至少填写一场比赛的主队进球和客队进球；收盘赔率可以先留空。",
      ]);
    }
    switchView("learning");
    return;
  }
  const payload = await postRequest("/api/learning/save-quick-results", {
    observations_json: value("#learningObservationsPath", "data/fixtures/observations_20260611_example.json"),
    rows,
  }, "保存快速赛后学习");
  if (payload.ok) {
    const saved = payload.data || {};
    const resultsSaved = Number(saved.quick_results_saved || 0);
    const closingSaved = Number(saved.quick_closing_saved || 0);
    state.lastLearningImpact = {
      saved: true,
      score_after: closingSaved > 0 ? 78 : 72,
      detail: `刚保存比分 ${resultsSaved} 场，收盘赔率 ${closingSaved} 项`,
      summary: `比分 ${resultsSaved} 场，收盘赔率 ${closingSaved} 项`,
      next: closingSaved > 0 ? "继续累计 CLV，观察长期是否跑赢收盘赔率。" : "下一次补收盘赔率，才能判断 CLV 价格质量。",
    };
    if (qs("#learningBuildSummary")) {
      qs("#learningBuildSummary").innerHTML = C.list([
        saved.summary_zh || "已保存快速赛后学习。",
        `比分文件：${saved.quick_results_path || "N/A"}`,
        saved.quick_closing_odds_path ? `收盘赔率文件：${saved.quick_closing_odds_path}` : "收盘赔率：未填写，已跳过 CLV。",
        saved.next_step_zh || "下次刷新累计学习时会读取这些样本。",
      ]);
    }
    loadLearningHistory(false);
    loadClvHistory(false);
    if (state.todayView) renderWorkflowScore(state.todayView, "ready");
  }
  switchView("learning");
}

function renderBuiltLearningFeedback(payload) {
  const report = payload.report || {};
  const summary = payload.builder_summary || {};
  const view = {
    status: "built",
    report,
    summary_cards: [
      { label: "观察加载", value: summary.observations_loaded ?? 0, help: "赛前观察 JSON 中读取到的观察项。" },
      { label: "已匹配", value: summary.matched_observations ?? 0, help: "成功匹配到赛果的观察项。" },
      { label: "未匹配", value: summary.unmatched_observations ?? 0, help: "不会强行归因到错误比赛。" },
      { label: "命中率", value: fmtPct(report.hit_rate), help: "只统计已匹配且可结算的观察。" },
    ],
    rows: report.rows || [],
    lessons: [summary.message_zh || "已构建赛后学习反馈。", report.main_lesson_zh || "", report.next_model_action_zh || ""].filter(Boolean),
  };
  if (qs("#learningBuildSummary")) {
    qs("#learningBuildSummary").innerHTML = C.list([
      summary.message_zh || "已构建赛后学习反馈。",
      `赛果 ${summary.results_loaded ?? 0} 场，观察 ${summary.observations_loaded ?? 0} 条，匹配 ${summary.matched_observations ?? 0} 条。`,
      payload.unmatched_observations?.length ? `未匹配观察：${payload.unmatched_observations.length} 条。` : "全部可匹配观察已进入复盘。",
    ]);
  }
  renderLearningFeedback(view);
  loadLearningHistory(false);
}

function renderLearningFeedback(view) {
  state.learningView = view;
  const report = view.report || {};
  qs("#learningCards").innerHTML = C.cards(view.summary_cards || []);
  qs("#learningLessons").innerHTML = C.list(view.lessons || [report.main_lesson_zh || "继续累计赛果样本。"]);
  qs("#learningBuckets").innerHTML = tableOrEmpty(report.bucket_rows || [], [
    { key: "bucket", label: "赔率段" },
    { key: "bucket_label_zh", label: "类型" },
    { key: "attempts", label: "观察数" },
    { key: "hits", label: "命中" },
    { key: "raw_hit_rate", label: "原始命中率" },
    { key: "bayesian_hit_rate", label: "贝叶斯命中率" },
    { key: "message_zh", label: "说明" },
  ], "暂无赔率段样本。");
  if (qs("#learningPlayTypes")) {
    qs("#learningPlayTypes").innerHTML = tableOrEmpty((report.play_type_rows || []).map(learningPlayTypeRow), learningPlayTypeColumns(), "暂无玩法历史样本。");
  }
  if (qs("#learningCalibrationBins")) {
    qs("#learningCalibrationBins").innerHTML = tableOrEmpty((report.calibration_bins || []).map(calibrationBinRow), calibrationBinColumns(), "暂无概率校准分桶。");
  }
  const rows = (report.rows || []).map((row) => ({
    match: row.match,
    play_type: row.play_type,
    direction: row.direction,
    odds: row.odds,
    model_prob: fmtPct(row.model_prob),
    calibrated_prob: fmtPct(row.calibrated_prob),
    brier_score: fmtNum(row.brier_score),
    log_loss: fmtNum(row.log_loss),
    hit: row.hit === true ? "命中" : row.hit === false ? "未命中" : "未结算",
    category: row.signal_category_zh,
    action: row.recommended_use_zh,
  }));
  qs("#learningRows").innerHTML = tableOrEmpty(rows, [
    { key: "match", label: "比赛" },
    { key: "play_type", label: "玩法" },
    { key: "direction", label: "方向" },
    { key: "odds", label: "赔率" },
    { key: "model_prob", label: "原模型概率" },
    { key: "calibrated_prob", label: "校准概率" },
    { key: "brier_score", label: "Brier" },
    { key: "log_loss", label: "Log Loss" },
    { key: "hit", label: "赛果" },
    { key: "category", label: "分类" },
    { key: "action", label: "模型动作" },
  ], "暂无观察项复盘。");
}

async function loadLearningHistory(shouldSwitch = true) {
  const payload = await request("/api/view/learning-history", {}, "刷新累计学习");
  if (payload.ok) renderLearningHistory(payload.data);
  await loadLearningClvHistory();
  if (shouldSwitch) switchView("learning");
}

function renderLearningHistory(view) {
  state.learningHistoryView = view;
  if (!qs("#learningHistoryCards")) return;
  const latestDaily = (view.daily_metrics || [])[0] || {};
  const allTime = (view.window_metrics || []).find((row) => row.window === "all_time") || {};
  qs("#learningHistoryCards").innerHTML = C.cards([
    { label: "学习文件", value: view.files_loaded ?? 0, help: "包含 fixture 和 data/learning_feedback 下的 JSON。" },
    { label: "已结算观察", value: view.settled_count ?? 0, help: "可用于累计命中率的观察项。" },
    { label: "累计命中率", value: fmtPct(view.hit_rate), help: "样本少时只做保守校准。" },
    { label: "累计 Brier", value: fmtNum(view.brier_score), help: view.probability_quality?.message_zh || "越低越好，评估概率校准。" },
    { label: "累计 Log Loss", value: fmtNum(view.log_loss), help: "越低越好，对过度自信惩罚更重。" },
    { label: "最新单日 ROI", value: fmtPct(latestDaily.paper_roi), help: latestDaily.message_zh || "按最近一个赛后学习日聚合。" },
    { label: "累计 CLV", value: fmtSignedPct(allTime.average_clv_pct), help: view.clv_history_summary?.summary_zh || "收盘赔率样本越多越可靠。" },
    { label: "错误文件", value: (view.errors || []).length, help: "读取失败的反馈文件数量。" },
  ]);
  qs("#learningHistoryLessons").innerHTML = C.list([
    ...(view.lessons || []),
    latestDaily.date ? `最新赛后日 ${latestDaily.date}：ROI ${fmtPct(latestDaily.paper_roi)}，Brier ${fmtNum(latestDaily.brier_score)}，Log Loss ${fmtNum(latestDaily.log_loss)}。` : "",
    allTime.window ? `累计窗口：ROI ${fmtPct(allTime.paper_roi)}，CLV ${fmtSignedPct(allTime.average_clv_pct)}。` : "",
    ...(view.next_actions_zh || []),
  ].filter(Boolean));
  if (qs("#learningStrategyAdjustments")) {
    qs("#learningStrategyAdjustments").innerHTML = strategyAdjustmentCards(view.strategy_adjustments || []);
  }
  if (qs("#learningCalibrationBins")) {
    qs("#learningCalibrationBins").innerHTML = tableOrEmpty((view.calibration_bins || []).map(calibrationBinRow), calibrationBinColumns(), "暂无累计概率校准分桶。");
  }
  qs("#learningBuckets").innerHTML = tableOrEmpty(view.bucket_rows || [], [
    { key: "bucket", label: "赔率段" },
    { key: "bucket_label_zh", label: "类型" },
    { key: "attempts", label: "观察数" },
    { key: "hits", label: "命中" },
    { key: "raw_hit_rate", label: "原始命中率" },
    { key: "bayesian_hit_rate", label: "贝叶斯命中率" },
    { key: "message_zh", label: "说明" },
  ], "暂无累计赔率段样本。");
  qs("#learningCategories").innerHTML = tableOrEmpty(view.category_rows || [], [
    { key: "label_zh", label: "信号类型" },
    { key: "attempts", label: "观察数" },
    { key: "hits", label: "命中" },
    { key: "hit_rate", label: "命中率" },
    { key: "message_zh", label: "说明" },
  ], "暂无信号类型样本。");
  if (qs("#learningPlayTypes")) {
    qs("#learningPlayTypes").innerHTML = tableOrEmpty((view.play_type_rows || []).map(learningPlayTypeRow), learningPlayTypeColumns(), "暂无玩法历史样本。");
  }
}

function strategyAdjustmentCards(rows = []) {
  if (!rows.length) return `<div class="emptyState">暂无可执行调参建议。先累计赛后结果和收盘赔率。</div>`;
  return `
    <div class="strategyAdjustmentGrid">
      ${rows.slice(0, 6).map((row) => `
        <article>
          <header>
            <span>${C.escapeHtml(row.action || "adjust")}</span>
            <b>${C.escapeHtml(String(row.priority ?? "N/A"))}</b>
          </header>
          <strong>${C.escapeHtml(row.label_zh || "调参建议")}</strong>
          <p>${C.escapeHtml(row.reason_zh || "继续累计样本。")}</p>
          <em>${C.escapeHtml(row.expected_effect_zh || row.apply_mode_zh || "轻量影响下一次排序。")}</em>
        </article>
      `).join("")}
    </div>
  `;
}

function calibrationBinRow(row) {
  return {
    probability_bin: row.probability_bin,
    attempts: row.attempts,
    hits: row.hits,
    avg_predicted_prob: fmtPct(row.avg_predicted_prob),
    observed_hit_rate: fmtPct(row.observed_hit_rate),
    calibration_gap: fmtSignedPct(row.calibration_gap),
    message_zh: row.message_zh,
  };
}

function learningPlayTypeRow(row) {
  return {
    label_zh: row.label_zh || row.play_type || "未知玩法",
    attempts: row.attempts ?? 0,
    hits: row.hits ?? 0,
    hit_rate: fmtPct(row.hit_rate),
    paper_roi: fmtSignedPct(row.paper_roi),
    brier_score: fmtNum(row.brier_score),
    log_loss: fmtNum(row.log_loss),
    sample_quality_zh: row.sample_quality_zh || "样本未知",
    model_action_zh: row.model_action_zh || row.message_zh || "继续累计样本。",
  };
}

function learningPlayTypeColumns() {
  return [
    { key: "label_zh", label: "玩法" },
    { key: "attempts", label: "样本" },
    { key: "hits", label: "命中" },
    { key: "hit_rate", label: "命中率" },
    { key: "paper_roi", label: "纸面 ROI" },
    { key: "brier_score", label: "Brier" },
    { key: "log_loss", label: "Log Loss" },
    { key: "sample_quality_zh", label: "样本质量" },
    { key: "model_action_zh", label: "模型动作" },
  ];
}

function calibrationBinColumns() {
  return [
    { key: "probability_bin", label: "预测概率段" },
    { key: "attempts", label: "样本" },
    { key: "hits", label: "命中" },
    { key: "avg_predicted_prob", label: "平均预测" },
    { key: "observed_hit_rate", label: "实际命中" },
    { key: "calibration_gap", label: "校准差" },
    { key: "message_zh", label: "说明" },
  ];
}

async function loadCredibility() {
  const payload = await request("/api/audit/credibility", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), risk_profile: riskProfileParam() }, "刷新可信度复核");
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
  qs("#missingInfoTable").innerHTML = renderMissingInfoFieldCards(view.fields || []);
}

function renderMissingInfoFieldCards(fields = []) {
  if (!fields.length) return `<div class="emptyState"><strong>暂无情报覆盖记录</strong><p>请先读取比赛或刷新情报覆盖。</p></div>`;
  const priority = ["伤停", "首发", "天气", "比赛城市", "新闻面", "旅行", "战意", "中立场", "赛事重要性"];
  const sorted = [...fields].sort((a, b) => priority.indexOf(a.label_zh) - priority.indexOf(b.label_zh));
  const cards = sorted.map((item) => {
    const status = item.status_zh || "未知";
    const level = /已确认|用户补充/.test(status) ? "ok" : /已检查|兜底/.test(status) ? "watch" : "missing";
    const canSupply = item.user_can_supply ? "可补" : "系统处理";
    return `
      <article class="missingInfoFieldCard ${level}">
        <div><span>${C.escapeHtml(status)}</span><b>${C.escapeHtml(canSupply)}</b></div>
        <strong>${C.escapeHtml(item.label_zh || "情报")}</strong>
        <p>${C.escapeHtml(item.message_zh || "当前按未知处理，不编造。")}</p>
        <em>${C.escapeHtml(item.supply_hint_zh || "暂无补齐动作。")}</em>
      </article>
    `;
  }).join("");
  const tableRows = sorted.map((item) => ({
    ...item,
    user_can_supply: item.user_can_supply ? "是" : "否",
  }));
  return `
    <div class="missingInfoFieldGrid">${cards}</div>
    <details class="detailDrawer"><summary>查看完整字段明细</summary>${C.table(tableRows, [
      { key: "label_zh", label: "情报" },
      { key: "status_zh", label: "状态" },
      { key: "impact_zh", label: "影响" },
      { key: "user_can_supply", label: "可补齐" },
      { key: "supply_hint_zh", label: "如何补齐" },
      { key: "message_zh", label: "说明" },
    ])}</details>
  `;
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

async function loadBestParlay(options = {}) {
  const payload = await request("/api/view/best-parlay", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), bankroll: bankrollParam(), risk_profile: riskProfileParam(), refresh: "1" }, "刷新优秀串联");
  if (payload.ok) renderBestParlay(payload.data);
  if (!options.stayOnCurrentView) switchView("bestparlay");
}
function renderBestParlay(view) {
  state.bestParlayView = view;
  if (!qs("#bestParlayCards")) return;
  qs("#bestParlayCards").innerHTML = bestParlayAnalysisDeck(view);
  const rows = [
    rowCandidate("每日单关", view.daily_single_candidate || view.best_single),
    rowCandidate("每日2串1", view.daily_2x1_candidate || view.best_2x1),
    rowCandidate("每日3串1", view.daily_3x1_candidate || view.best_3x1_if_allowed),
    rowCandidate("最稳组合", view.safest_combo),
    rowCandidate("最高EV组合", view.highest_ev_combo),
    rowCandidate("风险调整最佳", view.best_risk_adjusted_combo),
  ];
  const usefulRows = rows.filter((row) => row && row.status && row.status !== "empty" && row.status !== "no_combo" && row.candidate !== "当前没有可排序候选。" && row.candidate !== "暂无" && row.odds !== "N/A");
  const rejectedRows = (view.rejected_combos || []).slice(0, 10).map((item) => rowCandidate(item.label_zh || item.type || "被拒", item));
  qs("#bestParlayTable").innerHTML = usefulRows.length
    ? C.table(usefulRows, bestParlayColumns())
    : emptyBestParlayState(view);
  qs("#bestParlayRejected").innerHTML = rejectedRows.length
    ? C.table(rejectedRows, bestParlayColumns())
    : `<div class="emptyState"><strong>暂无未升级候选明细</strong><p>当前轻量预筛没有运行完整组合池。进入赛前优化后，若有候选暂未升级，会在这里展示具体分析原因。</p></div>`;
  qs("#bestParlayConclusion").innerHTML = `
    ${comboDisciplineCoach(view)}
    ${C.list([view.conclusion_zh || "暂无结论。", view.risk_note_zh || "串关会放大风险。"])}
  `;
}


function emptyBestParlayState(view = {}) {
  const reason = view.conclusion_zh || view.no_combo_reason || "当前没有通过纪律门控的组合。";
  const note = view.risk_note_zh || "组合必须同时命中，缺少完整概率、情报和单腿质量时，不应强行拼接。";
  return `
    <section class="emptyBestParlayPanel">
      <span>PAPER CANDIDATE</span>
      <strong>候选未升级，但保留实操观察</strong>
      <p>${C.escapeHtml(reason)}</p>
      <div class="emptyBestParlaySteps">
        <article><b>1</b><strong>先跑赛前优化</strong><p>生成完整单关、2串1、3串1 候选池。</p></article>
        <article><b>2</b><strong>再看未升级原因</strong><p>重点看模型概率是否覆盖赔率、相关性、冷门腿和情报缺口。</p></article>
        <article><b>3</b><strong>最后赛日复核</strong><p>首发、伤停、天气和终盘赔率转差时降级。</p></article>
      </div>
      <em>${C.escapeHtml(note)}</em>
      <div class="emptyBestParlayActions">
        <button type="button" class="primary" data-jump-view="optimizer">去赛前优化生成候选池</button>
        <button type="button" class="secondary" data-jump-view="missinginfo">先看情报覆盖</button>
      </div>
    </section>
  `;
}

function bestParlayAnalysisDeck(view = {}) {
  const rejected = Array.isArray(view.rejected_combos) ? view.rejected_combos : [];
  const single = displayCandidate(view.daily_single_candidate || view.best_single, rejected, "single");
  const parlay2 = displayCandidate(view.daily_2x1_candidate || view.best_2x1, rejected, "2");
  const parlay3 = displayCandidate(view.daily_3x1_candidate || view.best_3x1_if_allowed, rejected, "3");
  const adjusted = displayCandidate(view.best_risk_adjusted_combo || view.daily_2x1_candidate || view.highest_ev_combo || view.safest_combo, rejected, "risk");
  const hasAny = [single, parlay2, parlay3, adjusted].some((item) => item && item.hasData);
  const headline = hasAny ? "先看机会面，再看纪律过滤" : "暂无完整候选，先生成分析池";
  const body = hasAny
    ? "这里保留分析能力：赔率、模型概率、市场概率、EV、Edge 和可信度都会先展示；纪律结论只决定是否升级为组合观察。"
    : "当前轻量结果没有完整候选字段。先生成今日观察，系统会生成单关、2串1、3串1、比分和总进球候选池。";
  return `
    <section class="bestParlayAnalysisDeck">
      <article class="analysisLeadCard">
        <span>ANALYSIS FIRST</span>
        <strong>${C.escapeHtml(headline)}</strong>
        <p>${C.escapeHtml(body)}</p>
        <div class="analysisPillRow">
          <em>赔率价值</em><em>模型概率</em><em>市场概率</em><em>EV / Edge</em><em>可信度</em>
        </div>
      </article>
      <div class="analysisCandidateGrid">
        ${analysisCandidateCard("最佳单关", single, "single")}
        ${analysisCandidateCard("2串1候选", parlay2, "combo")}
        ${analysisCandidateCard("3串1候选", parlay3, "combo")}
        ${analysisCandidateCard("风险调整候选", adjusted, "balanced")}
      </div>
    </section>
  `;
}

function displayCandidate(primary = {}, rejectedRows = [], target = "") {
  if (candidateHasData(primary)) return { ...primary, hasData: true };
  const targetText = String(target || "").toLowerCase();
  const fallback = rejectedRows.find((row) => {
    const text = `${row.type || ""} ${row.label_zh || ""} ${row.category || ""} ${row.legs || ""}`.toLowerCase();
    if (targetText === "2") return text.includes("2") || text.includes("2x1");
    if (targetText === "3") return text.includes("3") || text.includes("3x1");
    if (targetText === "single") return text.includes("single") || text.includes("单关");
    return candidateHasData(row);
  });
  return fallback && candidateHasData(fallback)
    ? { ...fallback, hasData: true, fallback_candidate: true }
    : { status: "empty", message_zh: "暂无完整候选", hasData: false };
}

function candidateHasData(item = {}) {
  if (!item || item.status === "empty") return false;
  const status = String(item.status || "").toLowerCase();
  const hasNumericOdds = Number.isFinite(Number(item.odds || item.official_odds));
  const hasCandidateTarget = Boolean(item.legs || item.match || item.direction);
  if ((status === "no_combo" || status.includes("no_combo")) && !hasNumericOdds && !hasCandidateTarget) return false;
  return Boolean(hasCandidateTarget || hasNumericOdds || (item.message_zh && item.status !== "no_combo"));
}

function analysisCandidateCard(title, item = {}, kind = "single") {
  const hasData = item && item.hasData;
  const status = hasData ? candidateDisplayStatus(item) : "待生成";
  const candidate = hasData ? (item.legs || item.match || item.message_zh || "候选方向") : "先生成今日观察";
  const reason = hasData
    ? (item.selected_reason_zh || item.reject_reason || item.discipline_summary_zh || item.reason_zh || "已进入候选分析，继续看赔率覆盖和可信度。")
    : "当前没有完整概率字段，不代表没有机会；需要先生成完整候选池。";
  const next = hasData ? candidateNextStep(item) : "点击“生成今日观察”或进入“赛前优化”。";
  return `
    <article class="analysisCandidateCard kind-${C.escapeHtml(kind)} ${hasData ? "" : "isEmpty"}">
      <div class="analysisCandidateTop">
        <span>${C.escapeHtml(title)}</span>
        <b>${C.escapeHtml(status)}</b>
      </div>
      <strong>${C.escapeHtml(candidate)}</strong>
      <div class="analysisMetricGrid">
        ${analysisMetric("赔率", fmtMaybeNum(item.odds ?? item.official_odds))}
        ${analysisMetric("模型概率", fmtSmartPct(item.model_prob ?? item.fused_prob ?? item.probability))}
        ${analysisMetric("市场概率", fmtSmartPct(item.market_prob ?? item.market_probability))}
        ${analysisMetric("EV", fmtSignedSmartPct(item.ev))}
        ${analysisMetric("Edge", fmtSignedSmartPct(item.edge))}
        ${analysisMetric("可信度", fmtSmartPct(item.confidence_score ?? item.confidence))}
      </div>
      <p class="analysisReason">${C.escapeHtml(reason)}</p>
      <em>${C.escapeHtml(next)}</em>
    </article>
  `;
}

function analysisMetric(label, value) {
  return `<div><span>${C.escapeHtml(label)}</span><b>${C.escapeHtml(value || "待计算")}</b></div>`;
}


function normalizeComboStatusValue(value) {
  const text = String(value || "").toLowerCase();
  return text
    .replace(/未入选/g, "未通过门控")
    .replace(/已入选/g, "通过门控")
    .replace(/入选/g, "通过门控");
}

function isComboSelected(item = {}) {
  const status = normalizeComboStatusValue(item.status || item.final_status || item.selection_status || item.combo_status || "");
  if (["通过门控", "selected", "pass", "selected_after_gate"].some((k) => status.includes(k))) return true;
  return false;
}

function isComboRejected(item = {}) {
  const status = normalizeComboStatusValue(item.status || item.final_status || item.combo_status || item.selection_status || "");
  if (["未过门控", "未通过门控", "拒", "rejected", "closed", "no_combo", "暂不组合", "blocked", "blocked_by_risk", "watchlist", "daily_candidate", "paper_candidate"].some((k) => status.includes(k))) return true;
  return false;
}

function comboStatusLabel(item = {}) {
  const status = normalizeComboStatusValue(item.status || item.final_status || item.combo_status || item.selection_status || "");
  if (isComboSelected(item)) return "可进入观察";
  if (isComboRejected(item)) return "候选存在，暂未升级";
  if (item.daily_candidate || item.final_status === "daily_candidate") return "纸面候选";
  return item.combo_decision_label_zh || item.decision_reason_zh || item.decision_reason_zh || "待复核";
}

function candidateDisplayStatus(item = {}) {
  const raw = normalizeComboStatusValue(item.status || item.combo_decision_label_zh || item.final_status || "");
  if (/通过门控|selected|selected_after_gate/.test(raw)) return "可进入观察";
  if (/拒|未通过门控|未过门控|rejected|closed|no_combo|候选待复核|待复核/.test(raw)) return "候选存在，暂未升级";
  if (item.fallback_candidate) return "候选榜待复核";
  return raw || "分析候选";
}

function candidateNextStep(item = {}) {
  const odds = Number(item.odds || item.official_odds || 0);
  if (Number.isFinite(odds) && odds >= 6) return "这是高赔率冷门，先独立观察，不作为组合核心。";
  const reason = `${item.reject_reason || ""} ${item.discipline_summary_zh || ""}`;
  if (/情报|首发|伤停|天气|新闻/.test(reason)) return "补齐临场情报后再评估是否升级。";
  if (/相关性|折扣/.test(reason)) return "优先换成相关性更低的比赛腿。";
  if (/EV|Edge|优势/.test(reason)) return "优势偏薄时先留在候选榜，不急着升级。";
  return "继续核对赔率、概率和赛后学习表现。";
}

function comboDisciplineCoach(view) {
  const rejected = view.rejected_combos || [];
  const rejectedReasons = rejected.map((item) => `${item.reject_reason || ""} ${item.discipline_summary_zh || ""}`).join(" ");
  const hasConfidenceIssue = /可信度|情报|首发|伤停|天气|新闻/.test(rejectedReasons);
  const hasCorrelationIssue = /相关性|折扣/.test(rejectedReasons);
  const hasLongshotIssue = /冷门|高赔率|very_high|风险/.test(rejectedReasons);
  const actions = [
    hasConfidenceIssue
      ? "补齐首发、伤停、天气、新闻和战意后再评估；可信度不足时不把候选升级成组合。"
      : "继续保持情报覆盖，重点复核临场首发和终盘赔率。",
    hasCorrelationIssue
      ? "优先选择不同比赛、不同风险来源的腿，避免把相似不确定性叠在一起。"
      : "若组合腿相关性较低，再看组合概率是否覆盖组合赔率。",
    hasLongshotIssue
      ? "高赔率冷门只能做单独观察，默认不作为串联核心腿。"
      : "赔率不高不低的中风险腿，更适合进入风险调整比较。",
    "赛后把被拒组合也纳入学习包，观察长期是否真的被纪律过滤掉了亏损来源。",
  ];
  return `
    <section class="comboDisciplineCoach">
      <div>
        <span>COMBO DISCIPLINE</span>
        <strong>组合纪律怎么提分</strong>
        <p>目标不是每天硬凑串联，而是让每一腿先过可信度、赔率覆盖、相关性和回撤纪律。</p>
      </div>
      ${C.list(actions)}
    </section>
  `;
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
function fmtMaybeNum(value) { const n = Number(value); return Number.isFinite(n) ? n.toFixed(n >= 10 ? 1 : 2) : "待计算"; }
function fmtSmartPct(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "待计算";
  return `${(Math.abs(n) > 1 ? n : n * 100).toFixed(1)}%`;
}
function fmtSignedSmartPct(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "待计算";
  const pct = Math.abs(n) > 1 ? n : n * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
}

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
    { key: "injuries", label: "伤停" },
    { key: "lineup", label: "首发" },
    { key: "weather", label: "天气" },
    { key: "news", label: "新闻" },
    { key: "message_zh", label: "说明" },
  ]);
  qs("#reliabilityGuide").innerHTML = C.list([
    view.reliability_summary?.decision_guide_zh || "先看 Sporttery 主数据，再看第三方匹配和缺失情报。",
    "已检查但未返回，不等于确认没有该信息；兜底估算也不等于现场真值。",
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
        <label>DeepSeek Pro key<input id="deepSeekKeyInput" type="password" autocomplete="off" placeholder="粘贴后 auto 模式会自动调用 DS Pro 研究层"></label>
      </div>
      <div class="inlineActions">
        <button type="button" id="saveLocalSecretsBtn" class="secondary">保存到本机配置</button>
        <button type="button" id="verifyApiFootballBtn" class="ghost">验证 API-Football</button>
        <button type="button" id="verifyTheOddsBtn" class="ghost">验证 The Odds API</button>
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
  const deepSeekKey = value("#deepSeekKeyInput") || value("#deepSeekKeyInputTop");
  const body = {
    JC_EDGE_API_FOOTBALL_KEY: value("#apiFootballKeyInput"),
    JC_EDGE_THE_ODDS_API_KEY: value("#theOddsKeyInput"),
    JC_EDGE_DEEPSEEK_API_KEY: deepSeekKey,
    JC_EDGE_DEEPSEEK_ENABLED: deepSeekKey ? "true" : "",
    JC_EDGE_LLM_PROVIDER: deepSeekKey ? "deepseek" : "",
    JC_EDGE_DEEPSEEK_MODEL: deepSeekKey ? "deepseek-v4-pro" : "",
    JC_EDGE_DEEPSEEK_MAX_INPUT_TOKENS: deepSeekKey ? "24000" : "",
    JC_EDGE_DEEPSEEK_MAX_OUTPUT_TOKENS: deepSeekKey ? "4000" : "",
  };
  const payload = await postJson("/api/config/local-env", body, "保存本地 key");
  if (payload.ok) {
    if (deepSeekKey) {
      setStatus("OK", "DeepSeek Pro 已保存，auto DS 研究已启用");
      setAiAutoStatus("running", "DeepSeek Pro 已保存，正在自动接管", "系统会自动刷新 T+1 可售比赛、重跑本地组合纪律，并在 DS Pro ready 时生成研究摘要。");
    }
    if (qs("#apiFootballKeyInput")) qs("#apiFootballKeyInput").value = "";
    if (qs("#theOddsKeyInput")) qs("#theOddsKeyInput").value = "";
    if (qs("#deepSeekKeyInput")) qs("#deepSeekKeyInput").value = "";
    if (qs("#deepSeekKeyInputTop")) qs("#deepSeekKeyInputTop").value = "";
    if (qs("#explainMode") && deepSeekKey) qs("#explainMode").value = "auto";
    state.autoAiResearchKey = "";
    await refreshDataSourcesOnly();
    await loadLlmStatus();
    if (deepSeekKey) {
      if (state.todayView) maybeAutoRunAiResearch(state.todayView);
      else window.setTimeout(() => loadToday(), 250);
    }
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

async function runOptimizerWithProgress(compareProfiles = true, options = {}) {
  startTodayOptimizerInlineProgress();
  let failed = false;
  try {
    return await runOptimizer(compareProfiles, options);
  } catch (error) {
    failed = true;
    abortTodayOptimizerInlineProgress("运行异常，已回退当前页可读状态");
    throw error;
  } finally {
    if (failed) return;
    stopTodayOptimizerInlineProgress("完成");
  }
}

async function runOptimizer(compareProfiles = true, options = {}) {
  const stayOnCurrentView = Boolean(options.stayOnCurrentView);
  renderOptimizerLoadingState(compareProfiles);
  if (!stayOnCurrentView) switchView("optimizer");
  let settled = false;
  const watchdog = window.setTimeout(() => {
    if (settled) return;
    renderOptimizerSlowState("完整模型运行超过等待时间。先显示每日候选入口和最近结果；接口回来后会自动替换。");
  }, 18000);
  const payload = await request("/api/view/optimizer", {
    provider: providerParam(), date: state.todayView?.selected_date || currentDateParam(), bankroll: bankrollParam(), risk_profile: riskProfileParam(), show_rejected: "1", compare_profiles: compareProfiles ? "1" : "0", run_ai: "0", refresh: "1",
  }, compareProfiles ? "对比风险档位" : "生成今日观察", 36000);
  settled = true;
  window.clearTimeout(watchdog);
  stopOptimizerProgressTicker();
  if (payload.ok) {
    try {
      renderOptimizer(payload.data);
      if (state.todayView) renderToday(state.todayView);
    } catch (error) {
      renderOptimizerSlowState(`赛前优化渲染遇到问题：${error && error.message ? error.message : "未知错误"}`);
    }
  } else {
    renderOptimizerSlowState(payload.error?.message || "赛前优化暂未返回结果。");
  }
  if (!stayOnCurrentView) switchView("optimizer");
}

function renderOptimizerLoadingState(compareProfiles = true) {
  const title = compareProfiles ? "正在对比风险档位" : "正在生成观察候选池";
  const body = compareProfiles
    ? "系统会比较保守、均衡、进取三个档位，并检查单关、2串1、3串1；真实数据源可能需要 20 秒左右。"
    : "系统正在拉取赔率、融合概率、计算 Edge/EV，并审查组合风险；真实数据源可能需要 20 秒左右。";
  if (qs("#optimizerCards")) {
    qs("#optimizerCards").innerHTML = `
      <section class="optimizerStatePanel isLoading">
        <span>OPTIMIZER</span>
        <strong>${C.escapeHtml(title)}</strong>
        <p>${C.escapeHtml(body)}</p>
        ${optimizerProgressMarkup(0)}
      </section>
    `;
    startOptimizerProgressTicker();
  }
  if (qs("#optimizerNo2Reason")) qs("#optimizerNo2Reason").innerHTML = C.list(["请稍等，不要重复点击。若完整模型较慢，页面会自动给出可操作状态。"]);
  ["#optimizerProfileComparison", "#optimizerSingles", "#optimizerParlay2", "#optimizerParlay3", "#optimizerSingleRanking", "#optimizerParlay2Ranking", "#optimizerParlay3Ranking", "#optimizerRejected", "#optimizerExplanations"].forEach((selector) => {
    const el = qs(selector);
    if (el) el.innerHTML = "";
  });
}

function renderOptimizerSlowState(message) {
  stopOptimizerProgressTicker();
  const today = state.todayView || {};
  const fallbackSingles = today.top_singles || [];
  const fallback2 = today.top_2x1_display || today.top_parlay_2x1 || [];
  const fallback3 = today.top_3x1_display || today.top_parlay_3x1 || [];
  const fallbackLanes = today.best_parlay_summary?.daily_output_lanes
    || today.optimizer?.best_parlay_summary?.daily_output_lanes
    || state.optimizerView?.best_parlay_summary?.daily_output_lanes
    || [];
  if (qs("#optimizerCards")) {
    qs("#optimizerCards").innerHTML = `
      <section class="optimizerStatePanel isSlow">
        <span>保留可用候选</span>
        <strong>赛前优化后台继续</strong>
        <p>${C.escapeHtml(message || "完整模型较慢，本次不清空页面。先展示最近一次 / 今日观察里的每日候选，等接口恢复后再替换。")}</p>
        <div class="optimizerStateActions">
          <button type="button" class="primary" id="optimizerRetryInlineBtn">重试生成今日观察</button>
          <button type="button" class="secondary" data-jump-view="today">回今日观察</button>
          <button type="button" class="secondary" data-jump-view="missinginfo">先看情报覆盖</button>
        </div>
      </section>
      ${dailyOutputLanesPanel(fallbackLanes)}
    `;
  }
  if (qs("#optimizerNo2Reason")) {
    qs("#optimizerNo2Reason").innerHTML = C.list([
      "本次没有把未完成请求当作失败页，先保留候选预览。",
      "如果经常卡住，优先使用 mock/缓存预览，再等真实数据刷新。",
      "赛前优化恢复后会重新给出单关、2串1、3串1候选榜。",
    ]);
  }
  if (qs("#optimizerSingles")) qs("#optimizerSingles").innerHTML = todayCompactCards(fallbackSingles, "single", "暂无缓存单关候选；请稍后重试。", today.missing_signals || []);
  if (qs("#optimizerParlay2")) qs("#optimizerParlay2").innerHTML = todayCompactCards(fallback2, "combo", "暂无缓存 2串1候选；等待完整候选池。", today.missing_signals || []);
  if (qs("#optimizerParlay3")) qs("#optimizerParlay3").innerHTML = todayCompactCards(fallback3, "combo", "暂无缓存 3串1候选；等待完整候选池。", today.missing_signals || []);
}

function renderOptimizer(view) {
  stopOptimizerProgressTicker();
  state.optimizerView = view;
  const summaryCards = view.summary_cards || [];
  const priorityLabels = new Set(["观察日期", "实际数据源", "分析比赛数", "候选池", "可信度", "职业模型分", "串联纪律", "玩法偏置", "学习调参", "概率校准", "单关观察", "2串1观察", "3串1观察", "AI研究"]);
  const priorityCards = summaryCards.filter((card) => priorityLabels.has(card.label)).slice(0, 8);
  const extraCards = summaryCards.filter((card) => !priorityLabels.has(card.label));
  qs("#optimizerCards").innerHTML = [
    optimizerExecutiveBoard(view),
    dailyOutputLanesPanel(view.daily_output_lanes || view.best_parlay_summary?.daily_output_lanes || []),
    shortCycleModePanel(view),
    C.cards(priorityCards.length ? priorityCards : summaryCards.slice(0, 6)),
    `<details class="detailDrawer"><summary>查看模型体检和玩法偏置</summary>${professionalModelScorePanel(view.professional_model_score || {})}${playBiasPanel(view.play_bias_diagnostics || {})}</details>`,
    extraCards.length ? `<details class="detailDrawer"><summary>查看更多指标</summary>${C.cards(extraCards)}</details>` : "",
  ].join("");
  qs("#optimizerNo2Reason").innerHTML = C.list([
    view.combo_gate_summary_zh || view.no_combo_state?.reason_zh || view.no_combo_reason || view.no_2x1_reason || "当前暂无通过门控组合，先看单关与被拒复盘。",
    `AI 研究：${view.ai_status_summary_zh || view.ai_combo_research?.display_status_zh || view.ai_combo_research?.ds_status_zh || "待检查"}`,
    view.trader_review?.final_call_zh || "先看单关，再决定是否保留组合观察。",
    view.no_combo_reason || view.no_2x1_reason || "当前暂无通过门控组合，先看单关与被拒复盘。",
  ]);
  renderClvTracking(view.clv_tracking || {});
  const profileRows = view.profile_comparison || [];
  qs("#optimizerProfileComparison").innerHTML = profileRows.length ? `<details class="detailDrawer"><summary>查看风险档位对比</summary>${C.table(profileRows, [
    { key: "profile", label: "方案" }, { key: "daily_exposure_cap", label: "每日上限" }, { key: "recommended_paper_exposure", label: "纸面投入" },
    { key: "singles_count", label: "单关" }, { key: "parlay_2x1_count", label: "2串1" }, { key: "parlay_3x1_count", label: "3串1" }, { key: "note", label: "说明" },
  ])}</details>` : "";
  const selectedCols = compactOptimizerColumns();
  qs("#optimizerSingles").innerHTML = [
    todayCompactCards(view.singles_table || [], "single", "当前没有通过纪律筛选的单关观察。", view.missing_signals || []),
    (view.singles_table || []).length ? detailsTable("查看单关详细字段", view.singles_table || [], selectedCols) : "",
  ].join("");
  const parlay2Rows = (view.parlay_2x1_table || []).length ? (view.parlay_2x1_table || []) : (view.candidate_rankings?.parlay_2x1 || []).slice(0, 3);
  const parlay3Rows = (view.parlay_3x1_table || []).length ? (view.parlay_3x1_table || []) : (view.candidate_rankings?.parlay_3x1 || []).slice(0, 3);
  qs("#optimizerParlay2").innerHTML = [
    todayCompactCards(parlay2Rows, "combo", "当前没有可排序 2串1；请先确认比赛数据源。", view.missing_signals || []),
    parlay2Rows.length ? detailsTable("查看2串1详细字段", parlay2Rows, selectedCols) : "",
  ].join("");
  qs("#optimizerParlay3").innerHTML = [
    todayCompactCards(parlay3Rows, "combo", "当前没有可排序 3串1；请先确认比赛数据源。", view.missing_signals || []),
    parlay3Rows.length ? detailsTable("查看3串1详细字段", parlay3Rows, selectedCols) : "",
  ].join("");
  const rankCols = compactOptimizerColumns(true);
  qs("#optimizerSingleRanking").innerHTML = detailsTable("查看单关候选排行榜", view.candidate_rankings?.singles || [], rankCols);
  qs("#optimizerParlay2Ranking").innerHTML = (view.candidate_rankings?.parlay_2x1 || []).length ? detailsTable("查看2串1候选排行榜", view.candidate_rankings?.parlay_2x1 || [], rankCols) : "";
  qs("#optimizerParlay3Ranking").innerHTML = (view.candidate_rankings?.parlay_3x1 || []).length ? detailsTable("查看3串1候选排行榜", view.candidate_rankings?.parlay_3x1 || [], rankCols) : "";
  qs("#optimizerRejected").innerHTML = (view.rejected_table || []).length ? `<details class="detailDrawer"><summary>查看被拒明细</summary>${C.table(view.rejected_table || [], [
    { key: "type", label: "类型" }, { key: "match", label: "候选" }, { key: "ev", label: "EV" }, { key: "edge", label: "Edge" }, { key: "risk_level", label: "风险" }, { key: "reason", label: "被拒原因" },
  ])}</details>` : "";
  qs("#optimizerExplanations").innerHTML = C.list(view.explanations || []);
  qs("#parlay2Table").innerHTML = qs("#optimizerParlay2").innerHTML;
  qs("#parlay3Table").innerHTML = qs("#optimizerParlay3").innerHTML;
  qs("#parlay2RejectedTable").innerHTML = tableOrEmpty(view.candidate_rankings?.parlay_2x1 || [], rankCols, "当前暂无 2串1 被拒复盘项。 ");
  qs("#parlay3RejectedTable").innerHTML = tableOrEmpty(view.candidate_rankings?.parlay_3x1 || [], rankCols, "当前暂无 3串1 被拒复盘项。 ");
  qs("#riskNotes").innerHTML = C.list([view.no_combo_reason || view.no_2x1_reason || "组合放大风险高，建议先看候选纪律复核。", ...(view.explanations || [])]);
}

function dailyOutputLanesPanel(lanes = []) {
  const safe = Array.isArray(lanes) ? lanes : [];
  if (!safe.length) return "";
  return `
    <section class="dailyOutputLanes">
      <header>
        <span>今日输出</span>
        <strong>单关 / 2串1 / 3串1 候选</strong>
        <p>每天固定给出三条可复盘候选。没过纪律门槛也会显示为纸面候选，方便赛后验证规则是不是太保守。</p>
      </header>
      <div>
        ${safe.map((lane) => `
          <article data-status="${C.escapeHtml(lane.status || "unknown")}">
            <div>
              <span>${C.escapeHtml(lane.label_zh || "候选")}</span>
              <b>${C.escapeHtml(lane.status_zh || "待复核")}</b>
            </div>
            <strong>${C.escapeHtml(shortText(lane.target_zh || "暂无候选", 54))}</strong>
            ${lane.verdict_zh ? `<mark>${C.escapeHtml(lane.verdict_zh)}</mark>` : ""}
            <dl>
              <dt>赔率</dt><dd>${C.escapeHtml(lane.odds_zh || "N/A")}</dd>
              <dt>模型</dt><dd>${C.escapeHtml(lane.model_prob_zh || "N/A")}</dd>
              <dt>市场</dt><dd>${C.escapeHtml(lane.market_prob_zh || "N/A")}</dd>
              <dt>EV</dt><dd>${C.escapeHtml(lane.ev_zh || "N/A")}</dd>
              <dt>Edge</dt><dd>${C.escapeHtml(lane.edge_zh || "N/A")}</dd>
              <dt>风险</dt><dd>${C.escapeHtml(lane.risk_zh || "N/A")}</dd>
            </dl>
            <p>${C.escapeHtml(lane.action_zh || "等待复核")}</p>
            <em>${C.escapeHtml(shortText(lane.why_zh || lane.next_review_zh || "", 110))}</em>
            ${Array.isArray(lane.review_checklist_zh) && lane.review_checklist_zh.length ? `
              <ul>
                ${lane.review_checklist_zh.slice(0, 4).map((item) => `<li>${C.escapeHtml(item)}</li>`).join("")}
              </ul>
            ` : ""}
            ${lane.next_review_zh ? `<small>${C.escapeHtml(shortText(`下一步：${lane.next_review_zh}`, 120))}</small>` : ""}
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function shortCycleModePanel(view = {}) {
  const note = view.candidate_rankings?.singles?.[0]?.short_cycle_reason_zh || view.singles_table?.[0]?.short_cycle_reason_zh || "短周期调整会显示在候选明细里。";
  return `
    <section class="shortCycleModePanel">
      <span>WORLD CUP SHORT-CYCLE MODE</span>
      <strong>短赛会模式：先给候选，再防同质化</strong>
      <p>世界杯/杯赛阶段样本少，系统会优先看市场一致、概率区间稳、方向分散；不再只按高 EV 或高赔率排序。</p>
      <div>
        <em>同向主胜/让胜刷屏会被同质化降权。</em>
        <em>2串1/3串1保留纸面候选，但未过纪律不会包装成强观察。</em>
        <em>${C.escapeHtml(shortText(note, 96))}</em>
      </div>
    </section>
  `;
}

function compactOptimizerColumns(includeStatus = false) {
  const cols = [
    { key: "type", label: "类型" },
    { key: "match", label: "比赛/候选" },
    { key: "legs", label: "组成" },
    { key: "odds", label: "赔率" },
    { key: "model_prob", label: "模型概率" },
    { key: "market_prob", label: "市场概率" },
    { key: "ev", label: "EV" },
    { key: "edge", label: "Edge" },
    { key: "confidence", label: "可信度" },
    { key: "risk_level", label: "风险" },
    { key: "short_cycle_reason_zh", label: "短周期调整" },
    { key: "combo_homogeneity_reason_zh", label: "同质化" },
    { key: "recommended_action_zh", label: "动作" },
    { key: "reject_reason", label: "拒绝/保留原因" },
  ];
  if (includeStatus) cols.splice(10, 0, { key: "status", label: "状态" });
  return cols;
}

function optimizerExecutiveBoard(view = {}) {
  const singles = view.singles_table || view.candidate_rankings?.singles || [];
  const parlay2 = view.parlay_2x1_table || view.candidate_rankings?.parlay_2x1 || [];
  const parlay3 = view.parlay_3x1_table || view.candidate_rankings?.parlay_3x1 || [];
  const brief = view.daily_candidate_brief || {};
  const topSingle = singles[0] || {};
  const top2 = parlay2[0] || {};
  const top3 = parlay3[0] || {};
  const homogeneity = firstNonEmpty([
    top2.combo_homogeneity_reason_zh,
    top3.combo_homogeneity_reason_zh,
    (view.play_bias_diagnostics || {}).summary_zh,
  ], "如果候选集中在让胜/主胜，系统会标记玩法偏置：这说明方向单一，不能当作多样化组合。");
  const comboTruth = firstNonEmpty([
    top2.legs ? `2串1纸面候选：${top2.legs}` : "",
    view.no_2x1_reason,
    view.no_combo_reason,
    "没有足够分散、概率覆盖和可信度支撑时，不升级为正式组合。",
  ], "");
  const cards = [
    optimizerDecisionCard("最先看", topSingle.match || "暂无可用单关", topSingle.decision_label_zh || topSingle.status || "待复核", firstNonEmpty([topSingle.decision_reason_zh, topSingle.reason, "先判断单腿是否真的有赔率价值。"], "")),
    optimizerDecisionCard("2串1", top2.legs || top2.match || "今日相对2串1候选", top2.status || "纸面/待复核", comboTruth),
    optimizerDecisionCard("3串1", top3.legs || top3.match || "今日相对3串1候选", top3.status || "高风险", firstNonEmpty([top3.reject_reason, top3.discipline_summary_zh, "3串1 只保留作学习样本，不能用赔率高掩盖低命中概率。"], "")),
    optimizerDecisionCard("为什么方向单一", "玩法同质化审计", (view.play_bias_diagnostics || {}).label_zh || "检查中", homogeneity),
  ];
  return `
    <section class="optimizerExecutiveBoard">
      <header>
        <span>${C.escapeHtml(brief.score_zh ? `USEFUL RESULT · ${brief.score_zh}` : "USEFUL RESULT")}</span>
        <strong>${C.escapeHtml(brief.headline_zh || view.trader_review?.final_call_zh || view.combo_gate_summary_zh || "赛前优化完成")}</strong>
        <p>${C.escapeHtml(brief.summary_zh || view.no_combo_state?.reason_zh || view.no_combo_reason || "先看候选质量，再看是否值得组合。")}</p>
        ${brief.score_explain_zh ? `<em>${C.escapeHtml(brief.score_explain_zh)}</em>` : ""}
      </header>
      <div>${cards.join("")}</div>
      ${optimizerChecklistStrip(brief)}
      ${brief.next_action_zh ? `<p class="optimizerBoardNext">${C.escapeHtml(brief.next_action_zh)}</p>` : ""}
    </section>
  `;
}

function optimizerChecklistStrip(brief = {}) {
  const pre = Array.isArray(brief.pre_match_checklist_zh) ? brief.pre_match_checklist_zh : [];
  const post = Array.isArray(brief.post_match_learning_checklist_zh) ? brief.post_match_learning_checklist_zh : [];
  if (!pre.length && !post.length) return "";
  return `
    <details class="optimizerChecklistStrip isCollapsed">
      <summary>查看赛前复核 / 赛后学习清单</summary>
      <div>
        ${pre.length ? `
          <article>
            <span>赛前复核</span>
            <ul>${pre.slice(0, 4).map((item) => `<li>${C.escapeHtml(item)}</li>`).join("")}</ul>
          </article>
        ` : ""}
        ${post.length ? `
          <article>
            <span>赛后学习</span>
            <ul>${post.slice(0, 4).map((item) => `<li>${C.escapeHtml(item)}</li>`).join("")}</ul>
          </article>
        ` : ""}
      </div>
    </details>
  `;
}

function optimizerDecisionBoard(view = {}) {
  const singles = view.singles_table || view.candidate_rankings?.singles || [];
  const parlay2 = view.parlay_2x1_table || view.candidate_rankings?.parlay_2x1 || [];
  const parlay3 = view.parlay_3x1_table || view.candidate_rankings?.parlay_3x1 || [];
  const topSingle = singles[0] || {};
  const top2 = parlay2[0] || {};
  const top3 = parlay3[0] || {};
  const bias = view.play_bias_diagnostics || {};
  const pro = view.professional_model_score || {};
  const radar = pro.score_gap_radar || [];
  const biasGap = radar.find((row) => row.key === "play_bias_control") || {};
  const marketGap = firstNonEmpty([
    topSingle.model_disagreement_reason_zh,
    top2.model_disagreement_reason_zh,
    top3.model_disagreement_reason_zh,
    topSingle.discipline_summary_zh && topSingle.discipline_summary_zh.includes("模型分歧") ? topSingle.discipline_summary_zh : "",
  ], "模型与市场分歧待复核。");
  const learningAdjustment = firstNonEmpty([
    topSingle.strategy_adjustment_reason_zh,
    top2.strategy_adjustment_reason_zh,
    top3.strategy_adjustment_reason_zh,
    top2.combo_homogeneity_reason_zh,
    top3.combo_homogeneity_reason_zh,
    view.strategy_adjustment_status?.reason_zh,
  ], "赛后学习样本不足时，只做轻量调参，不会大幅改变排序。");
  const probabilityCalibration = firstNonEmpty([
    topSingle.probability_shrinkage_reason_zh,
    top2.probability_shrinkage_reason_zh,
    top3.probability_shrinkage_reason_zh,
    topSingle.market_benchmark_discipline_zh,
    top2.market_benchmark_discipline_zh,
    top3.market_benchmark_discipline_zh,
    view.probability_shrinkage_status?.reason_zh,
  ], "样本不足或市场分歧较大时，模型概率会向市场概率收缩。");
  const robustValue = firstNonEmpty([
    topSingle.robust_value_reason_zh,
    top2.robust_value_reason_zh,
    top3.robust_value_reason_zh,
  ], "用概率区间下沿检查 EV 和 Edge，避免只看点概率造成虚高。");
  const cards = [
    optimizerDecisionCard("单关优先级", topSingle.match || "暂无强单关", topSingle.decision_label_zh || topSingle.status || "待复核", firstNonEmpty([topSingle.decision_reason_zh, topSingle.reason, topSingle.discipline_summary_zh], "先看概率、赔率价值和情报完整度。")),
    optimizerDecisionCard("2串1纪律", top2.legs || top2.match || "今日相对2串1候选", top2.status || view.no_combo_state?.label_zh || "未过门控", firstNonEmpty([top2.reject_reason, top2.discipline_summary_zh, view.no_2x1_reason, view.no_combo_reason], "2串1 需要两腿同时命中，先看联合概率和相关性。")),
    optimizerDecisionCard("3串1纪律", top3.legs || top3.match || "今日相对3串1候选", top3.status || "高风险待复核", firstNonEmpty([top3.reject_reason, top3.discipline_summary_zh, "3串1 风险最高，只保留纸面候选用于赛后学习。"], "")),
    optimizerDecisionCard("玩法偏置", bias.label_zh || "玩法分布待检查", biasGap.score == null ? "待检查" : `${biasGap.score}/${biasGap.target_score || 84}`, firstNonEmpty([bias.summary_zh, biasGap.next_step_zh], "如果让球胜平负或同方向刷屏，系统会降权并等待赛后验证。")),
    optimizerDecisionCard("组合同质化", firstNonEmpty([top2.combo_homogeneity_reason_zh, top3.combo_homogeneity_reason_zh], "组合结构相对分散"), top2.combo_homogeneity?.level || top3.combo_homogeneity?.level || "audit", "不是不同比赛就一定分散；同玩法、同方向、同赔率段、同AI因子会被额外审计。"),
    optimizerDecisionCard("模型-市场一致性", marketGap, "分歧审计", "模型看好但市场不支持时，不直接升级为强组合；先降权、再看 CLV 和赛后样本。"),
    optimizerDecisionCard("市场基准纪律", firstNonEmpty([topSingle.market_benchmark_discipline_zh, top2.market_benchmark_discipline_zh, top3.market_benchmark_discipline_zh], "等待赛后样本证明模型是否优于市场概率。"), "market", "专业模型必须证明概率长期优于市场基准；否则排序更尊重市场赔率。"),
    optimizerDecisionCard("概率纪律校准", probabilityCalibration, view.probability_shrinkage_status?.status || "calibrated", "原模型概率保留作审计，排序使用校准概率，避免小样本模型过度自信。"),
    optimizerDecisionCard("稳健价值检验", robustValue, topSingle.robust_value_label_zh || top2.robust_value_label_zh || "区间审计", "只要概率下沿无法覆盖赔率，候选就会被降权；组合腿更严格。"),
    optimizerDecisionCard("赛后学习调参", learningAdjustment, view.strategy_adjustment_status?.status || "learning", "弱玩法、长赔、负 CLV 或弱赔率段会轻量压低排序；样本不足时只提醒，不硬改模型。"),
    optimizerDecisionCard("下一步", view.trader_review?.final_call_zh || view.combo_gate_summary_zh || "先看结论，再看排行榜", view.risk_profile_label || "进取", firstNonEmpty([view.ai_status_summary_zh, view.no_combo_reason, "展开排行榜查看完整证据。"], "")),
  ];
  return `
    <section class="optimizerDecisionBoard">
      <header>
        <span>DECISION BOARD</span>
        <strong>先看结论，再看细表</strong>
        <p>这里压缩显示使用者真正需要的判断：单关、2串1、3串1、玩法偏置、模型市场分歧和下一步。</p>
      </header>
      <div>${cards.join("")}</div>
    </section>
  `;
}

function optimizerDecisionCard(label, title, badge, body) {
  return `
    <article>
      <span>${C.escapeHtml(label || "判断")}</span>
      <strong>${C.escapeHtml(shortText(title || "待复核", 46))}</strong>
      <b>${C.escapeHtml(shortText(badge || "待检查", 24))}</b>
      <p>${C.escapeHtml(shortText(body || "继续查看候选和被拒原因。", 96))}</p>
    </article>
  `;
}

function firstNonEmpty(values = [], fallback = "") {
  for (const value of values) {
    const text = value == null ? "" : String(value).trim();
    if (text) return text;
  }
  return fallback;
}

function playBiasPanel(diag = {}) {
  if (!diag || !Object.keys(diag).length) return "";
  const sections = diag.sections || [];
  return `
    <section class="playBiasPanel" data-status="${C.escapeHtml(diag.status || "balanced")}">
      <div>
        <span>玩法偏置诊断</span>
        <strong>${C.escapeHtml(diag.label_zh || "玩法分布待检查")}</strong>
        <p>${C.escapeHtml(diag.summary_zh || "检查候选是否过度集中在某一种玩法或方向。")}</p>
      </div>
      <div class="playBiasGrid">
        ${sections.map((item) => `
          <article>
            <b>${C.escapeHtml(item.label_zh || "候选")}</b>
            <span>${C.escapeHtml(item.top_play_type || "暂无")} · ${C.escapeHtml(fmtPct(item.top_play_share))}</span>
            <em>${C.escapeHtml(item.message_zh || "")}</em>
          </article>
        `).join("")}
      </div>
      <p class="mutedLine">${C.escapeHtml(diag.next_step_zh || "长期按玩法统计命中率，不因单日集中就盲目调权重。")}</p>
    </section>
  `;
}

function professionalModelScorePanel(score) {
  if (!score || !Object.keys(score).length) return "";
  const components = Array.isArray(score.components) ? score.components : [];
  const missing = Array.isArray(score.missing_to_95) ? score.missing_to_95 : [];
  const principles = Array.isArray(score.principles_zh) ? score.principles_zh : [];
  const researchSources = Array.isArray(score.research_sources_zh) ? score.research_sources_zh : [];
  const benchmarks = Array.isArray(score.industry_benchmark_zh) ? score.industry_benchmark_zh : [];
  const evidence = score.learning_evidence || {};
  const roadmap = score.roadmap_to_95 || {};
  const roadmapItems = Array.isArray(roadmap.items) ? roadmap.items : [];
  const gapRows = Array.isArray(score.score_gap_radar) ? score.score_gap_radar : [];
  const topGap = gapRows[0] || {};
  const nextActions = Array.isArray(roadmap.next_best_actions) ? roadmap.next_best_actions : [];
  const firstAction = nextActions[0] || {};
  const benchmarkSummary = professionalBenchmarkSummary(benchmarks);
  const evidenceRequirements = score.evidence_requirements || {};
  const gateChecklist = Array.isArray(evidenceRequirements.gate_checklist) ? evidenceRequirements.gate_checklist : [];
  const current = Number(score.score || 0);
  const ceiling = Number(score.ceiling_score || 0);
  const pct = Math.max(0, Math.min(100, current));
  const ceilingPct = Math.max(0, Math.min(100, ceiling || 95));
  return `
    <section class="proScorePanel">
      <div class="proScoreHeader">
        <div>
          <span>PRO MODEL SCORE</span>
          <strong>${C.escapeHtml(score.label_zh || "职业模型评估")}</strong>
          <p>${C.escapeHtml(score.summary_zh || "按市场、模型、情报、校准、CLV、组合纪律和学习闭环综合评估。")}</p>
        </div>
        <div class="proScoreDial" style="--score:${pct}%;--ceiling:${ceilingPct}%">
          <b>${C.escapeHtml(String(current || "--"))}</b>
          <em>/100</em>
        </div>
      </div>
      <div class="proScoreTrack" aria-label="职业模型分">
        <i style="--score:${pct}%"></i>
        <b style="left:${ceilingPct}%">上限 ${C.escapeHtml(String(ceiling || 95))}</b>
      </div>
      <div class="proScoreConclusionStrip">
        <article>
          <span>当前判断</span>
          <strong>${C.escapeHtml(current >= 85 ? "接近职业级" : current >= 70 ? "可研究但需复盘" : "证据仍不足")}</strong>
          <p>${C.escapeHtml(ceiling < 95 ? `当前上限 ${ceiling}，先补硬证据再谈 95。` : "理论上限已打开，继续看缺口雷达。")}</p>
        </article>
        <article>
          <span>最大拖分项</span>
          <strong>${C.escapeHtml(topGap.label_zh || "待生成")}</strong>
          <p>${C.escapeHtml(topGap.impact_zh || topGap.next_step_zh || "生成模型体检后查看。")}</p>
        </article>
        <article>
          <span>第一动作</span>
          <strong>${C.escapeHtml(firstAction.title_zh || "补赛后证据")}</strong>
          <p>${C.escapeHtml(firstAction.action_zh || "保存赛前观察，赛后补比分和收盘赔率。")}</p>
        </article>
        <article>
          <span>行业基准</span>
          <strong>${C.escapeHtml(benchmarkSummary.label)}</strong>
          <p>${C.escapeHtml(benchmarkSummary.detail)}</p>
        </article>
      </div>
      ${components.length ? `
        <div class="proScoreGrid">
          ${components.map((item) => `
            <article>
              <header><span>${C.escapeHtml(item.label_zh || item.key || "评分项")}</span><b>${C.escapeHtml(String(item.score ?? "--"))}</b></header>
              <div class="miniMeter"><i style="--score:${Math.max(0, Math.min(100, Number(item.score || 0)))}%"></i></div>
              <p>${C.escapeHtml(item.detail_zh || "")}</p>
            </article>
          `).join("")}
        </div>
      ` : ""}
      <div class="proEvidenceStrip" aria-label="职业模型证据">
        <article><span>赛后样本</span><b>${C.escapeHtml(String(evidence.settled_count ?? 0))}</b><em>已结算观察</em></article>
        <article><span>Brier</span><b>${C.escapeHtml(evidence.brier_score == null ? "N/A" : String(evidence.brier_score))}</b><em>概率校准</em></article>
        <article><span>Log Loss</span><b>${C.escapeHtml(evidence.log_loss == null ? "N/A" : String(evidence.log_loss))}</b><em>过度自信惩罚</em></article>
        <article><span>CLV</span><b>${C.escapeHtml(evidence.average_clv_pct == null ? "N/A" : fmtSignedPct(evidence.average_clv_pct))}</b><em>${C.escapeHtml(String(evidence.clv_settled_count ?? 0))} 条收盘样本</em></article>
        <article><span>市场技能分</span><b>${C.escapeHtml(evidence.market_benchmark?.brier_skill_score == null ? "N/A" : fmtSignedPct(evidence.market_benchmark.brier_skill_score))}</b><em>模型 vs 市场概率</em></article>
      </div>
      ${evidence.evidence_zh || evidence.market_benchmark_summary_zh ? `<p class="proEvidenceNote">${C.escapeHtml([evidence.evidence_zh, evidence.market_benchmark_summary_zh].filter(Boolean).join(" "))}</p>` : ""}
      ${gateChecklist.length ? `
        <section class="proGateChecklist">
          <header>
            <span>EVIDENCE GATES</span>
            <strong>证据门槛</strong>
            <p>${C.escapeHtml(evidenceRequirements.summary_zh || "职业级不是靠单日命中证明，而是靠长期证据逐档解锁。")}</p>
          </header>
          <div>
            ${gateChecklist.map((item) => `
              <article class="${item.passed ? "passed" : "blocked"}">
                <b>${C.escapeHtml(String(item.level || ""))}</b>
                <strong>${C.escapeHtml(item.label_zh || "门槛")}</strong>
                <p>${C.escapeHtml(item.next_missing_zh || item.message_zh || "")}</p>
              </article>
            `).join("")}
          </div>
        </section>
      ` : ""}
      ${roadmapItems.length ? `
        <section class="proRoadmap">
          <header>
            <span>PATH TO 95</span>
            <strong>95 分路线图</strong>
            <p>${C.escapeHtml(roadmap.summary_zh || "先补真实数据、赛后样本和 CLV，再谈接近职业级。")}</p>
          </header>
          <div class="proRoadmapList">
            ${roadmapItems.map((item) => `
              <article class="status-${C.escapeHtml(item.status || "todo")}">
                <b>${C.escapeHtml(item.label_zh || "改进项")}</b>
                <em>${C.escapeHtml(item.status_zh || "")}${item.estimated_score_gain ? ` · 预计 +${C.escapeHtml(String(item.estimated_score_gain))} 分` : ""}</em>
                <div class="miniMeter"><i style="--score:${Math.max(0, Math.min(100, Number(item.score || 0)))}%"></i></div>
                <p>${C.escapeHtml(item.current_state_zh || "")}</p>
                <small>${C.escapeHtml(item.priority_zh || "")}${item.priority_rank ? ` · 优先级 ${C.escapeHtml(String(item.priority_rank))}` : ""}</small>
                <small>${C.escapeHtml(item.why_it_matters_zh || "")}</small>
              </article>
            `).join("")}
          </div>
        </section>
      ` : ""}
      ${benchmarks.length ? `
        <details class="detailDrawer proBenchmarkDrawer" open>
          <summary>按职业模型基准检查</summary>
          <div class="proBenchmarkGrid">
            ${benchmarks.map((item) => `
              <article class="status-${C.escapeHtml(item.status || "not_yet")}">
                <header>
                  <b>${C.escapeHtml(item.label_zh || "检查项")}</b>
                  <em>${C.escapeHtml(item.status_zh || "")}</em>
                </header>
                <div class="miniMeter"><i style="--score:${Math.max(0, Math.min(100, Number(item.score || 0)))}%"></i></div>
                <p>${C.escapeHtml(item.detail_zh || "")}</p>
                <small>${C.escapeHtml(item.next_step_zh || "")}</small>
              </article>
            `).join("")}
          </div>
        </details>
      ` : ""}
      ${missing.length ? `
        <details class="detailDrawer proScorePath" open>
          <summary>距离 95 分还差什么</summary>
          ${C.list(missing)}
        </details>
      ` : ""}
      ${principles.length ? `
        <details class="detailDrawer proScorePath">
          <summary>职业级判断原则</summary>
          ${C.list(principles)}
        </details>
      ` : ""}
      ${researchSources.length ? `
        <details class="detailDrawer proScorePath">
          <summary>主流模型依据摘要</summary>
          ${C.list(researchSources)}
        </details>
      ` : ""}
    </section>
  `;
}

function professionalBenchmarkSummary(benchmarks = []) {
  const rows = Array.isArray(benchmarks) ? benchmarks : [];
  if (!rows.length) {
    return { label: "待检查", detail: "暂无行业基准明细。" };
  }
  const passed = rows.filter((item) => ["passed", "done", "ok"].includes(String(item.status || ""))).length;
  const partial = rows.filter((item) => ["partial", "warning", "in_progress"].includes(String(item.status || ""))).length;
  const total = rows.length;
  const label = `${passed}/${total} 通过`;
  const blockers = rows.filter((item) => !["passed", "done", "ok"].includes(String(item.status || ""))).slice(0, 2).map((item) => item.label_zh || item.key).filter(Boolean);
  const detail = blockers.length
    ? `未完全达标：${blockers.join("、")}。`
    : `全部核心基准已通过，继续扩大样本。`;
  return { label, detail: partial ? `${detail} 其中 ${partial} 项仍需观察。` : detail };
}

async function loadScoreGoals(options = {}) {
  const payload = await request("/api/view/score-goals", { provider: providerParam(), date: state.todayView?.selected_date || currentDateParam() }, "刷新比分/进球数", 60000);
  if (payload.ok) renderScoreGoals(payload.data);
  if (!options.stayOnCurrentView) switchView("scoregoals");
}
function renderScoreGoals(view) {
  state.scoreGoalsView = view;
  qs("#scoreGoalsCards").innerHTML = C.cards(view.summary_cards || []);
  qs("#scoreGoalsHandicap").innerHTML = [
    scoreGoalCards(view.handicap_table || [], "handicap", "当前没有让球胜平负观察。"),
    detailsTable("查看让球详细字段", view.handicap_table || [], compactObsColumns()),
  ].join("");
  qs("#scoreGoalsTotals").innerHTML = [
    `<div class="sectionHint">优先看“模型概率、赔率/EV 状态、可信度和动作”。完整技术字段放在下方折叠详情里。</div>`,
    scoreGoalCards(view.total_goals_table || [], "total", "当前没有总进球观察。"),
    detailsTable("查看总进球详细字段", view.total_goals_table || [], compactObsColumns()),
  ].join("");
  qs("#scoreGoalsScores").innerHTML = [
    `<div class="sectionHint">比分是高波动精确事件，只适合作为倾向参考，不适合作为强信号。</div>`,
    scoreGoalCards(view.score_table || [], "score", "当前没有比分观察。"),
    detailsTable("查看比分详细字段", view.score_table || [], compactObsColumns()),
  ].join("");
  qs("#scoreGoalsIntegrity").innerHTML = (view.probability_integrity || []).length ? `<details class="detailDrawer"><summary>查看概率矩阵完整性</summary>${C.table(view.probability_integrity || [], [
    { key: "match", label: "比赛" },
    { key: "total_goals_sum", label: "总进球合计" },
    { key: "had_sum", label: "胜平负合计" },
    { key: "hhad_sum", label: "让球合计" },
    { key: "top5_score_mass", label: "Top5 比分覆盖" },
    { key: "status", label: "状态" },
    { key: "message_zh", label: "说明" },
  ])}</details>` : "";
  const reliabilityRows = view.reliability_notes || [];
  const missingNotes = (view.missing_signals || []).map((x) => `${intelligenceLabel(x)}：当前按未知处理。`);
  qs("#scoreGoalsNotes").innerHTML = [
    C.list([...(view.risk_notes || []), ...missingNotes]),
    reliabilityRows.length ? `<details class="detailDrawer"><summary>查看玩法可靠性说明</summary>${C.table(reliabilityRows, [
      { key: "type", label: "玩法" },
      { key: "reliability", label: "可靠性" },
      { key: "usage", label: "适合用途" },
      { key: "why", label: "原因" },
      { key: "top_example", label: "当前示例" },
    ])}</details>` : "",
  ].join("");
}

function compactObsColumns() {
  return [
    { key: "match", label: "比赛" },
    { key: "play_type", label: "玩法" },
    { key: "direction", label: "方向" },
    { key: "model_prob", label: "模型概率" },
    { key: "official_odds", label: "赔率" },
    { key: "ev_status_zh", label: "EV 状态" },
    { key: "confidence_label_zh", label: "可信度" },
    { key: "market_audit_zh", label: "赔率审计" },
    { key: "recommended_action_zh", label: "动作" },
  ];
}

function detailsTable(title, rows, columns) {
  if (!rows || !rows.length) return "";
  return `<details class="detailDrawer"><summary>${C.escapeHtml(title)}</summary>${C.table(rows, columns)}</details>`;
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
  const credibility = await request("/api/view/backtest-credibility", { input: params.input, source_type: "user_csv" }, "评估 CSV 回测可信度");
  if (credibility.ok) renderBacktestCredibility(credibility.data);
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
function renderClvTracking(view) {
  const cardsEl = qs("#optimizerClvCards");
  const tableEl = qs("#optimizerClvTable");
  const notesEl = qs("#optimizerClvNotes");
  if (!cardsEl || !tableEl || !notesEl) return;
  const rows = view.rows || [];
  const waitingRows = rows.filter((row) => String(row.status || "").includes("等待") || !row.closing_odds || row.closing_odds === "N/A");
  const settledRows = rows.length - waitingRows.length;
  const summary = view.summary_zh || (rows.length
    ? `已记录 ${rows.length} 个赛前赔率观察项，其中 ${waitingRows.length} 个等待收盘赔率；当前不把 CLV 当作赛前主判断。`
    : "当前没有可跟踪的 CLV 观察项。");
  cardsEl.innerHTML = C.cards([
    { label: "CLV状态", value: rows.length ? "等待赛后" : "暂无", help: summary },
    { label: "赛前记录", value: rows.length, help: "只说明已记录赛前赔率，不代表信号强弱。" },
    { label: "已可复盘", value: settledRows, help: "有收盘赔率后才计算 CLV。" },
  ]);
  tableEl.innerHTML = rows.length ? `<details class="detailDrawer"><summary>查看 CLV 等待明细</summary>${C.table(rows, [
    { key: "match", label: "比赛" },
    { key: "direction", label: "方向" },
    { key: "entry_odds", label: "赛前赔率" },
    { key: "closing_odds", label: "收盘赔率" },
    { key: "status", label: "状态" },
    { key: "message", label: "解释" },
  ])}</details>` : "";
  notesEl.innerHTML = C.list([summary, "CLV 是赛后学习指标；没有收盘赔率时，不应占用赛前主屏。"]);
}
function renderBacktestCredibility(report) {
  qs("#backtestCredibilityCards").innerHTML = C.cards([
    { label: "可信度", value: `${report.score ?? 0}/100`, help: `评级 ${report.grade || "D"}，等级 ${report.confidence_level_zh || "低"}` },
    { label: "样本量", value: report.row_count ?? 0, help: "历史比赛越多，回测越不容易被短期波动误导。" },
    { label: "赔率覆盖", value: fmtPct(report.odds_coverage), help: "胜/平/负赔率覆盖越完整，EV 和 CLV 复盘越可靠。" },
    { label: "赛果覆盖", value: fmtPct(report.result_coverage), help: "主客队进球/比分字段决定回测能否结算。" },
  ]);
  qs("#backtestCredibilityNotes").innerHTML = C.list([
    ...(report.reasons || []),
    ...(report.next_steps || []),
    report.disclaimer || "回测可信度不保证未来表现。",
  ]);
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
async function loadLlmStatus() {
  const payload = await request("/api/llm/status", {}, "读取解释层状态");
  if (!payload.ok || !qs("#llmStatusPanel")) return;
  const data = payload.data || {};
  const displayInputTokens = data.max_input_tokens || (data.api_key_present ? "24000" : "N/A");
  const displayOutputTokens = data.max_output_tokens || (data.api_key_present ? "4000" : "N/A");
  const runtimeLine = data.last_attempt_at
    ? `最近一次：${data.runtime_status_zh || data.runtime_status || "未知"}；目标 ${data.last_provider_target || "N/A"} / 实际 ${data.last_provider_resolved || "N/A"}`
    : "最近一次：还没有触发本轮 DS 研究。";
  const detailLine = data.status_detail_zh || data.fallback_reason || "自动 DS：等待 key 或启用状态；不可用时会改用本地研究摘要。";
  const configLine = data.config_status_zh || "配置状态：待检查。";
  const runtimeNotice = data.runtime_notice_zh || "本轮状态：待检查。";
  const nextStep = data.next_step_zh || "刷新今日观察后，系统会自动判断是否触发 DS 研究。";
  qs("#llmStatusPanel").innerHTML = C.list([
    `状态：${data.status_zh || data.status || "unknown"}；模型：${data.model || "未配置"}`,
    `配置：${configLine}`,
    `API key：${data.api_key_present ? "已配置" : "未配置"}；默认外部调用：${data.external_calls_default ? "是" : "否"}`,
    `Token 上限：输入 ${displayInputTokens} / 输出 ${displayOutputTokens}`,
    data.ready_for_auto ? "自动 DS：已就绪；刷新 T+1 后会自动运行研究层。" : (data.fallback_reason || "自动 DS：等待 key 或启用状态；不可用时会改用本地研究摘要。"),
    `本轮触发：${data.ds_attempted ? "已尝试" : "未尝试"}；结果：${data.ds_completed ? "已成功返回" : "未成功返回"}`,
    data.last_token_total ? `最近一次消耗：输入 ${data.last_token_in ?? "N/A"} / 输出 ${data.last_token_out ?? "N/A"} / 合计 ${data.last_token_total}` : "最近一次消耗：暂无",
    runtimeLine,
    runtimeNotice,
    detailLine,
    `下一步：${nextStep}`,
    data.last_error_label_zh ? `最近一次异常：${data.last_error_label_zh}${data.last_error_message_zh ? `；${data.last_error_message_zh}` : ""}` : "最近一次异常：暂无",
    ...(Array.isArray(data.decision_chain) ? data.decision_chain.map((step) => `${step.label_zh || step.step}：${step.detail_zh || (step.passed ? "已通过" : "未通过")}`) : []),
    "长线策略：便宜 token 优先用于解释被拒组合、缺失情报、赛后复盘和下一轮改进，不直接改概率引擎。",
    "用途：只做解释层，不参与概率、EV、候选筛选或组合决策。",
  ]);
}

function bind(selector, event, handler) { const el = qs(selector); if (el) el.addEventListener(event, handler); }
document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => jumpToView(tab.dataset.view)));
document.querySelectorAll("[data-jump-view]").forEach((button) => button.addEventListener("click", () => jumpToView(button.dataset.jumpView)));
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest("[data-jump-view]") : null;
  if (!button) return;
  event.preventDefault();
  jumpToView(button.dataset.jumpView);
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest("#optimizerRetryInlineBtn") : null;
  if (!button) return;
  event.preventDefault();
  runOneClickObservation();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest("#todayFallbackOptimizerBtn") : null;
  if (!button) return;
  event.preventDefault();
  runOneClickObservation();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest("[data-run-optimizer]") : null;
  if (!button) return;
  event.preventDefault();
  runOneClickObservation();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest("[data-run-scoregoals]") : null;
  if (!button) return;
  event.preventDefault();
  loadScoreGoals();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest(".matchdayReviewBtn") : null;
  if (button) evaluateMatchdayOdds(button);
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest("#quickLearningPackBtn") : null;
  if (!button) return;
  event.preventDefault();
  prepareDailyLearningPack();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest("#quickComboDisciplineBtn") : null;
  if (!button) return;
  event.preventDefault();
  loadBestParlay();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest(".workflowExperimentRecordBtn") : null;
  if (!button) return;
  event.preventDefault();
  recordTodayExperimentStart();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest(".workflowExperimentReviewBtn") : null;
  if (!button) return;
  event.preventDefault();
  reviewTodayExperiment();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest(".workflowNextExperimentPlanBtn") : null;
  if (!button) return;
  event.preventDefault();
  recordNextExperimentPlan();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest(".workflowStartPlannedExperimentBtn") : null;
  if (!button) return;
  event.preventDefault();
  startPlannedExperiment();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest(".workflowQuickActionBtn") : null;
  if (!button) return;
  event.preventDefault();
  const action = button.dataset.workflowAction || "";
  const scoreBefore = state.currentWorkflowScore;
  button.classList.add("isWorking");
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  recordWorkflowAction(action, workflowActionStatusText(action), "running", { score_before: scoreBefore });
  if (state.todayView) renderWorkflowScore(state.todayView, "ready");
  setStatus("Working", workflowActionStatusText(action));
  workflowRunQuickAction(action)
    .then(() => {
      recordWorkflowAction(action, workflowActionDoneText(action), "done", { score_before: scoreBefore, score_after: state.currentWorkflowScore });
      if (state.todayView) renderWorkflowScore(state.todayView, "ready");
    })
    .catch((error) => {
      recordWorkflowAction(action, workflowActionErrorText(action, error), "error", { score_before: scoreBefore, score_after: state.currentWorkflowScore });
      if (state.todayView) renderWorkflowScore(state.todayView, "ready");
      setStatus("Check", workflowActionErrorText(action, error));
    })
    .finally(() => {
      button.classList.remove("isWorking");
      button.disabled = false;
      button.removeAttribute("aria-busy");
    });
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest(".workflowClearHistoryBtn") : null;
  if (!button) return;
  event.preventDefault();
  const defaultText = button.dataset.defaultText || button.textContent || "清空";
  button.dataset.defaultText = defaultText;
  if (button.dataset.confirming !== "1") {
    button.dataset.confirming = "1";
    const confirmVerb = defaultText.includes("重置") ? "重置" : "清空";
    button.textContent = `再点确认${confirmVerb}`;
    setStatus("Check", `再次点击${defaultText}会删除最近处理历史。`);
    window.setTimeout(() => {
      if (button.dataset.confirming === "1") {
        button.dataset.confirming = "0";
        button.textContent = button.dataset.defaultText || "清空";
      }
    }, 5000);
    return;
  }
  button.dataset.confirming = "0";
  button.textContent = button.dataset.defaultText || "清空";
  clearWorkflowActionHistory();
});
document.addEventListener("click", (event) => {
  const button = event.target && event.target.closest ? event.target.closest(".workflowCopyBtn") : null;
  if (!button) return;
  event.preventDefault();
  const defaultText = button.dataset.defaultText || button.textContent || "复制摘要";
  button.dataset.defaultText = defaultText;
  button.dataset.copyState = "working";
  button.textContent = "复制中";
  button.disabled = true;
  copyTextToClipboard(button.dataset.copyText || "")
    .then((ok) => {
      button.dataset.copyState = ok ? "done" : "error";
      button.textContent = ok ? "已复制" : "复制失败";
      setStatus(ok ? "Ready" : "Check", ok ? (button.dataset.copyOk || "摘要已复制。") : (button.dataset.copyFail || "复制失败，请手动选中文本。"));
    })
    .catch((error) => {
      button.dataset.copyState = "error";
      button.textContent = "复制失败";
      setStatus("Check", `复制失败：${error?.message || "浏览器未允许剪贴板访问"}`);
    })
    .finally(() => {
      window.setTimeout(() => {
        button.dataset.copyState = "idle";
        button.textContent = button.dataset.defaultText || "复制摘要";
        button.disabled = false;
      }, 1800);
    });
});
bind("#todayRefreshBtn", "click", () => runOneClickObservation());
bind("#todayQuickRefreshBtn", "click", () => runOneClickObservation());
bind("#aiComboResearchBtn", "click", loadAiComboResearch);
bind("#saveDeepSeekTopBtn", "click", saveLocalSecrets);
bind("#todayOptimizerBtn", "click", () => runOneClickObservation());
bind("#todayOperationBtn", "click", runOperation);
bind("#todayImportBtn", "click", previewImport);
bind("#healthBtn", "click", checkHealth);
bind("#clearBtn", "click", clearOutput);
bind("#matchesBtn", "click", loadMatches);
bind("#matchesToOptimizerBtn", "click", () => runOptimizer(true));
bind("#credibilityBtn", "click", loadCredibility);
bind("#missingInfoBtn", "click", loadMissingInfo);
bind("#signalsPreviewBtn", "click", previewSignals);
bind("#bestParlayBtn", "click", () => runOneClickObservation());
bind("#traderReviewBtn", "click", loadTraderReview);
bind("#learningFeedbackBtn", "click", loadLearningFeedback);
bind("#learningBuildBtn", "click", buildLearningFeedbackPreview);
bind("#learningSaveBtn", "click", saveLearningFeedback);
bind("#learningDailyPackBtn", "click", prepareDailyLearningPack);
bind("#learningQuickFormBtn", "click", renderLearningQuickForm);
bind("#learningQuickSaveBtn", "click", saveLearningQuickResults);
bind("#learningDailySaveBtn", "click", saveDailyLearningResults);
bind("#learningSnapshotBtn", "click", saveLearningObservationSnapshot);
bind("#learningResultTemplateBtn", "click", saveLearningResultTemplate);
bind("#learningClosingTemplateBtn", "click", saveLearningClosingOddsTemplate);
bind("#learningClvReviewBtn", "click", reviewLearningClv);
bind("#learningClvSaveBtn", "click", saveLearningClvReview);
bind("#dailyPackTodayBtn", "click", prepareDailyLearningPack);
bind("#dailyReviewTodayBtn", "click", renderLearningQuickForm);
bind("#optimizerBtn", "click", () => runOneClickObservation());
bind("#optimizerCompareBtn", "click", () => runOptimizer(true));
bind("#scoreGoalsBtn", "click", loadScoreGoals);
bind("#operationBtn", "click", runOperation);
bind("#importBtn", "click", previewImport);
bind("#qaBtn", "click", runQa);

renderRaw({});
state.workflowActionHistory = readWorkflowActionHistory().slice(0, 6);
state.lastWorkflowAction = state.workflowActionHistory[0] || null;
updateLearningFlowStatus();
loadLlmStatus();
renderAiResearchMemory();
loadToday();

function installAuxiliaryUseGuides() {
  const guides = [
    {
      view: "#view-missinginfo",
      items: [
        ["已确认", "可以提高信心", "伤停、首发、天气或新闻如果有明确返回，才算真正确认。"],
        ["已检查为空", "不是没有风险", "接口没返回不等于确认没有伤停，只能说明当前来源没查到。"],
        ["兜底估算", "只能作参考", "天气或城市用兜底时，会降低可信度，不当作现场真值。"],
      ],
    },
    {
      view: "#view-import",
      items: [
        ["先预检", "看字段能否识别", "系统会先判断日期、球队、赔率和赛果字段是否齐。"],
        ["再修复", "按中文建议改表", "缺字段时优先补数据，不要让模型猜。"],
        ["最后回测", "样本量决定可信度", "真实历史越完整，Brier、Log Loss、ROI 和走盘复盘越有意义。"],
      ],
    },
    {
      view: "#view-qa",
      items: [
        ["只读边界", "先确认安全", "安全检查会看是否有越界写入、外部调用或不该出现的操作入口。"],
        ["页面语言", "再看是否误导", "如果出现承诺式文案或强行组合，应该被视为问题。"],
        ["接口健康", "最后看服务状态", "本地 API 和 Dashboard 正常，才继续做赛前观察。"],
      ],
    },
  ];
  guides.forEach(({ view, items }) => {
    const root = qs(view);
    if (!root || root.querySelector(".auxUseGuide")) return;
    const heading = root.querySelector(".sectionHeading");
    if (!heading) return;
    const panel = document.createElement("div");
    panel.className = "reviewGuardPanel preRunGuide auxUseGuide";
    panel.innerHTML = items.map(([kicker, title, body]) => `
      <article><span>${C.escapeHtml(kicker)}</span><strong>${C.escapeHtml(title)}</strong><p>${C.escapeHtml(body)}</p></article>
    `).join("");
    heading.insertAdjacentElement("afterend", panel);
  });
}

function translateUserFacingNoise() {
  const replacements = new Map([
    ["N/A", "待完整评估"],
    ["JSON", "情报文件"],
    ["CSV", "历史表格"],
    ["not_connected", "未接入"],
    ["unknown", "未知"],
  ]);
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (nodes.length < 800) {
    const node = walker.nextNode();
    if (!node) break;
    nodes.push(node);
  }
  nodes.forEach((node) => {
    let text = node.nodeValue;
    replacements.forEach((to, from) => {
      if (text.includes(from)) text = text.split(from).join(to);
    });
    node.nodeValue = text;
  });
}

function installUxRepairPass() {
  installAuxiliaryUseGuides();
  translateUserFacingNoise();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", installUxRepairPass, { once: true });
} else {
  installUxRepairPass();
}

function installFinalAuxiliaryRepairs() {
  const forceGuides = [
    {
      view: "#view-missinginfo",
      items: [
        ["先分状态", "已确认才算强情报", "已检查但未返回、兜底估算和未接入都要降可信度。"],
        ["再看影响", "缺口会影响组合", "伤停、首发、天气、新闻面缺失时，不应强行升级 2串1/3串1。"],
        ["最后补充", "只补可靠信息", "本地情报文件可以补充事实，但系统不会自动编造。"],
      ],
    },
    {
      view: "#view-reliability",
      items: [
        ["真实来源", "先看可售比赛和赔率", "竞彩足球主数据优先；第三方赔率只能做交叉参考。"],
        ["覆盖程度", "再看伤停/首发/天气", "复杂情报缺失时，可信度评级必须下调。"],
        ["结论口径", "不要把待评估当确认", "待完整评估代表数据还不够，不代表没有风险。"],
      ],
    },
  ];
  forceGuides.forEach(({ view, items }) => {
    const root = qs(view);
    if (!root || root.querySelector(".auxUseGuide")) return;
    const anchor = root.querySelector(".sectionHeading") || root.querySelector("h2")?.parentElement || root.firstElementChild;
    if (!anchor) return;
    const panel = document.createElement("div");
    panel.className = "reviewGuardPanel preRunGuide auxUseGuide";
    panel.innerHTML = items.map(([kicker, title, body]) => `
      <article><span>${C.escapeHtml(kicker)}</span><strong>${C.escapeHtml(title)}</strong><p>${C.escapeHtml(body)}</p></article>
    `).join("");
    anchor.insertAdjacentElement("afterend", panel);
  });
  translateUserFacingNoise();
}

function installFinalNoiseObserver() {
  installFinalAuxiliaryRepairs();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", installFinalNoiseObserver, { once: true });
} else {
  installFinalNoiseObserver();
}

function translateAllUserFacingNoise() {
  const replacements = [
    ["N/A", "待完整评估"],
    ["JSON", "情报文件"],
    ["CSV", "历史表格"],
    ["not_connected", "未接入"],
    ["unknown", "未知"],
  ];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = [];
  let node;
  while ((node = walker.nextNode())) nodes.push(node);
  nodes.forEach((textNode) => {
    let text = textNode.nodeValue;
    replacements.forEach(([from, to]) => {
      if (text.includes(from)) text = text.split(from).join(to);
    });
    if (text !== textNode.nodeValue) textNode.nodeValue = text;
  });
}

// Unified below by installUnifiedUiPolishLoop().

function translateResultPageLabels() {
  const replacements = [
    ["OPTIMIZER RESULT", "优化结论"],
    ["sporttery", "竞彩足球真实数据"],
    ["Sporttery", "竞彩足球主数据"],
    ["fallback/mock", "回退/示例数据"],
    ["mock", "示例数据"],
    ["CLV状态", "收盘赔率状态"],
    ["CLV 是", "收盘赔率复盘是"],
    ["计算 CLV", "计算收盘赔率复盘"],
    ["AI研究", "AI 研究"],
  ];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = [];
  let node;
  while ((node = walker.nextNode())) nodes.push(node);
  nodes.forEach((textNode) => {
    let text = textNode.nodeValue;
    replacements.forEach(([from, to]) => {
      if (text.includes(from)) text = text.split(from).join(to);
    });
    if (text !== textNode.nodeValue) textNode.nodeValue = text;
  });
}

// Unified below by installUnifiedUiPolishLoop().

function foldDenseResultTables() {
  const foldTargets = [
    ["bestParlayTable", "查看组合审核明细"],
    ["bestParlayRejected", "查看被拒组合明细"],
    ["operationEquityTable", "查看每日本金曲线"],
    ["operationComboTable", "查看单关 / 组合表现明细"],
    ["operationWalkLog", "查看逐笔走盘明细"],
    ["parlay2Table", "查看 2串1 复核明细"],
    ["parlay3Table", "查看 3串1 复核明细"],
    ["parlay2RejectedTable", "查看 2串1 被拒明细"],
    ["parlay3RejectedTable", "查看 3串1 被拒明细"],
  ];
  foldTargets.forEach(([id, summary]) => {
    const box = qs(`#${id}`);
    if (!box || box.dataset.foldedDense === "1") return;
    if (!box.querySelector("table") && !box.innerText.trim()) return;
    const detail = document.createElement("details");
    detail.className = "detailDrawer denseResultFold";
    const summaryEl = document.createElement("summary");
    summaryEl.textContent = summary;
    detail.appendChild(summaryEl);
    const inner = document.createElement("div");
    inner.className = "denseResultFoldBody";
    while (box.firstChild) inner.appendChild(box.firstChild);
    detail.appendChild(inner);
    box.appendChild(detail);
    box.dataset.foldedDense = "1";
  });
}

function installDenseResultFoldObserver() {
  foldDenseResultTables();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", installDenseResultFoldObserver, { once: true });
} else {
  installDenseResultFoldObserver();
}

function repairBrokenDenseFolds() {
  ["bestParlayTable", "bestParlayRejected"].forEach((id) => {
    const box = qs(`#${id}`);
    if (!box) return;
    if (box.dataset.foldedDense === "1" && !box.querySelector(".denseResultFold") && box.querySelector("table")) {
      delete box.dataset.foldedDense;
    }
  });
  foldDenseResultTables();
}
// Unified below by installUnifiedUiPolishLoop().

function foldOptimizerSecondarySections() {
  const targets = [
    ["optimizerClvCards", "查看收盘赔率复盘状态"],
    ["optimizerClvNotes", "查看收盘赔率说明"],
    ["optimizerExplanations", "查看交易纪律完整说明"],
  ];
  targets.forEach(([id, summary]) => {
    const box = qs(`#${id}`);
    if (!box || box.dataset.secondaryFolded === "1" || !box.innerText.trim()) return;
    const detail = document.createElement("details");
    detail.className = "detailDrawer secondaryResultFold";
    const summaryEl = document.createElement("summary");
    summaryEl.textContent = summary;
    detail.appendChild(summaryEl);
    const inner = document.createElement("div");
    inner.className = "secondaryResultFoldBody";
    while (box.firstChild) inner.appendChild(box.firstChild);
    detail.appendChild(inner);
    box.appendChild(detail);
    box.dataset.secondaryFolded = "1";
  });
}

function decorateOptimizerResultCards() {
  const root = qs("#view-optimizer");
  if (!root) return;
  [...root.querySelectorAll(".metricCard")].forEach((card) => {
    const text = card.innerText || "";
    card.classList.toggle("signalPrimaryCard", text.includes("可信度") || text.includes("串联纪律") || text.includes("AI 研究"));
    card.classList.toggle("signalMutedCard", text.includes("观察日期") || text.includes("实际数据源") || text.includes("候选池") || text.includes("分析比赛数"));
  });
}

function installOptimizerResultPolish() {
  foldOptimizerSecondarySections();
  decorateOptimizerResultCards();
  translateResultPageLabels();
}
// Unified below by installUnifiedUiPolishLoop().

function hideOptimizerSecondaryHeadings() {
  const hiddenTitles = new Set(["收盘赔率复盘", "方案对比", "候选排行榜", "被拒原因", "交易纪律"]);
  document.querySelectorAll("#view-optimizer h3").forEach((heading) => {
    const text = (heading.innerText || "").trim();
    if (hiddenTitles.has(text)) heading.classList.add("visuallyHiddenHeading");
  });
  translateTextFragments([
    ["CLV / 收盘赔率复盘", "收盘赔率复盘"],
    ["查看 CLV 等待明细", "查看收盘赔率等待明细"],
    ["token 消耗", "用量"],
  ]);
}

function translateTextFragments(pairs) {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = [];
  let node;
  while ((node = walker.nextNode())) nodes.push(node);
  nodes.forEach((textNode) => {
    let text = textNode.nodeValue;
    pairs.forEach(([from, to]) => {
      if (text.includes(from)) text = text.split(from).join(to);
    });
    if (text !== textNode.nodeValue) textNode.nodeValue = text;
  });
}
function runUnifiedUiPolishPass() {
  installFinalAuxiliaryRepairs();
  translateAllUserFacingNoise();
  translateResultPageLabels();
  repairBrokenDenseFolds();
  installOptimizerResultPolish();
  hideOptimizerSecondaryHeadings();
  polishLowFrequencyPages();
}

function installUnifiedUiPolishLoop() {
  if (window.__jcEdgeUnifiedPolishInstalled) return;
  window.__jcEdgeUnifiedPolishInstalled = true;
  runUnifiedUiPolishPass();
  window.setInterval(runUnifiedUiPolishPass, 1200);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", installUnifiedUiPolishLoop, { once: true });
} else {
  installUnifiedUiPolishLoop();
}

function foldLowFrequencyDensePanels() {
  const foldTargets = [
    ["traderReviewBest", "查看组合审核明细"],
    ["credibilityMissing", "查看缺失与部分覆盖明细"],
    ["jsonOutput", "查看原始明细内容"],
  ];
  foldTargets.forEach(([id, summary]) => {
    const box = qs(`#${id}`);
    if (!box || box.dataset.lowFrequencyFolded === "1" || !box.innerText.trim()) return;
    const detail = document.createElement("details");
    detail.className = "detailDrawer lowFrequencyFold";
    const summaryEl = document.createElement("summary");
    summaryEl.textContent = summary;
    detail.appendChild(summaryEl);
    const inner = document.createElement("div");
    inner.className = "lowFrequencyFoldBody";
    while (box.firstChild) inner.appendChild(box.firstChild);
    detail.appendChild(inner);
    box.appendChild(detail);
    box.dataset.lowFrequencyFolded = "1";
  });
}

function repairLowFrequencyDensePanels() {
  ["traderReviewBest", "credibilityMissing", "jsonOutput"].forEach((id) => {
    const box = qs(`#${id}`);
    if (!box) return;
    if (box.dataset.lowFrequencyFolded === "1" && !box.querySelector(".lowFrequencyFold") && box.innerText.trim()) {
      delete box.dataset.lowFrequencyFolded;
    }
  });
  foldLowFrequencyDensePanels();
}

function polishLowFrequencyPages() {
  repairLowFrequencyDensePanels();
  translateAllUserFacingNoise();
  translateResultPageLabels();
}
// Unified by runUnifiedUiPolishPass().

function removeTodayPrimaryPath() {
  const view = qs("#view-today");
  if (!view) return;
  view.querySelectorAll(".todayPrimaryPath").forEach((node) => node.remove());
}

function installFinalUsabilityPass() {
  removeTodayPrimaryPath();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", installFinalUsabilityPass, { once: true });
} else {
  installFinalUsabilityPass();
}

// Phase 2-S UX hotfix: show progress while refreshing combo audit.
(function comboAuditProgressEnhancement() {
  if (window.__jcEdgeComboAuditProgressInstalled) return;
  window.__jcEdgeComboAuditProgressInstalled = true;
  const STEPS = [
    "读取组合候选",
    "检查相关性",
    "审查同方向集中",
    "套用可信度门控",
    "生成组合结论",
  ];

  function ensureHost() {
    let host = document.querySelector("#comboAuditProgressHost");
    if (host) return host;
    host = document.createElement("div");
    host.id = "comboAuditProgressHost";
    host.className = "comboAuditProgressHost";
    const anchor = document.querySelector("#main") || document.querySelector("main") || document.body;
    anchor.prepend(host);
    return host;
  }

  function render(stepIndex, percent) {
    const safeStep = Math.max(0, Math.min(stepIndex, STEPS.length - 1));
    const host = ensureHost();
    host.innerHTML = `
      <section class="comboAuditProgress" style="--combo-progress:${percent}%">
        <div class="comboAuditProgress__top">
          <span>组合审核</span>
          <strong>${STEPS[safeStep]}</strong>
          <em>${Math.round(percent)}%</em>
        </div>
        <div class="comboAuditProgress__rail" aria-hidden="true">
          <i></i><b></b><u></u>
        </div>
        <div class="comboAuditProgress__steps">
          ${STEPS.map((label, index) => `<span class="${index < safeStep ? "isDone" : index === safeStep ? "isActive" : ""}">${index + 1}. ${label}</span>`).join("")}
        </div>
      </section>
    `;
  }

  function hideSoon(delay = 650) {
    window.setTimeout(() => {
      const host = document.querySelector("#comboAuditProgressHost");
      if (host) host.innerHTML = "";
    }, delay);
  }

  function startComboAuditProgress() {
    if (window.__jcEdgeComboAuditProgressTimer) {
      window.clearInterval(window.__jcEdgeComboAuditProgressTimer);
    }
    let tick = 0;
    render(0, 8);
    window.__jcEdgeComboAuditProgressTimer = window.setInterval(() => {
      tick += 1;
      const percent = Math.min(96, 8 + tick * 13);
      const stepIndex = Math.min(STEPS.length - 1, Math.floor((percent / 100) * STEPS.length));
      render(stepIndex, percent);
      if (percent >= 96) {
        window.clearInterval(window.__jcEdgeComboAuditProgressTimer);
        window.__jcEdgeComboAuditProgressTimer = null;
        render(STEPS.length - 1, 100);
        hideSoon(900);
      }
    }, 420);
  }

  document.addEventListener("click", (event) => {
    const button = event.target && event.target.closest ? event.target.closest("button, a, [role='button']") : null;
    if (!button) return;
    const text = (button.textContent || "").replace(/\s+/g, "");
    const target = `${button.getAttribute("data-tab") || ""}${button.getAttribute("href") || ""}${button.id || ""}${button.className || ""}`;
    if (text.includes("组合审核") || text.includes("查看被拒") || text.includes("生成今日观察") || /best-parlay|combo|parlay/i.test(target)) {
      startComboAuditProgress();
    }
  }, true);
})();

// Phase 2-S UX hotfix v2: fetch-driven combo/optimizer progress overlay.
(function comboAuditFetchProgressOverlay() {
  if (window.__jcEdgeComboAuditFetchProgressInstalled) return;
  window.__jcEdgeComboAuditFetchProgressInstalled = true;
  const WATCHED = [
    "/api/view/optimizer",
    "/api/view/best-parlay",
    "/api/view/trader-review",
    "/api/audit/credibility",
    "/api/audit/professional-model-score",
    "/api/view/daily-decision-board",
  ];
  const STEPS = [
    [8, "启动组合审核", "读取本地快照和候选池"],
    [26, "核对玩法分布", "检查胜平负、让球、比分和总进球是否过度集中"],
    [44, "计算组合质量", "评估赔率、模型概率、EV、Edge 和相关性"],
    [63, "执行纪律门控", "判断是否只保留纸面候选或允许进入组合观察"],
    [82, "生成解释", "整理入选原因、拒绝原因和下一步复核点"],
    [96, "等待页面更新", "接口已返回，正在渲染结果"],
  ];
  let activeCount = 0;
  let timer = null;
  let startedAt = 0;

  function shouldWatch(input) {
    const url = typeof input === "string" ? input : (input && input.url ? input.url : "");
    return WATCHED.some((item) => String(url).includes(item));
  }

  function ensureOverlay() {
    let overlay = document.querySelector("#comboAuditFetchOverlay");
    if (overlay) return overlay;
    overlay = document.createElement("aside");
    overlay.id = "comboAuditFetchOverlay";
    overlay.className = "comboAuditFetchOverlay";
    overlay.setAttribute("aria-live", "polite");
    document.body.appendChild(overlay);
    return overlay;
  }

  function stepFor(percent) {
    let current = STEPS[0];
    for (const step of STEPS) {
      if (percent >= step[0]) current = step;
    }
    return current;
  }

  function render(percent, done = false, failed = false) {
    const overlay = ensureOverlay();
    const safe = Math.max(0, Math.min(100, Math.round(percent)));
    const current = failed ? [safe, "本次未完成", "接口返回较慢或页面未拿到完整结果"] : done ? [100, "组合审核完成", "结果已写入页面，可以继续看候选与拒绝原因"] : stepFor(safe);
    overlay.classList.add("isVisible");
    overlay.innerHTML = `
      <div class="comboAuditFetchCard ${done ? "isDone" : ""} ${failed ? "isFailed" : ""}" style="--audit-progress:${safe}%">
        <div class="comboAuditFetchHeader">
          <span>COMBO AUDIT</span>
          <strong>${current[1]}</strong>
          <em>${safe}%</em>
        </div>
        <div class="comboAuditFetchRail" aria-hidden="true"><i></i><b></b><u></u></div>
        <p>${current[2]}</p>
        <div class="comboAuditFetchDots" aria-hidden="true">
          ${STEPS.slice(0, 5).map((step) => `<i class="${safe >= step[0] ? "isOn" : ""}"></i>`).join("")}
        </div>
      </div>
    `;
  }

  function start() {
    activeCount += 1;
    startedAt = Date.now();
    if (timer) window.clearInterval(timer);
    render(8);
    timer = window.setInterval(() => {
      const elapsed = Date.now() - startedAt;
      const percent = Math.min(94, 8 + Math.floor(elapsed / 180));
      render(percent);
    }, 220);
  }

  function finish(ok = true) {
    activeCount = Math.max(0, activeCount - 1);
    if (activeCount > 0) return;
    if (timer) {
      window.clearInterval(timer);
      timer = null;
    }
    render(ok ? 100 : 88, ok, !ok);
    window.setTimeout(() => {
      const overlay = document.querySelector("#comboAuditFetchOverlay");
      if (overlay) overlay.classList.remove("isVisible");
    }, ok ? 1800 : 2600);
  }

  const originalFetch = window.fetch;
  if (typeof originalFetch === "function") {
    window.fetch = function patchedComboAuditFetch(input, init) {
      if (!shouldWatch(input)) return originalFetch.apply(this, arguments);
      start();
      return originalFetch.apply(this, arguments).then((response) => {
        finish(response && response.ok !== false);
        return response;
      }).catch((error) => {
        finish(false);
        throw error;
      });
    };
  }

  document.addEventListener("click", (event) => {
    const target = event.target && event.target.closest ? event.target.closest("button, a, [role='button'], .pill, .nav-pill") : null;
    if (!target) return;
    const text = (target.textContent || "").replace(/\s+/g, "");
    if (/组合审核|赛前优化|生成今日观察|模型体检|被拒/.test(text)) {
      start();
      window.setTimeout(() => finish(true), 2400);
    }
  }, true);
})();

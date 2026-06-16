window.FootballComponents = (() => {
  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function cards(items = []) {
    if (!items.length) return '<div class="empty">暂无卡片数据</div>';
    return `<div class="cardGrid">${items.map((item) => `
      <article class="metricCard">
        <span>${escapeHtml(item.label)}</span>
        <strong>${escapeHtml(item.value ?? "N/A")}</strong>
        <p>${escapeHtml(item.help || "")}</p>
      </article>`).join("")}</div>`;
  }

  function table(rows = [], columns = []) {
    if (!rows.length) return '<div class="empty">暂无表格数据</div>';
    return `<div class="tableWrap"><table><thead><tr>${columns.map((col) => `<th>${escapeHtml(col.label)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${columns.map((col) => `<td>${escapeHtml(valueFor(row, col.key))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  }

  function valueFor(row, key) {
    const value = key.split(".").reduce((acc, part) => (acc && acc[part] !== undefined ? acc[part] : ""), row);
    if (Array.isArray(value)) return value.map((item) => typeof item === "object" ? Object.values(item).filter(Boolean).join(" / ") : item).join("；");
    if (value && typeof value === "object") return JSON.stringify(value);
    return value;
  }

  function list(items = []) {
    if (!items.length) return '<p class="empty">暂无说明</p>';
    return `<ul class="noteList">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  function warnings(items = []) {
    if (!items.length) return '<p class="okText">当前没有新的提醒。</p>';
    return `<ul class="warningList">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  function badge(value) {
    const normalized = String(value || "unknown").toLowerCase();
    return `<span class="riskBadge risk-${escapeHtml(normalized)}">${escapeHtml(value || "未分级")}</span>`;
  }

  return { escapeHtml, cards, table, list, warnings, badge };
})();

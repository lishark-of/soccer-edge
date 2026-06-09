const apiBaseInput = document.querySelector("#apiBase");
const statusText = document.querySelector("#statusText");
const jsonOutput = document.querySelector("#jsonOutput");
const warningsList = document.querySelector("#warningsList");

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
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

async function request(path, params = {}) {
  statusText.textContent = "Loading";
  try {
    const response = await fetch(endpoint(path, params));
    const payload = await response.json();
    render(payload);
    statusText.textContent = payload.ok ? "OK" : "Error";
  } catch (error) {
    render({ ok: false, error: { code: "connection_error", message: String(error) }, warnings: ["API server may not be running"] });
    statusText.textContent = "Offline";
  }
}

function render(payload) {
  jsonOutput.textContent = JSON.stringify(payload, null, 2);
  const warnings = payload.warnings || payload.data?.warnings || [];
  warningsList.innerHTML = "";
  if (!warnings.length) {
    warningsList.innerHTML = "<li>None</li>";
    return;
  }
  warnings.forEach((warning) => {
    const item = document.createElement("li");
    item.textContent = warning;
    warningsList.appendChild(item);
  });
}

document.querySelector("#healthBtn").addEventListener("click", () => request("/api/health"));
document.querySelector("#analyzeBtn").addEventListener("click", () => request("/api/analyze", { provider: value("#provider"), date: value("#date") }));
document.querySelector("#backtestBtn").addEventListener("click", () => request("/api/backtest", { historical_data: value("#historicalData") }));
document.querySelector("#importBtn").addEventListener("click", () => request("/api/import/preview", { input: value("#importInput"), adapter: "auto" }));
document.querySelector("#calibrationBtn").addEventListener("click", () => request("/api/calibration/validate", { path: value("#calibrationPath") }));
document.querySelector("#clearBtn").addEventListener("click", () => render({}));

request("/api/health");

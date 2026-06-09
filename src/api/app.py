from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.application import build_analysis_payload, build_match_odds_payload, build_matches_payload, build_odds_history_payload, default_target_date


APP_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>football-jc-analysis Preview</title>
  <style>
    :root {
      --bg: #f5efe1;
      --panel: rgba(255,255,255,0.88);
      --ink: #192126;
      --muted: #6f756e;
      --line: rgba(25,33,38,0.1);
      --accent: #0d7a5f;
      --accent-soft: #d7f1e9;
      --danger: #9f3a2d;
      --gold: #b88723;
      --shadow: 0 22px 60px rgba(25,33,38,0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "PingFang SC", "Noto Sans SC", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(184,135,35,0.16), transparent 32%),
        radial-gradient(circle at bottom right, rgba(13,122,95,0.18), transparent 30%),
        linear-gradient(180deg, #fbf7ee 0%, var(--bg) 100%);
    }
    .shell {
      max-width: 1220px;
      margin: 0 auto;
      padding: 36px 20px 48px;
    }
    .hero {
      display: grid;
      gap: 16px;
      margin-bottom: 24px;
    }
    .eyebrow {
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--muted);
      font-size: 12px;
    }
    h1 {
      margin: 0;
      font-size: clamp(32px, 5vw, 56px);
      line-height: 0.96;
      font-weight: 700;
    }
    .hero p {
      margin: 0;
      max-width: 760px;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.7;
    }
    .grid {
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 20px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }
    .controls {
      padding: 20px;
      position: sticky;
      top: 20px;
    }
    .controls h2, .content h2 {
      margin: 0 0 14px;
      font-size: 18px;
    }
    label {
      display: block;
      margin: 0 0 8px;
      font-size: 13px;
      color: var(--muted);
    }
    input, select, button {
      width: 100%;
      border-radius: 14px;
      border: 1px solid var(--line);
      padding: 12px 14px;
      font-size: 15px;
      background: white;
      color: var(--ink);
    }
    button {
      margin-top: 8px;
      border: 0;
      background: linear-gradient(135deg, #0d7a5f 0%, #1aa179 100%);
      color: white;
      font-weight: 600;
      cursor: pointer;
      transition: transform 160ms ease, box-shadow 160ms ease;
      box-shadow: 0 14px 26px rgba(13,122,95,0.24);
    }
    button:hover { transform: translateY(-1px); }
    .secondary {
      background: white;
      color: var(--ink);
      border: 1px solid var(--line);
      box-shadow: none;
    }
    .stack { display: grid; gap: 14px; }
    .content {
      padding: 22px;
      display: grid;
      gap: 18px;
    }
    .stat-row {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }
    .stat {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
    }
    .stat .label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }
    .stat .value {
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
    }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 13px;
      font-weight: 600;
    }
    .pill.warn {
      background: rgba(159,58,45,0.1);
      color: var(--danger);
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
    }
    .card {
      padding: 16px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.82);
    }
    .card h3 {
      margin: 0 0 8px;
      font-size: 16px;
    }
    .meta {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }
    .metric {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin-top: 8px;
      font-size: 13px;
    }
    .risk-low { color: var(--accent); }
    .risk-medium { color: var(--gold); }
    .risk-high, .risk-very_high { color: var(--danger); }
    .note-list {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.7;
      font-size: 14px;
    }
    .empty {
      padding: 18px;
      border-radius: 18px;
      border: 1px dashed var(--line);
      color: var(--muted);
      background: rgba(255,255,255,0.5);
    }
    @media (max-width: 960px) {
      .grid { grid-template-columns: 1fr; }
      .controls { position: static; }
      .stat-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="hero">
      <div class="eyebrow">Football JC Analysis</div>
      <h1>竞彩足球概率推演与组合候选预览页</h1>
      <p>这不是投注平台，而是一块本地研究看板。它会展示比赛列表、去水概率、模型概率、正期望候选和组合风险，并在真实 provider 不稳定时自动降级到 mock 数据。</p>
    </div>

    <div class="grid">
      <div class="panel controls">
        <h2>参数</h2>
        <div class="stack">
          <div>
            <label for="dateInput">目标日期</label>
            <input id="dateInput" type="date" />
          </div>
          <div>
            <label for="providerInput">数据入口</label>
            <select id="providerInput">
              <option value="auto">auto fallback</option>
              <option value="mock">mock</option>
              <option value="sporttery">sporttery</option>
            </select>
          </div>
          <button id="runBtn">生成预览</button>
          <button class="secondary" id="xlsxBtn">导出 XLSX</button>
        </div>
      </div>

      <div class="panel content">
        <div class="stat-row" id="stats"></div>
        <div class="pill-row" id="pills"></div>
        <section>
          <h2>单关候选</h2>
          <div class="cards" id="singleCards"></div>
        </section>
        <section>
          <h2>2串1 候选</h2>
          <div class="cards" id="parlayCards"></div>
        </section>
        <section>
          <h2>比赛列表</h2>
          <div class="cards" id="matchCards"></div>
        </section>
        <section>
          <h2>说明与风险</h2>
          <ul class="note-list" id="notes"></ul>
        </section>
      </div>
    </div>
  </div>

  <script>
    const today = new Date();
    const tomorrow = new Date(today.getTime() + 86400000);
    document.getElementById("dateInput").value = tomorrow.toISOString().slice(0, 10);

    const statsEl = document.getElementById("stats");
    const pillsEl = document.getElementById("pills");
    const singleCardsEl = document.getElementById("singleCards");
    const parlayCardsEl = document.getElementById("parlayCards");
    const matchCardsEl = document.getElementById("matchCards");
    const notesEl = document.getElementById("notes");

    const formatPct = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`;
    const formatNum = (value) => Number(value || 0).toFixed(3);

    function cardHTML(title, meta, metrics) {
      const metricHtml = metrics.map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`).join("");
      return `<article class="card"><h3>${title}</h3><div class="meta">${meta}</div>${metricHtml}</article>`;
    }

    function renderStats(payload) {
      const stats = [
        ["分析场次", payload.matches_analyzed ?? 0],
        ["单关候选", (payload.single_candidates || []).length],
        ["2串1 候选", (payload.parlay_2x1_candidates || []).length],
        ["3串1 候选", (payload.parlay_3x1_candidates || []).length],
      ];
      statsEl.innerHTML = stats.map(([label, value]) => `<div class="stat"><div class="label">${label}</div><div class="value">${value}</div></div>`).join("");
    }

    function renderPills(payload) {
      const items = [
        `<span class="pill">requested: ${payload.provider_requested}</span>`,
        `<span class="pill">used: ${payload.provider_used}</span>`,
        payload.fallback_used ? `<span class="pill warn">fallback to mock</span>` : "",
      ];
      for (const warning of (payload.provider_warnings || [])) {
        items.push(`<span class="pill warn">${warning}</span>`);
      }
      pillsEl.innerHTML = items.join("");
    }

    function renderSingles(payload) {
      const singles = payload.single_candidates || [];
      if (!singles.length) {
        singleCardsEl.innerHTML = `<div class="empty">当前没有满足阈值的单关候选。</div>`;
        return;
      }
      singleCardsEl.innerHTML = singles.map((item) => {
        const riskClass = `risk-${item.risk_level}`;
        return cardHTML(
          `${item.match_no} ${item.home_team} vs ${item.away_team}`,
          `${item.league} · ${item.play_type} ${item.outcome_label} · <span class="${riskClass}">${item.risk_level}</span>`,
          [
            ["赔率", item.odds],
            ["去水概率", formatPct(item.fair_prob)],
            ["模型概率", formatPct(item.model_prob)],
            ["Edge", formatNum(item.edge)],
            ["EV", formatNum(item.ev)],
            ["用途", item.recommended_use],
          ],
        );
      }).join("");
    }

    function renderParlays(payload) {
      const parlays = payload.parlay_2x1_candidates || [];
      if (!parlays.length) {
        parlayCardsEl.innerHTML = `<div class="empty">当前没有满足约束的 2串1 组合。</div>`;
        return;
      }
      parlayCardsEl.innerHTML = parlays.map((item) => {
        const legs = item.legs.map((leg) => `${leg.match_no} ${leg.outcome_label} @ ${leg.odds}`).join("<br/>");
        return cardHTML(
          `${item.pass_type} · ${item.risk_level}`,
          legs,
          [
            ["组合赔率", item.combined_odds],
            ["命中概率", formatPct(item.hit_probability)],
            ["市场概率", formatPct(item.market_probability)],
            ["组合EV", formatNum(item.ev)],
            ["总投入", item.payout.total_stake],
            ["理论回报", item.payout.theoretical_max_payout],
          ],
        );
      }).join("");
    }

    function renderMatches(payload) {
      const matches = payload.matches || [];
      if (!matches.length) {
        matchCardsEl.innerHTML = `<div class="empty">当前 provider 没有返回比赛列表。</div>`;
        return;
      }
      matchCardsEl.innerHTML = matches.map((match) => {
        return cardHTML(
          `${match.match_no} ${match.home_team} vs ${match.away_team}`,
          `${match.league} · ${match.kickoff_at}`,
          [
            ["单关", match.supports_single ? "支持" : "不支持"],
            ["相关组", match.correlation_group || "-"],
            ["home_rating", (match.metadata || {}).home_rating ?? "-"],
            ["away_rating", (match.metadata || {}).away_rating ?? "-"],
          ],
        );
      }).join("");
    }

    function renderNotes(payload) {
      const notes = [
        ...(payload.disclaimers || []),
        ...(payload.warnings || []),
      ];
      notesEl.innerHTML = notes.map((item) => `<li>${item}</li>`).join("");
    }

    async function loadPreview() {
      const date = document.getElementById("dateInput").value;
      const provider = document.getElementById("providerInput").value;
      const [analysisResp, matchesResp] = await Promise.all([
        fetch(`/api/analysis?date=${encodeURIComponent(date)}&provider=${encodeURIComponent(provider)}`),
        fetch(`/api/matches?date=${encodeURIComponent(date)}&provider=${encodeURIComponent(provider)}`),
      ]);
      const analysisPayload = await analysisResp.json();
      const matchesPayload = await matchesResp.json();
      renderStats(analysisPayload);
      renderPills(analysisPayload);
      renderSingles(analysisPayload);
      renderParlays(analysisPayload);
      renderMatches(matchesPayload);
      renderNotes(analysisPayload);
    }

    document.getElementById("runBtn").addEventListener("click", () => {
      loadPreview().catch((error) => {
        notesEl.innerHTML = `<li>页面加载失败：${error}</li>`;
      });
    });

    document.getElementById("xlsxBtn").addEventListener("click", () => {
      const date = document.getElementById("dateInput").value;
      const provider = document.getElementById("providerInput").value;
      window.open(`/api/export?date=${encodeURIComponent(date)}&provider=${encodeURIComponent(provider)}&format=xlsx`, "_blank");
    });

    loadPreview();
  </script>
</body>
</html>
"""


def phase_two_notice() -> dict[str, str]:
    return {
        "status": "preview_ready",
        "message": "Local web preview is available. Run `python3 -m src.api.app`.",
    }


class PreviewHandler(BaseHTTPRequestHandler):
    server_version = "football-jc-analysis/0.2"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(APP_HTML)
            return
        if parsed.path == "/api/health":
            self._send_json({"status": "ok", "service": "football-jc-analysis-preview"})
            return
        if parsed.path == "/api/matches":
            params = self._params(parsed.query)
            payload = build_matches_payload(params.get("date"), params.get("provider", "auto"))
            self._send_json(payload)
            return
        if parsed.path == "/api/analysis":
            params = self._params(parsed.query)
            payload = build_analysis_payload(params.get("date"), params.get("provider", "auto"))
            self._send_json(payload)
            return
        if parsed.path == "/api/export":
            params = self._params(parsed.query)
            export_format = params.get("format", "xlsx")
            payload = build_analysis_payload(params.get("date"), params.get("provider", "auto"), export_format=export_format)
            export_file = payload.get("export_file")
            if not export_file:
                self._send_json({"error": "export file not created"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._send_file(Path(str(export_file)))
            return
        if parsed.path.startswith("/api/match/") and parsed.path.endswith("/odds"):
            params = self._params(parsed.query)
            match_id = parsed.path.split("/")[3]
            payload = build_match_odds_payload(match_id, params.get("date"), params.get("provider", "auto"))
            self._send_json(payload)
            return
        if parsed.path.startswith("/api/match/") and parsed.path.endswith("/odds-history"):
            params = self._params(parsed.query)
            match_id = parsed.path.split("/")[3]
            payload = build_odds_history_payload(match_id, params.get("date"), params.get("provider", "auto"))
            self._send_json(payload)
            return
        self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args) -> None:
        return

    def _params(self, query: str) -> dict[str, str]:
        parsed = parse_qs(query)
        return {key: values[-1] for key, values in parsed.items() if values}

    def _send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        body = path.read_bytes()
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if path.suffix.lower() == ".csv":
            content_type = "text/csv; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
        self.end_headers()
        self.wfile.write(body)


def run_preview_server(host: str = "127.0.0.1", port: int = 8011) -> None:
    server = ThreadingHTTPServer((host, port), PreviewHandler)
    print(f"Preview server running on http://{host}:{port}")
    server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="football-jc-analysis local preview server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8011)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_preview_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

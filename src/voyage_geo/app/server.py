"""ASGI server for optional GUI/app mode."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Route

from voyage_geo.app.jobs import JobStore, get_run_details, list_runs


def create_app(output_dir: str = "./data/runs", cwd: str | None = None) -> Starlette:
    store = JobStore(output_dir=output_dir, cwd=cwd)

    async def home(_: Request) -> HTMLResponse:
        return HTMLResponse(_index_html())

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    async def api_jobs(request: Request) -> JSONResponse:
        limit = int(request.query_params.get("limit", "100"))
        return JSONResponse([j.__dict__ for j in store.list_jobs(limit=limit)])

    async def api_job(request: Request) -> JSONResponse:
        job_id = request.path_params["job_id"]
        try:
            return JSONResponse(store.get_job(job_id).__dict__)
        except KeyError:
            return JSONResponse({"detail": "job not found"}, status_code=404)

    async def api_job_logs(request: Request) -> JSONResponse:
        job_id = request.path_params["job_id"]
        tail = int(request.query_params.get("tail", "200"))
        try:
            return JSONResponse({"job_id": job_id, "logs": store.tail_logs(job_id, tail=tail)})
        except KeyError:
            return JSONResponse({"detail": "job not found"}, status_code=404)

    async def api_job_cancel(request: Request) -> JSONResponse:
        job_id = request.path_params["job_id"]
        if not store.cancel_job(job_id):
            return JSONResponse({"detail": "job not found or not running"}, status_code=404)
        return JSONResponse({"ok": True})

    async def api_run_job(request: Request) -> JSONResponse:
        req = await request.json()
        brand = str(req.get("brand", "")).strip()
        if not brand:
            return JSONResponse({"detail": "brand is required"}, status_code=400)
        args = [
            "run",
            "-b",
            brand,
            "-p",
            str(req.get("providers", "chatgpt,gemini,claude,perplexity-or,deepseek,grok,llama,mistral,cohere,qwen,kimi,glm")),
            "-q",
            str(int(req.get("queries", 20))),
            "-i",
            str(int(req.get("iterations", 1))),
            "-f",
            str(req.get("formats", "html,json")),
            "-c",
            str(int(req.get("concurrency", 10))),
            "-o",
            output_dir,
        ]
        if req.get("website"):
            args += ["-w", str(req["website"])]
        if req.get("processing_provider"):
            args += ["--processing-provider", str(req["processing_provider"])]
        if req.get("processing_model"):
            args += ["--processing-model", str(req["processing_model"])]
        if req.get("as_of_date"):
            args += ["--as-of-date", str(req["as_of_date"])]
        if req.get("resume"):
            args += ["--resume", str(req["resume"])]
        if req.get("stop_after"):
            args += ["--stop-after", str(req["stop_after"])]
        if bool(req.get("no_interactive", True)):
            args += ["--no-interactive"]

        job = store.create_job(kind="run", args=args)
        return JSONResponse(job.__dict__)

    async def api_leaderboard_job(request: Request) -> JSONResponse:
        req = await request.json()
        category = str(req.get("category", "")).strip()
        if not category:
            return JSONResponse({"detail": "category is required"}, status_code=400)
        args = [
            "leaderboard",
            category,
            "-p",
            str(req.get("providers", "chatgpt,gemini,claude,perplexity-or,deepseek,grok,llama,mistral,cohere,qwen,kimi,glm")),
            "-q",
            str(int(req.get("queries", 20))),
            "-f",
            str(req.get("formats", "html,json")),
            "-c",
            str(int(req.get("concurrency", 10))),
            "--max-brands",
            str(int(req.get("max_brands", 50))),
            "-o",
            output_dir,
        ]
        if req.get("processing_provider"):
            args += ["--processing-provider", str(req["processing_provider"])]
        if req.get("processing_model"):
            args += ["--processing-model", str(req["processing_model"])]
        if req.get("resume"):
            args += ["--resume", str(req["resume"])]
        if req.get("stop_after"):
            args += ["--stop-after", str(req["stop_after"])]
        job = store.create_job(kind="leaderboard", args=args)
        return JSONResponse(job.__dict__)

    async def api_runs(request: Request) -> JSONResponse:
        limit = int(request.query_params.get("limit", "100"))
        return JSONResponse(list_runs(output_dir=output_dir, limit=limit))

    async def api_run_details(request: Request) -> JSONResponse:
        run_id = request.path_params["run_id"]
        try:
            return JSONResponse(get_run_details(output_dir=output_dir, run_id=run_id))
        except FileNotFoundError:
            return JSONResponse({"detail": "run not found"}, status_code=404)

    async def api_report_path(request: Request) -> JSONResponse:
        run_id = request.path_params["run_id"]
        details = get_run_details(output_dir=output_dir, run_id=run_id)
        report_path = Path(details["paths"]["report_html"])
        return JSONResponse({
            "run_id": run_id,
            "exists": report_path.exists(),
            "path": str(report_path),
        })

    async def run_report_html(request: Request):
        run_id = request.path_params["run_id"]
        details = get_run_details(output_dir=output_dir, run_id=run_id)
        report_path = Path(details["paths"]["report_html"])
        if not report_path.exists():
            # Lazily generate HTML report when the run only has non-HTML artifacts.
            if run_id.startswith("lb-"):
                cmd = [
                    sys.executable,
                    "-m",
                    "voyage_geo",
                    "leaderboard-report",
                    "--run-id",
                    run_id,
                    "--formats",
                    "html,json",
                    "--output-dir",
                    output_dir,
                ]
            else:
                cmd = [
                    sys.executable,
                    "-m",
                    "voyage_geo",
                    "report",
                    "--run-id",
                    run_id,
                    "--formats",
                    "html,json",
                    "--output-dir",
                    output_dir,
                ]
            subprocess.run(cmd, capture_output=True, text=True)

        if not report_path.exists():
            return PlainTextResponse("Report not found", status_code=404)
        return FileResponse(path=str(report_path), media_type="text/html")

    return Starlette(
        routes=[
            Route("/", home),
            Route("/api/health", health),
            Route("/api/jobs", api_jobs),
            Route("/api/jobs/run", api_run_job, methods=["POST"]),
            Route("/api/jobs/leaderboard", api_leaderboard_job, methods=["POST"]),
            Route("/api/jobs/{job_id}", api_job),
            Route("/api/jobs/{job_id}/logs", api_job_logs),
            Route("/api/jobs/{job_id}/cancel", api_job_cancel, methods=["POST"]),
            Route("/api/runs", api_runs),
            Route("/api/runs/{run_id}", api_run_details),
            Route("/api/runs/{run_id}/report", api_report_path),
            Route("/runs/{run_id}/report", run_report_html),
        ]
    )


def _index_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Voyage GEO Control Center</title>
  <style>
    :root {
      --bg: #f3f6f6;
      --panel: #ffffff;
      --line: #dde6e5;
      --ink: #1b2d2b;
      --muted: #6c7f7d;
      --teal: #0f766e;
      --orange: #c2410c;
      --shadow: 0 10px 26px rgba(16, 24, 40, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Manrope", "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 0% 0%, #fff7ed 0, transparent 40%),
        radial-gradient(circle at 100% 0%, #ecfeff 0, transparent 40%),
        var(--bg);
    }
    .wrap { max-width: 1260px; margin: 0 auto; padding: 24px 18px 40px; }
    .header {
      display: flex; justify-content: space-between; align-items: end; gap: 10px;
      margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--line);
    }
    .title { margin: 0; font-size: 35px; letter-spacing: -0.03em; }
    .subtitle { color: var(--muted); font-size: 14px; margin-top: 4px; }
    .layout { display: grid; gap: 12px; grid-template-columns: 1fr 1fr; }
    .card {
      background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
      box-shadow: var(--shadow); padding: 14px;
    }
    .card h3 {
      margin: 0 0 10px; font-size: 12px; letter-spacing: 0.12em;
      text-transform: uppercase; color: var(--muted);
    }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
    label { font-size: 11px; color: var(--muted); display: block; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.06em; }
    input, select {
      width: 100%; border: 1px solid var(--line); border-radius: 10px; background: #fff;
      padding: 9px 10px; font: inherit;
    }
    .check-grid {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      background: #fff;
      max-height: 126px;
      overflow: auto;
    }
    .check-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      background: #f8fbfb;
      border: 1px solid #e6efee;
      border-radius: 8px;
      padding: 4px 6px;
    }
    .check-item input {
      width: auto;
      margin: 0;
      padding: 0;
      border: 0;
    }
    .helper { font-size: 11px; color: var(--muted); margin-top: 3px; }
    .actions { display: flex; gap: 8px; margin-top: 6px; }
    button {
      border: 0; border-radius: 10px; color: #fff; cursor: pointer;
      padding: 10px 14px; font-weight: 700; letter-spacing: 0.01em;
    }
    .btn-primary { background: linear-gradient(90deg, #0f766e, #0d9488); }
    .btn-alt { background: linear-gradient(90deg, #c2410c, #ea580c); }
    .stack { display: grid; gap: 12px; margin-top: 12px; }
    .split { display: grid; grid-template-columns: 2fr 1fr; gap: 12px; }
    .sticky { position: sticky; top: 12px; align-self: start; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th {
      text-align: left; color: var(--muted); font-size: 11px; text-transform: uppercase;
      letter-spacing: 0.08em; padding: 8px 6px; border-bottom: 1px solid var(--line);
    }
    td { padding: 8px 6px; border-bottom: 1px solid #edf2f2; }
    tr.pickable:hover { background: #f1f9f8; cursor: pointer; }
    .mono { font-family: "JetBrains Mono", "SF Mono", Menlo, monospace; font-size: 11px; }
    pre {
      margin: 0; background: #0f172a; color: #d1fae5; border-radius: 10px; padding: 12px;
      max-height: 260px; overflow: auto; font-size: 11px;
    }
    .status-pill {
      border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px; font-size: 11px;
      background: #fafefe;
    }
    @media (max-width: 980px) {
      .layout { grid-template-columns: 1fr; }
      .row { grid-template-columns: 1fr; }
      .title { font-size: 29px; }
      .split { grid-template-columns: 1fr; }
      .sticky { position: static; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div>
        <h1 class="title">Voyage GEO Control Center</h1>
        <div class="subtitle">Unified GUI for Claude/Codex + local CLI job execution.</div>
      </div>
      <div class="status-pill">Auto-refresh: 4s</div>
    </div>

    <div class="layout">
      <div class="card">
        <h3>Start GEO Run</h3>
        <div class="row">
          <div>
            <label>Brand</label>
            <input id="brand" placeholder="Brand name" />
          </div>
          <div>
            <label>Website</label>
            <input id="website" placeholder="https://example.com (optional)" />
          </div>
        </div>
        <div class="row">
          <div>
            <label>Models</label>
            <div id="providersBox" class="check-grid"></div>
            <div class="helper">Select AI models to run against</div>
          </div>
          <div>
            <label>As-of Date</label>
            <input id="asof" placeholder="YYYY-MM-DD (optional)" />
          </div>
        </div>
        <div class="row">
          <div>
            <label>Queries</label>
            <input id="queries" value="10" />
          </div>
          <div>
            <label>Formats</label>
            <input id="formats" value="html,json" />
          </div>
        </div>
        <div class="actions">
          <button class="btn-primary" onclick="startRun()">Start Run</button>
          <button class="btn-alt" onclick="refreshAll()">Refresh</button>
        </div>
      </div>

      <div class="card">
        <h3>Start Leaderboard</h3>
        <div class="row">
          <div>
            <label>Category</label>
            <input id="category" placeholder="best CRM tools" />
          </div>
          <div>
            <label>Models</label>
            <div id="lbProvidersBox" class="check-grid"></div>
          </div>
        </div>
        <div class="row">
          <div>
            <label>Queries</label>
            <input id="lbqueries" value="10" />
          </div>
          <div>
            <label>Formats</label>
            <input id="lbformats" value="html,json" />
          </div>
        </div>
        <div class="actions">
          <button class="btn-primary" onclick="startLeaderboard()">Start Leaderboard</button>
        </div>
      </div>
    </div>

    <div class="stack">
      <div class="card">
        <h3>Jobs</h3>
        <table id="jobs"></table>
      </div>
      <div class="card">
        <h3>Job Logs (latest selected)</h3>
        <pre id="logs">(select a job)</pre>
      </div>
      <div class="split">
        <div class="card">
          <h3>Past Runs</h3>
          <div class="helper" style="margin-bottom:8px;">Click a run row for details, or use Open</div>
          <table id="runs"></table>
        </div>
        <div class="card sticky">
          <h3>Run Details</h3>
          <div id="runDetails" class="helper">Select a run from the table.</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const modelOptions = [
      { id: "chatgpt", label: "ChatGPT" },
      { id: "gemini", label: "Gemini" },
      { id: "claude", label: "Claude" },
      { id: "perplexity-or", label: "Perplexity" },
      { id: "deepseek", label: "DeepSeek" },
      { id: "grok", label: "Grok" },
      { id: "llama", label: "Llama" },
      { id: "mistral", label: "Mistral" },
      { id: "cohere", label: "Cohere" },
      { id: "qwen", label: "Qwen" },
      { id: "kimi", label: "Kimi" },
      { id: "glm", label: "GLM" },
    ];
    let selectedJob = null;
    let selectedRun = null;

    function hydrateProviders(containerId, defaults) {
      const el = document.getElementById(containerId);
      el.innerHTML = modelOptions.map(m => `
        <label class="check-item">
          <input type="checkbox" value="${m.id}" ${defaults.includes(m.id) ? "checked" : ""} />
          <span>${m.label}</span>
        </label>
      `).join("");
    }

    function selectedProviders(containerId) {
      const el = document.getElementById(containerId);
      return Array.from(el.querySelectorAll('input[type="checkbox"]:checked')).map(o => o.value).join(",");
    }

    async function api(path, opts) {
      const r = await fetch(path, opts);
      if (!r.ok) throw new Error(await r.text());
      return await r.json();
    }

    async function startRun() {
      const body = {
        brand: document.getElementById("brand").value,
        website: document.getElementById("website").value || null,
        providers: selectedProviders("providersBox"),
        queries: parseInt(document.getElementById("queries").value || "10", 10),
        formats: document.getElementById("formats").value,
        as_of_date: document.getElementById("asof").value || null,
        no_interactive: true
      };
      const job = await api("/api/jobs/run", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(body)
      });
      selectedJob = job.job_id;
      refreshAll();
    }

    async function startLeaderboard() {
      const body = {
        category: document.getElementById("category").value,
        providers: selectedProviders("lbProvidersBox"),
        queries: parseInt(document.getElementById("lbqueries").value || "10", 10),
        formats: document.getElementById("lbformats").value
      };
      const job = await api("/api/jobs/leaderboard", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(body)
      });
      selectedJob = job.job_id;
      refreshAll();
    }

    function jobsTable(jobs) {
      const rows = jobs.map(j => `
        <tr class="pickable" onclick="pickJob('${j.job_id}')">
          <td class="mono">${j.job_id}</td>
          <td>${j.kind}</td>
          <td>${j.status}</td>
          <td class="mono">${j.run_id || ""}</td>
          <td>${(j.created_at || "").slice(0,19)}</td>
        </tr>`).join("");
      document.getElementById("jobs").innerHTML =
        `<tr><th>ID</th><th>Kind</th><th>Status</th><th>Run</th><th>Created</th></tr>${rows}`;
    }

    function runsTable(runs) {
      const rows = runs.map(r => `
        <tr class="pickable" onclick="pickRun('${r.run_id}')">
          <td class="mono">${r.run_id}</td>
          <td>${r.type}</td>
          <td>${r.brand || r.category || ""}</td>
          <td>${r.status}</td>
          <td>${(r.as_of_date || "").toString()}</td>
          <td><a href="/runs/${r.run_id}/report" target="_blank" rel="noopener" onclick="event.stopPropagation()">Open</a></td>
        </tr>`).join("");
      document.getElementById("runs").innerHTML =
        `<tr><th>Run ID</th><th>Type</th><th>Label</th><th>Status</th><th>As-of</th><th>Report</th></tr>${rows}`;
    }

    async function pickRun(runId) {
      selectedRun = runId;
      const data = await api(`/api/runs/${runId}`);
      const meta = data.metadata || {};
      const summary = data.summary || {};
      const score = summary.overall_score ?? data.snapshot?.overall_score ?? "—";
      const headline = summary.headline || "No summary available yet";
      const reportUrl = `/runs/${runId}/report`;
      document.getElementById("runDetails").innerHTML = `
        <div><strong>${runId}</strong></div>
        <div class="helper">Type: ${meta.type || "analysis"} | Status: ${meta.status || "—"} | As-of: ${meta.as_of_date || "—"}</div>
        <div style="margin-top:6px;"><strong>Score:</strong> ${score}</div>
        <div style="margin-top:4px;">${headline}</div>
        <div style="margin-top:8px;"><a href="${reportUrl}" target="_blank" rel="noopener">Open Report</a></div>
      `;
    }

    async function pickJob(jobId) {
      selectedJob = jobId;
      const data = await api(`/api/jobs/${jobId}/logs?tail=300`);
      document.getElementById("logs").textContent = data.logs.join("\\n");
    }

    async function refreshAll() {
      const [jobs, runs] = await Promise.all([api("/api/jobs?limit=50"), api("/api/runs?limit=50")]);
      jobsTable(jobs);
      runsTable(runs);
      if (selectedJob) {
        try { await pickJob(selectedJob); } catch (_) {}
      }
      if (selectedRun) {
        try { await pickRun(selectedRun); } catch (_) {}
      }
    }

    hydrateProviders("providersBox", ["chatgpt", "gemini", "claude"]);
    hydrateProviders("lbProvidersBox", ["chatgpt", "gemini", "claude"]);
    document.getElementById("asof").value = new Date().toISOString().slice(0, 10);
    refreshAll();
    setInterval(refreshAll, 4000);
  </script>
</body>
</html>
"""

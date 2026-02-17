"""HTML dashboard renderer for trend data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from voyage_geo.trends import build_competitor_series, collect_trend_records


def build_dashboard_payload(records: list[dict[str, Any]], compare: list[str] | None = None) -> dict[str, Any]:
    metric_series: dict[str, list[dict[str, Any]]] = {
        "overall_score": [],
        "mention_rate": [],
        "mindshare": [],
        "sentiment_score": [],
        "mindshare_gap_to_leader": [],
        "mention_rate_gap_to_leader": [],
        "share_of_voice_top5": [],
    }

    for record in records:
        rel = record.get("competitor_relative", {}) or {}
        base = {"as_of_date": record.get("as_of_date", ""), "run_id": record.get("run_id", "")}
        metric_series["overall_score"].append({**base, "value": record.get("overall_score", 0.0)})
        metric_series["mention_rate"].append({**base, "value": record.get("mention_rate", 0.0)})
        metric_series["mindshare"].append({**base, "value": record.get("mindshare", 0.0)})
        metric_series["sentiment_score"].append({**base, "value": record.get("sentiment_score", 0.0)})
        metric_series["mindshare_gap_to_leader"].append({**base, "value": rel.get("mindshare_gap_to_leader", 0.0)})
        metric_series["mention_rate_gap_to_leader"].append({**base, "value": rel.get("mention_rate_gap_to_leader", 0.0)})
        metric_series["share_of_voice_top5"].append({**base, "value": rel.get("share_of_voice_top5", 0.0)})

    competitors = build_competitor_series(records, compare)
    latest = records[-1] if records else {}
    return {
        "records": records,
        "latest": latest,
        "series": metric_series,
        "competitors": competitors,
    }


def render_dashboard_html(brand: str, payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload)
    brand_safe = json.dumps(brand)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GEO Trends Dashboard</title>
  <style>
    :root {{
      --bg: #f4efe8;
      --panel: #fffdfa;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #e8dfd3;
      --accent: #0f766e;
      --accent2: #c2410c;
      --good: #166534;
      --bad: #b91c1c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 0% 0%, #fff7ed 0%, transparent 45%),
        radial-gradient(circle at 100% 0%, #ecfeff 0%, transparent 40%),
        var(--bg);
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px 16px 40px;
    }}
    .head {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 12px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 14px;
      margin-bottom: 18px;
    }}
    .head h1 {{
      margin: 0;
      font-size: 28px;
      letter-spacing: -0.02em;
    }}
    .sub {{
      color: var(--muted);
      font-size: 13px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 18px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
    }}
    .k {{
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.07em;
      margin-bottom: 4px;
    }}
    .v {{
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    .panels {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 12px;
    }}
    .chart-wrap {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
    }}
    .chart-title {{
      margin: 0 0 8px;
      font-size: 14px;
      font-weight: 700;
    }}
    .chart {{
      width: 100%;
      height: 220px;
      display: block;
      background: linear-gradient(180deg, #ffffff 0%, #fff9f1 100%);
      border-radius: 8px;
      border: 1px solid #f0e6d8;
    }}
    .legend {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 8px;
      font-size: 12px;
      color: var(--muted);
    }}
    .dot {{
      width: 9px;
      height: 9px;
      border-radius: 999px;
      display: inline-block;
      margin-right: 4px;
      vertical-align: middle;
    }}
    .comp-list {{
      display: grid;
      gap: 8px;
    }}
    .row {{
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 8px;
      align-items: center;
      font-size: 13px;
      border-bottom: 1px dashed #eee1d0;
      padding-bottom: 6px;
    }}
    .pill {{
      font-size: 11px;
      border: 1px solid var(--line);
      border-radius: 99px;
      padding: 2px 7px;
      color: var(--muted);
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .panels {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="head">
      <div>
        <h1 id="title"></h1>
        <div class="sub">Time-series GEO trends with competitor-relative context</div>
      </div>
      <div class="sub" id="runs"></div>
    </div>
    <div class="grid">
      <div class="card"><div class="k">Latest Score</div><div class="v" id="score">-</div></div>
      <div class="card"><div class="k">Mindshare Gap To Leader</div><div class="v" id="gap-ms">-</div></div>
      <div class="card"><div class="k">Mention Gap To Leader</div><div class="v" id="gap-mr">-</div></div>
      <div class="card"><div class="k">Share Of Voice (Top 5)</div><div class="v" id="sov">-</div></div>
    </div>
    <div class="panels">
      <div class="chart-wrap">
        <h3 class="chart-title">Brand Metrics Over Time</h3>
        <svg class="chart" id="metric-chart" viewBox="0 0 900 220" preserveAspectRatio="none"></svg>
        <div class="legend" id="metric-legend"></div>
      </div>
      <div class="chart-wrap">
        <h3 class="chart-title">Competitor Latest Snapshot</h3>
        <div class="comp-list" id="comp-list"></div>
      </div>
    </div>
  </div>
  <script>
    const brand = {brand_safe};
    const data = {payload_json};
    const palette = ["#0f766e","#c2410c","#1d4ed8","#7c3aed","#be123c","#0f766e"];
    const metrics = [
      ["overall_score", "Overall Score"],
      ["mindshare_gap_to_leader", "Mindshare Gap"],
      ["share_of_voice_top5", "SOV Top5"],
    ];

    function fmt(v, pct=false) {{
      if (v === null || v === undefined || Number.isNaN(v)) return "-";
      return pct ? (v * 100).toFixed(1) + "%" : Number(v).toFixed(3);
    }}

    function points(series) {{
      return series.map(p => Number(p.value || 0));
    }}

    function drawChart(el, lines) {{
      const w = 900, h = 220, pad = 24;
      const vals = lines.flatMap(l => l.values);
      const min = Math.min(...vals, 0);
      const max = Math.max(...vals, 1);
      const span = (max - min) || 1;
      const n = lines[0]?.values.length || 1;
      const x = i => pad + (i * (w - pad * 2)) / Math.max(1, n - 1);
      const y = v => h - pad - ((v - min) * (h - pad * 2)) / span;

      let g = "";
      for (let i = 0; i < 4; i++) {{
        const yy = pad + i * (h - pad * 2) / 3;
        g += `<line x1="${{pad}}" y1="${{yy}}" x2="${{w-pad}}" y2="${{yy}}" stroke="#eadfce" stroke-width="1"/>`;
      }}

      const paths = lines.map(l => {{
        const d = l.values.map((v, i) => `${{i ? "L" : "M"}} ${{x(i)}} ${{y(v)}}`).join(" ");
        return `<path d="${{d}}" fill="none" stroke="${{l.color}}" stroke-width="2.5" />`;
      }}).join("");
      el.innerHTML = g + paths;
    }}

    function latestCompRows() {{
      const items = [];
      for (const [name, rows] of Object.entries(data.competitors || {{}})) {{
        if (!rows.length) continue;
        const r = rows[rows.length - 1];
        items.push({{name, ...r}});
      }}
      items.sort((a,b) => (b.mindshare || 0) - (a.mindshare || 0));
      return items.slice(0, 8);
    }}

    document.getElementById("title").textContent = `${{brand}} GEO Trends Dashboard`;
    document.getElementById("runs").textContent = `${{data.records.length}} runs`;
    const latest = data.latest?.competitor_relative || {{}};
    document.getElementById("score").textContent = fmt(data.latest?.overall_score);
    document.getElementById("gap-ms").textContent = fmt(latest.mindshare_gap_to_leader, true);
    document.getElementById("gap-mr").textContent = fmt(latest.mention_rate_gap_to_leader, true);
    document.getElementById("sov").textContent = fmt(latest.share_of_voice_top5, true);

    const lines = metrics.map((m, i) => ({{
      key: m[0],
      label: m[1],
      color: palette[i],
      values: points(data.series[m[0]] || [])
    }}));
    drawChart(document.getElementById("metric-chart"), lines);
    document.getElementById("metric-legend").innerHTML = lines
      .map(l => `<span><span class="dot" style="background:${{l.color}}"></span>${{l.label}}</span>`)
      .join("");

    const compList = document.getElementById("comp-list");
    compList.innerHTML = latestCompRows().map(c => `
      <div class="row">
        <div>${{c.name}}</div>
        <div class="pill">Mindshare ${{fmt(c.mindshare, true)}}</div>
        <div class="pill">Mentions ${{fmt(c.mention_rate, true)}}</div>
      </div>
    `).join("") || '<div class="sub">No competitor data yet.</div>';
  </script>
</body>
</html>
"""


def write_dashboard(brand: str, output_dir: str, out_file: str | None = None, compare: list[str] | None = None) -> Path:
    records = collect_trend_records(output_dir, brand=brand)
    payload = build_dashboard_payload(records, compare=compare)
    if out_file:
        path = Path(out_file)
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", brand.lower()).strip("-")
        path = Path("data/trends") / f"{slug or 'brand'}-dashboard.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard_html(brand, payload))
    return path

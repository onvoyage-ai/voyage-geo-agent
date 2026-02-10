"""Stage 5: Reporting — generates HTML, JSON, CSV, and Markdown reports."""

from __future__ import annotations

import html as html_mod
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import structlog

from voyage_geo.core.context import RunContext
from voyage_geo.core.pipeline import PipelineStage
from voyage_geo.storage.filesystem import FileSystemStorage
from voyage_geo.utils.progress import console, stage_header

logger = structlog.get_logger()


class ReportingStage(PipelineStage):
    name = "reporting"
    description = "Generate reports"

    def __init__(self, storage: FileSystemStorage) -> None:
        self.storage = storage

    async def execute(self, ctx: RunContext) -> RunContext:
        stage_header(self.name, self.description)

        if not ctx.analysis_result:
            raise RuntimeError("Analysis results required for reporting")

        formats = ctx.config.report.formats
        run_dir = self.storage.run_dir(ctx.run_id)

        for fmt in formats:
            console.print(f"  Generating [cyan]{fmt}[/cyan] report...")
            if fmt == "json":
                await self._render_json(ctx, run_dir)
            elif fmt == "csv":
                await self._render_csv(ctx, run_dir)
            elif fmt == "markdown":
                await self._render_markdown(ctx, run_dir)
            elif fmt == "html":
                await self._render_html(ctx, run_dir)

        console.print(f"  [green]Reports saved to:[/green] {run_dir / 'reports'}")

        ctx.completed_at = datetime.now(UTC).isoformat()
        return ctx

    async def _render_json(self, ctx: RunContext, run_dir: Path) -> None:
        await self.storage.save_json(ctx.run_id, "reports/report.json", ctx.analysis_result)

    async def _render_csv(self, ctx: RunContext, run_dir: Path) -> None:
        import pandas as pd
        analysis = ctx.analysis_result
        if not analysis:
            return

        # Mention rates by provider
        if analysis.mention_rate.by_provider:
            df = pd.DataFrame([
                {"provider": k, "mention_rate": v}
                for k, v in analysis.mention_rate.by_provider.items()
            ])
            path = run_dir / "reports" / "mention-rates.csv"
            df.to_csv(path, index=False)

        # Sentiment by provider
        if analysis.sentiment.by_provider:
            df = pd.DataFrame([
                {"provider": k, "score": v, "label": analysis.sentiment.by_provider_label.get(k, "")}
                for k, v in analysis.sentiment.by_provider.items()
            ])
            path = run_dir / "reports" / "sentiment.csv"
            df.to_csv(path, index=False)

        # Competitor scores
        if analysis.competitor_analysis.competitors:
            df = pd.DataFrame([c.model_dump() for c in analysis.competitor_analysis.competitors])
            path = run_dir / "reports" / "competitors.csv"
            df.to_csv(path, index=False)

    async def _render_markdown(self, ctx: RunContext, run_dir: Path) -> None:
        a = ctx.analysis_result
        if not a:
            return
        lines = [
            f"# GEO Report: {a.brand}",
            f"*Generated {a.analyzed_at}*\n",
            "## Executive Summary",
            f"**{a.summary.headline}**\n",
            "### Key Findings",
            *[f"- {f}" for f in a.summary.key_findings],
            "\n### Strengths",
            *[f"- {s}" for s in a.summary.strengths],
            "\n### Weaknesses",
            *[f"- {w}" for w in a.summary.weaknesses],
            "\n### Recommendations",
            *[f"- {r}" for r in a.summary.recommendations],
            "\n## Metrics",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Mention Rate | {a.mention_rate.overall*100:.1f}% |",
            f"| Mindshare | {a.mindshare.overall*100:.1f}% |",
            f"| Sentiment | {a.sentiment.label} ({a.sentiment.overall:.2f}) |",
            f"| Confidence | {a.sentiment.confidence:.0%} |",
            f"| Brand Rank | #{a.mindshare.rank}/{a.mindshare.total_brands_detected} |",
            f"| Overall Score | {a.summary.overall_score}/100 |",
            "\n## Sentiment by Provider",
            "| Provider | Score | Label |",
            "|----------|-------|-------|",
            *[f"| {p} | {s:.3f} | {a.sentiment.by_provider_label.get(p, '')} |" for p, s in a.sentiment.by_provider.items()],
        ]
        path = run_dir / "reports" / "report.md"
        path.write_text("\n".join(lines))

    async def _render_html(self, ctx: RunContext, run_dir: Path) -> None:
        a = ctx.analysis_result
        if not a:
            return

        # Generate plotly charts as embedded HTML
        charts_html = self._generate_charts(a)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GEO Report: {a.brand}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; color: #f1f5f9; }}
        h2 {{ font-size: 1.4rem; margin: 2rem 0 1rem; color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
        .score-banner {{ background: linear-gradient(135deg, #1e3a5f, #1e293b); padding: 2rem; border-radius: 12px; margin: 1.5rem 0; display: flex; align-items: center; gap: 2rem; }}
        .score-big {{ font-size: 3.5rem; font-weight: bold; color: #60a5fa; }}
        .score-label {{ font-size: 1.1rem; color: #94a3b8; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
        .metric {{ background: #1e293b; padding: 1.2rem; border-radius: 8px; }}
        .metric-value {{ font-size: 1.8rem; font-weight: bold; color: #60a5fa; }}
        .metric-label {{ font-size: 0.85rem; color: #94a3b8; margin-top: 0.3rem; }}
        .findings {{ list-style: none; }}
        .findings li {{ padding: 0.5rem 0; border-bottom: 1px solid #1e293b; }}
        .chart-container {{ background: #1e293b; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; font-weight: 600; }}
        .positive {{ color: #4ade80; }}
        .negative {{ color: #f87171; }}
        .neutral {{ color: #94a3b8; }}
        .query-group {{ background: #1e293b; border-radius: 8px; padding: 1.2rem; margin: 1rem 0; }}
        .query-text {{ font-size: 1.05rem; font-weight: 600; color: #f1f5f9; margin-bottom: 0.75rem; }}
        .query-badge {{ display: inline-block; font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 4px; margin-left: 0.5rem; font-weight: 500; vertical-align: middle; }}
        .badge-strategy {{ background: #1e3a5f; color: #60a5fa; }}
        .badge-category {{ background: #312e81; color: #a78bfa; }}
        .response-block {{ margin: 0.5rem 0; }}
        .response-block summary {{ cursor: pointer; padding: 0.5rem 0.75rem; background: #0f172a; border-radius: 6px; color: #94a3b8; font-size: 0.9rem; }}
        .response-block summary:hover {{ color: #e2e8f0; }}
        .response-block .provider-tag {{ color: #60a5fa; font-weight: 600; }}
        .response-block .model-tag {{ color: #64748b; font-size: 0.8rem; margin-left: 0.5rem; }}
        .response-content {{ padding: 0.75rem 1rem; margin-top: 0.25rem; background: #0f172a; border-radius: 0 0 6px 6px; white-space: pre-wrap; font-size: 0.85rem; line-height: 1.5; color: #cbd5e1; max-height: 400px; overflow-y: auto; }}
    </style>
</head>
<body>
<div class="container">
    <h1>GEO Report: {a.brand}</h1>
    <p style="color: #64748b;">Generated {a.analyzed_at}</p>

    <div class="score-banner">
        <div>
            <div class="score-big">{a.summary.overall_score}</div>
            <div class="score-label">Overall GEO Score</div>
        </div>
        <div style="flex:1;">
            <div style="font-size:1.2rem; margin-bottom:0.5rem;">{a.summary.headline}</div>
            <div style="color:#94a3b8;">{'  |  '.join(a.summary.key_findings[:3])}</div>
        </div>
    </div>

    <div class="metrics">
        <div class="metric"><div class="metric-value">{a.mention_rate.overall*100:.1f}%</div><div class="metric-label">Mention Rate</div></div>
        <div class="metric"><div class="metric-value">{a.mindshare.overall*100:.1f}%</div><div class="metric-label">Mindshare</div></div>
        <div class="metric"><div class="metric-value {a.sentiment.label}">{a.sentiment.label.title()}</div><div class="metric-label">Sentiment ({a.sentiment.overall:.2f})</div></div>
        <div class="metric"><div class="metric-value">#{a.mindshare.rank}</div><div class="metric-label">Brand Rank / {a.mindshare.total_brands_detected}</div></div>
        <div class="metric"><div class="metric-value">{a.sentiment.confidence:.0%}</div><div class="metric-label">Confidence</div></div>
        <div class="metric"><div class="metric-value">{a.sentiment.total_sentences}</div><div class="metric-label">Sentences Analyzed</div></div>
    </div>

    {charts_html}

    <h2>Strengths</h2>
    <ul class="findings">{''.join(f"<li>✓ {s}</li>" for s in a.summary.strengths)}</ul>

    <h2>Weaknesses</h2>
    <ul class="findings">{''.join(f"<li>✗ {w}</li>" for w in a.summary.weaknesses)}</ul>

    <h2>Recommendations</h2>
    <ul class="findings">{''.join(f"<li>→ {r}</li>" for r in a.summary.recommendations)}</ul>

    <h2>Sentiment by Provider</h2>
    <table>
        <tr><th>Provider</th><th>Score</th><th>Label</th></tr>
        {''.join(f"<tr><td>{p}</td><td>{s:.3f}</td><td class='{a.sentiment.by_provider_label.get(p, 'neutral')}'>{a.sentiment.by_provider_label.get(p, 'neutral')}</td></tr>" for p, s in a.sentiment.by_provider.items())}
    </table>

    <h2>Competitor Rankings</h2>
    <table>
        <tr><th>Brand</th><th>Mention Rate</th><th>Mindshare</th><th>Sentiment</th></tr>
        {''.join(f"<tr><td>{'<strong>' + c.name + '</strong>' if c.name == a.brand else c.name}</td><td>{c.mention_rate*100:.1f}%</td><td>{c.mindshare*100:.1f}%</td><td class='{('positive' if c.sentiment > 0.05 else 'negative' if c.sentiment < -0.05 else 'neutral')}'>{c.sentiment:.3f}</td></tr>" for c in a.competitor_analysis.competitors)}
    </table>

    {self._narrative_html(a)}

    {self._excerpts_html(a)}

    {self._query_results_html(ctx)}

</div>
</body>
</html>"""

        path = run_dir / "reports" / "report.html"
        path.write_text(html)

    def _narrative_html(self, a) -> str:
        n = a.narrative
        if not n.claims:
            return ""

        parts = []

        # Section 1: What AI Says About {brand}
        if n.brand_themes:
            parts.append(f"<h2>What AI Says About {html_mod.escape(a.brand)}</h2>")
            parts.append("<table><tr><th>Theme</th><th>Sentiment</th><th>Sample Claims</th></tr>")
            for attr, claims in n.brand_themes.items():
                pos = sum(1 for c in claims if c.sentiment == "positive")
                neg = sum(1 for c in claims if c.sentiment == "negative")
                neu = sum(1 for c in claims if c.sentiment == "neutral")
                sentiment_summary = []
                if pos:
                    sentiment_summary.append(f"<span class='positive'>{pos} positive</span>")
                if neg:
                    sentiment_summary.append(f"<span class='negative'>{neg} negative</span>")
                if neu:
                    sentiment_summary.append(f"<span class='neutral'>{neu} neutral</span>")
                sample = "; ".join(html_mod.escape(c.claim) for c in claims[:3])
                parts.append(
                    f"<tr><td><strong>{html_mod.escape(attr)}</strong></td>"
                    f"<td>{', '.join(sentiment_summary)}</td>"
                    f"<td>{sample}</td></tr>"
                )
            parts.append("</table>")

            # Plotly horizontal bar chart for brand themes
            attrs = list(n.brand_themes.keys())
            pos_counts = [sum(1 for c in n.brand_themes[a_] if c.sentiment == "positive") for a_ in attrs]
            neg_counts = [sum(1 for c in n.brand_themes[a_] if c.sentiment == "negative") for a_ in attrs]
            neu_counts = [sum(1 for c in n.brand_themes[a_] if c.sentiment == "neutral") for a_ in attrs]
            parts.append("""
    <div class="chart-container"><div id="narrative-themes-chart"></div></div>
    <script>
    Plotly.newPlot('narrative-themes-chart', [""")
            parts.append(f"""{{
        y: {attrs}, x: {pos_counts}, name: 'Positive', type: 'bar', orientation: 'h',
        marker: {{ color: '#4ade80' }}
    }}, {{
        y: {attrs}, x: {neu_counts}, name: 'Neutral', type: 'bar', orientation: 'h',
        marker: {{ color: '#94a3b8' }}
    }}, {{
        y: {attrs}, x: {neg_counts}, name: 'Negative', type: 'bar', orientation: 'h',
        marker: {{ color: '#f87171' }}
    }}], {{
        barmode: 'stack',
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: {{ color: '#e2e8f0' }},
        xaxis: {{ gridcolor: '#334155', title: 'Claims' }},
        margin: {{t: 10, b: 40, l: 120, r: 10}},
        height: {max(200, len(attrs) * 40 + 80)},
        legend: {{ orientation: 'h', y: -0.2 }}
    }}, {{responsive: true}});
    </script>""")

        # Section 2: USP Coverage Gaps
        if n.gaps:
            parts.append("<h2>USP Coverage Gaps</h2>")
            parts.append(f'<p style="color:#94a3b8;">Coverage: <strong>{n.coverage_score*100:.0f}%</strong> of USPs mentioned by AI models</p>')
            parts.append("<table><tr><th>USP</th><th>Status</th><th>Detail</th></tr>")
            for gap in n.gaps:
                status = "<span class='positive'>Covered</span>" if gap.covered else "<span class='negative'>Missing</span>"
                parts.append(
                    f"<tr><td>{html_mod.escape(gap.usp)}</td>"
                    f"<td>{status}</td>"
                    f"<td>{html_mod.escape(gap.detail)}</td></tr>"
                )
            parts.append("</table>")

        # Section 3: Competitive Narrative Map
        if n.competitor_themes:
            # Collect all attributes across all competitors
            all_attrs: set[str] = set()
            for attrs_map in n.competitor_themes.values():
                all_attrs.update(attrs_map.keys())
            sorted_attrs = sorted(all_attrs)

            parts.append("<h2>Competitive Narrative Map</h2>")
            parts.append("<table><tr><th>Brand</th>")
            for attr in sorted_attrs:
                parts.append(f"<th>{html_mod.escape(attr)}</th>")
            parts.append("</tr>")
            for brand, attrs_map in sorted(n.competitor_themes.items()):
                parts.append(f"<tr><td>{html_mod.escape(brand)}</td>")
                for attr in sorted_attrs:
                    count = attrs_map.get(attr, 0)
                    parts.append(f"<td>{count if count else '—'}</td>")
                parts.append("</tr>")
            parts.append("</table>")

        return "\n".join(parts)

    def _generate_charts(self, a) -> str:
        parts = []

        # Mindshare pie chart
        if a.competitor_analysis.competitors:
            labels = [c.name for c in a.competitor_analysis.competitors]
            values = [c.mindshare for c in a.competitor_analysis.competitors]
            parts.append(f"""
    <h2>Mindshare Distribution</h2>
    <div class="chart-container"><div id="mindshare-chart"></div></div>
    <script>
    Plotly.newPlot('mindshare-chart', [{{
        labels: {labels},
        values: {values},
        type: 'pie',
        hole: 0.4,
        marker: {{ colors: ['#60a5fa', '#f472b6', '#facc15', '#4ade80', '#a78bfa', '#fb923c', '#94a3b8'] }}
    }}], {{ paper_bgcolor: 'transparent', font: {{ color: '#e2e8f0' }}, margin: {{t:10,b:10,l:10,r:10}}, height: 350 }}, {{responsive: true}});
    </script>""")

        # Sentiment by provider bar chart
        if a.sentiment.by_provider:
            providers = list(a.sentiment.by_provider.keys())
            scores = list(a.sentiment.by_provider.values())
            colors = ['#4ade80' if s > 0.05 else '#f87171' if s < -0.05 else '#94a3b8' for s in scores]
            parts.append(f"""
    <h2>Sentiment by Provider</h2>
    <div class="chart-container"><div id="sentiment-chart"></div></div>
    <script>
    Plotly.newPlot('sentiment-chart', [{{
        x: {providers},
        y: {scores},
        type: 'bar',
        marker: {{ color: {colors} }}
    }}], {{ paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: {{ color: '#e2e8f0' }}, yaxis: {{gridcolor: '#334155'}}, margin: {{t:10,b:40,l:50,r:10}}, height: 300 }}, {{responsive: true}});
    </script>""")

        return "\n".join(parts)

    def _excerpts_html(self, a) -> str:
        parts = []
        if a.sentiment.top_positive:
            parts.append("<h2>Top Positive Mentions</h2><table><tr><th>Provider</th><th>Score</th><th>Excerpt</th></tr>")
            for e in a.sentiment.top_positive:
                parts.append(f"<tr><td>{e.provider}</td><td class='positive'>{e.score:.3f}</td><td>{e.text}</td></tr>")
            parts.append("</table>")
        if a.sentiment.top_negative:
            parts.append("<h2>Top Negative Mentions</h2><table><tr><th>Provider</th><th>Score</th><th>Excerpt</th></tr>")
            for e in a.sentiment.top_negative:
                parts.append(f"<tr><td>{e.provider}</td><td class='negative'>{e.score:.3f}</td><td>{e.text}</td></tr>")
            parts.append("</table>")
        return "\n".join(parts)

    def _query_results_html(self, ctx: RunContext) -> str:
        if not ctx.execution_run or not ctx.execution_run.results:
            return ""

        # Build a lookup for query metadata (strategy, category)
        query_meta: dict[str, dict[str, str]] = {}
        if ctx.query_set:
            for q in ctx.query_set.queries:
                query_meta[q.id] = {"strategy": q.strategy, "category": q.category}

        # Group results by query_text (preserving order)
        grouped: dict[str, list] = defaultdict(list)
        query_order: list[str] = []
        for r in ctx.execution_run.results:
            key = r.query_text
            if key not in grouped:
                query_order.append(key)
            grouped[key].append(r)

        parts = ['<h2>Simulated Queries &amp; AI Responses</h2>']

        for query_text in query_order:
            responses = grouped[query_text]
            first = responses[0]
            meta = query_meta.get(first.query_id, {})
            strategy = meta.get("strategy", "")
            category = meta.get("category", "")

            badges = ""
            if strategy:
                badges += f'<span class="query-badge badge-strategy">{html_mod.escape(strategy)}</span>'
            if category:
                badges += f'<span class="query-badge badge-category">{html_mod.escape(category)}</span>'

            parts.append(f'<div class="query-group">')
            parts.append(f'<div class="query-text">{html_mod.escape(query_text)}{badges}</div>')

            for r in responses:
                provider_esc = html_mod.escape(r.provider)
                model_esc = html_mod.escape(r.model)
                response_esc = html_mod.escape(r.response or "(no response)")

                preview = html_mod.escape((r.response or "")[:200])
                if len(r.response or "") > 200:
                    preview += "..."

                parts.append(f'<details class="response-block">')
                parts.append(
                    f'<summary><span class="provider-tag">{provider_esc}</span>'
                    f'<span class="model-tag">{model_esc}</span> — {preview}</summary>'
                )
                parts.append(f'<div class="response-content">{response_esc}</div>')
                parts.append('</details>')

            parts.append('</div>')

        return "\n".join(parts)

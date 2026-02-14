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

# Provider logo SVGs — small inline icons with brand colors
# Each is a 20x20 SVG with the provider's logo/mark
PROVIDER_LOGOS: dict[str, str] = {
    "chatgpt": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#10a37f"/><path d="M10 4.5c-.4 0-.8.3-.8.7v3l-2.6-1.5a.8.8 0 00-1.1.3.8.8 0 00.3 1.1L8.4 9.6l-2.6 1.5a.8.8 0 00-.3 1.1.8.8 0 001.1.3l2.6-1.5v3c0 .4.4.7.8.7s.8-.3.8-.7v-3l2.6 1.5a.8.8 0 001.1-.3.8.8 0 00-.3-1.1l-2.6-1.5 2.6-1.5a.8.8 0 00.3-1.1.8.8 0 00-1.1-.3l-2.6 1.5v-3c0-.4-.4-.7-.8-.7z" fill="white"/></svg>',
    "claude": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#d4956b"/><path d="M10.8 5.5L7 14h1.7l.8-1.8h3.3l.7 1.8H15l-3.1-8.5h-1.1zm.1 3l1.1 2.7H9.8l1.1-2.7z" fill="white"/></svg>',
    "gemini": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#4285f4"/><path d="M10 4a6 6 0 00-6 6c0 1.5.6 2.9 1.5 4A6 6 0 0010 16a6 6 0 004.5-2 6 6 0 001.5-4 6 6 0 00-6-6zm0 1.8a4.2 4.2 0 014.2 4.2A4.2 4.2 0 0110 14.2 4.2 4.2 0 015.8 10 4.2 4.2 0 0110 5.8z" fill="white" fill-opacity=".5"/><circle cx="10" cy="10" r="2.5" fill="white"/></svg>',
    "perplexity-or": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#20808d"/><path d="M10 4L5 8l5 4 5-4-5-4zM5 12l5 4 5-4" stroke="white" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "perplexity": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#20808d"/><path d="M10 4L5 8l5 4 5-4-5-4zM5 12l5 4 5-4" stroke="white" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "deepseek": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#4D6BFE"/><path d="M6.5 6.5C6.5 6.5 8 5 10 5s3.5 1.5 3.5 1.5M7 10h6M6.5 13.5S8 15 10 15s3.5-1.5 3.5-1.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/></svg>',
    "grok": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#1a1a1a"/><path d="M6 6l3.5 4L6 14M10.5 6L14 10l-3.5 4" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "llama": '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#6C3AED"/><path d="M8 14V8.5C8 7 9 5.5 10 5.5S12 7 12 8.5V14M8 11h4M7 14h1.5M11.5 14H13" stroke="white" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}

# Fallback: generate a colored circle with initial
_FALLBACK_COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#14b8a6", "#f59e0b", "#ef4444", "#ec4899"]


def _provider_logo(name: str) -> str:
    """Return inline SVG logo HTML for a provider, or a colored initial fallback."""
    if name in PROVIDER_LOGOS:
        return PROVIDER_LOGOS[name]
    # Fallback: colored rounded square with first letter
    color = _FALLBACK_COLORS[hash(name) % len(_FALLBACK_COLORS)]
    initial = name[0].upper() if name else "?"
    return f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="{color}"/><text x="10" y="14.5" text-anchor="middle" fill="white" font-family="system-ui,sans-serif" font-size="11" font-weight="700">{initial}</text></svg>'


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

        e = html_mod.escape
        brand = e(a.brand)
        score = a.summary.overall_score
        sc = "#3d7a5f" if score > 60 else "#96742b" if score > 30 else "#b04848"
        mr = a.mention_rate.overall * 100
        ms = a.mindshare.overall * 100
        circ = 2 * 3.14159 * 56
        n_providers = len(a.sentiment.by_provider)

        # Score grade
        if score > 75: grade, grade_w = "Excellent", "Outstanding AI visibility"
        elif score > 60: grade, grade_w = "Strong", "Above-average AI presence"
        elif score > 40: grade, grade_w = "Moderate", "Room for improvement"
        elif score > 20: grade, grade_w = "Weak", "Significant gaps in AI visibility"
        else: grade, grade_w = "Critical", "Nearly invisible to AI models"

        # Sentiment
        sl = a.sentiment.label
        so = a.sentiment.overall

        # Findings
        findings = "".join(f'<div class="f-item"><div class="f-dot"></div><span>{e(f)}</span></div>' for f in a.summary.key_findings)

        # Metric sparklines - provider bars for mention rate
        def make_provider_rows(data: dict[str, float], fmt: str = "pct", colors_by_label: dict | None = None) -> str:
            if not data:
                return ""
            mx = max(data.values()) if data else 1
            rows = ""
            for p, v in sorted(data.items(), key=lambda x: -x[1]):
                w = (v / max(mx, 0.001)) * 100 if fmt == "pct" else max((v + 1) / 2 * 100, 3)
                val_str = f"{v*100:.0f}%" if fmt == "pct" else f"{v:.2f}"
                bar_color = ""
                if colors_by_label:
                    lb = colors_by_label.get(p, "neutral")
                    bar_color = f' style="background:var(--c-{lb})"'
                logo = _provider_logo(p)
                rows += f'<div class="pv-row"><span class="pv-logo">{logo}</span><span class="pv-name">{e(p)}</span><div class="pv-bar"><div class="pv-fill"{bar_color} style="width:{w:.0f}%{bar_color}"></div></div><span class="pv-val">{val_str}</span></div>'
            return rows

        mr_rows = make_provider_rows(a.mention_rate.by_provider, "pct")
        ms_rows = make_provider_rows(a.mindshare.by_provider, "pct")
        sent_rows = make_provider_rows(a.sentiment.by_provider, "score", a.sentiment.by_provider_label)

        # Competitor table
        comp_html = ""
        if a.competitor_analysis.competitors:
            rows = ""
            for i, c in enumerate(a.competitor_analysis.competitors):
                is_t = c.name.lower() == a.brand.lower()
                cls = ' class="t-hl"' if is_t else ""
                nm = f"<strong>{e(c.name)}</strong>" if is_t else e(c.name)
                # Mindshare bar
                ms_w = min(c.mindshare * 100 / max(a.competitor_analysis.competitors[0].mindshare, 0.01) * 100, 100) if a.competitor_analysis.competitors[0].mindshare else 0
                s_cls = "positive" if c.sentiment > 0.05 else "negative" if c.sentiment < -0.05 else "neutral"
                rows += f'<tr{cls}><td class="t-rank">{i+1}</td><td class="t-name">{nm}</td><td><div class="t-bar-wrap"><div class="t-bar" style="width:{c.mention_rate*100:.0f}%"></div></div><span class="t-pct">{c.mention_rate*100:.0f}%</span></td><td><div class="t-bar-wrap"><div class="t-bar t-bar-ms" style="width:{ms_w:.0f}%"></div></div><span class="t-pct">{c.mindshare*100:.1f}%</span></td><td class="t-sent t-{s_cls}">{c.sentiment:+.2f}</td></tr>'
            comp_html = f'<div class="sect"><h3>Competitive Landscape</h3><div class="panel"><table class="comp-tbl"><thead><tr><th></th><th>Brand</th><th>Mentions</th><th>Mindshare</th><th>Sentiment</th></tr></thead><tbody>{rows}</tbody></table></div></div>'

        # Strengths / weaknesses
        str_items = "".join(f'<div class="sw-item sw-s"><svg viewBox="0 0 20 20" fill="currentColor" class="sw-ico"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg><span>{e(s)}</span></div>' for s in a.summary.strengths)
        wk_items = "".join(f'<div class="sw-item sw-w"><svg viewBox="0 0 20 20" fill="currentColor" class="sw-ico"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg><span>{e(w)}</span></div>' for w in a.summary.weaknesses)

        # Recommendations
        rec_items = "".join(f'<div class="rec-item"><div class="rec-num">{i+1}</div><span>{e(r)}</span></div>' for i, r in enumerate(a.summary.recommendations))

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{brand} — GEO Analysis</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
:root{{
--c-bg:#f8f8f7;--c-surface:#ffffff;--c-surface2:#f2f1ef;--c-border:#e3e1dd;--c-border2:#d4d1cc;
--c-text:#1c1917;--c-text2:#44403c;--c-text3:#78716c;--c-text4:#a8a29e;
--c-accent:#292524;--c-accent2:#44403c;--c-accent-dim:rgba(41,37,36,.06);
--c-positive:#2b7a4b;--c-negative:#b33b3b;--c-neutral:#78716c;
--c-positive-dim:rgba(43,122,75,.09);--c-negative-dim:rgba(179,59,59,.08);
--r:10px;--r2:12px;
}}
body{{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--c-bg);color:var(--c-text);line-height:1.55;-webkit-font-smoothing:antialiased;min-height:100vh}}
.wrap{{max-width:1100px;margin:0 auto;padding:56px 40px 80px}}

/* ── Masthead ── */
.mast{{display:flex;align-items:flex-end;justify-content:space-between;padding-bottom:32px;border-bottom:1px solid var(--c-border);margin-bottom:48px}}
.mast-brand{{display:flex;align-items:center;gap:14px}}
.mast-icon{{width:36px;height:36px;background:var(--c-text);border-radius:9px;display:flex;align-items:center;justify-content:center}}
.mast-icon svg{{width:20px;height:20px;fill:white}}
.mast h1{{font-size:14px;font-weight:500;color:var(--c-text3);letter-spacing:-.01em}}
.mast h1 strong{{color:var(--c-text);font-weight:700;font-size:18px;display:block;margin-top:2px;letter-spacing:-.02em}}
.mast-meta{{text-align:right;font-size:11px;color:var(--c-text3);line-height:1.8;letter-spacing:.01em}}

/* ── Hero score ── */
.hero{{display:grid;grid-template-columns:auto 1fr;gap:56px;align-items:center;margin-bottom:48px}}
.hero-ring{{position:relative;width:140px;height:140px}}
.hero-ring svg{{width:140px;height:140px;transform:rotate(-90deg)}}
.hero-ring .trk{{fill:none;stroke:var(--c-surface2);stroke-width:9}}
.hero-ring .val{{fill:none;stroke-width:9;stroke-linecap:round}}
.hero-center{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.hero-score{{font-size:44px;font-weight:900;letter-spacing:-.05em;line-height:1}}
.hero-of{{font-size:12px;color:var(--c-text3);font-weight:500;margin-top:3px;letter-spacing:.02em}}
.hero-right h2{{font-size:26px;font-weight:800;letter-spacing:-.025em;line-height:1.25;margin-bottom:6px;color:var(--c-text)}}
.hero-grade{{font-size:13px;font-weight:500;color:var(--c-text2);margin-bottom:24px}}
.hero-grade em{{font-style:normal;padding:3px 10px;border-radius:5px;font-size:11px;margin-right:8px;font-weight:700;letter-spacing:.03em;text-transform:uppercase}}
.f-wrap{{display:flex;flex-direction:column;gap:7px}}
.f-item{{display:flex;align-items:baseline;gap:10px;font-size:13px;color:var(--c-text2);line-height:1.5}}
.f-dot{{width:4px;height:4px;border-radius:50%;background:var(--c-border2);flex-shrink:0;margin-top:7px}}

/* ── KPI strip ── */
.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--c-border);border-radius:var(--r2);overflow:hidden;margin-bottom:48px;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.kpi{{background:var(--c-surface);padding:26px 22px}}
.kpi-val{{font-size:24px;font-weight:800;letter-spacing:-.03em;line-height:1;color:var(--c-text)}}
.kpi-label{{font-size:10px;color:var(--c-text3);text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-top:8px}}
.kpi-sub{{font-size:11px;color:var(--c-text3);margin-top:3px;font-weight:400}}

/* ── Sections ── */
.sect{{margin-bottom:44px}}
.sect h3{{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--c-text3);font-weight:700;margin-bottom:18px;padding-left:1px}}

/* ── Panel ── */
.panel{{background:var(--c-surface);border:1px solid var(--c-border);border-radius:var(--r2);overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.03)}}
.panel-head{{padding:16px 24px;border-bottom:1px solid var(--c-border);font-size:12px;font-weight:600;color:var(--c-text2);display:flex;align-items:center;justify-content:space-between;letter-spacing:.01em}}
.panel-body{{padding:20px 24px}}

/* ── Provider bars ── */
.pv-row{{display:flex;align-items:center;gap:12px;height:34px}}
.pv-logo{{width:20px;height:20px;flex-shrink:0;border-radius:5px}}
.pv-logo svg{{display:block}}
.pv-name{{font-size:12px;font-weight:500;color:var(--c-text2);width:70px;text-align:left;flex-shrink:0}}
.pv-bar{{flex:1;height:5px;background:var(--c-surface2);border-radius:99px;overflow:hidden}}
.pv-fill{{height:100%;border-radius:99px;background:var(--c-accent);transition:width .5s cubic-bezier(.4,0,.2,1)}}
.pv-val{{font-size:12px;font-weight:700;color:var(--c-text);width:50px;text-align:right;font-variant-numeric:tabular-nums}}

/* ── Grid ── */
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.g3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}}

/* ── Comp table ── */
.comp-tbl{{width:100%;border-collapse:collapse}}
.comp-tbl th{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--c-text3);font-weight:600;text-align:left;padding:13px 16px;border-bottom:1px solid var(--c-border)}}
.comp-tbl td{{padding:11px 16px;border-bottom:1px solid var(--c-surface2);font-size:13px;vertical-align:middle}}
.comp-tbl tr:last-child td{{border:none}}
.comp-tbl tr:hover{{background:var(--c-surface2)}}
.t-hl{{background:var(--c-accent-dim)!important}}
.t-hl td{{font-weight:600}}
.t-rank{{color:var(--c-text3);font-weight:600;width:32px;font-variant-numeric:tabular-nums}}
.t-name{{font-weight:500}}
.t-bar-wrap{{display:inline-block;width:56px;height:4px;background:var(--c-surface2);border-radius:99px;overflow:hidden;vertical-align:middle;margin-right:8px}}
.t-bar{{height:100%;border-radius:99px;background:var(--c-accent)}}
.t-bar-ms{{background:var(--c-text3)}}
.t-pct{{font-size:12px;font-weight:600;color:var(--c-text2);font-variant-numeric:tabular-nums}}
.t-sent{{font-weight:700;font-variant-numeric:tabular-nums;font-size:12px}}
.t-positive{{color:var(--c-positive)}}
.t-negative{{color:var(--c-negative)}}
.t-neutral{{color:var(--c-text3)}}

/* ── Strengths / Weaknesses ── */
.sw-item{{display:flex;align-items:flex-start;gap:10px;padding:12px 0;border-bottom:1px solid var(--c-surface2);font-size:13px;color:var(--c-text2);line-height:1.55}}
.sw-item:last-child{{border:none}}
.sw-ico{{width:17px;height:17px;flex-shrink:0;margin-top:1px}}
.sw-s .sw-ico{{color:var(--c-positive)}}
.sw-w .sw-ico{{color:var(--c-negative)}}

/* ── Recs ── */
.rec-item{{display:flex;align-items:flex-start;gap:14px;padding:14px 0;border-bottom:1px solid var(--c-surface2);font-size:13px;color:var(--c-text2);line-height:1.6}}
.rec-item:last-child{{border:none}}
.rec-num{{width:24px;height:24px;border-radius:7px;background:var(--c-surface2);color:var(--c-text2);font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}}

/* ── Narrative ── */
.nar-row{{display:grid;grid-template-columns:110px auto 1fr;gap:16px;padding:14px 0;border-bottom:1px solid var(--c-surface2);align-items:center}}
.nar-row:last-child{{border:none}}
.nar-attr{{font-size:12px;font-weight:700;color:var(--c-text);text-transform:capitalize}}
.nar-pills{{display:flex;gap:5px;flex-wrap:wrap}}
.nar-pill{{font-size:10px;font-weight:700;padding:2px 7px;border-radius:5px;letter-spacing:.02em}}
.nar-pill-pos{{background:var(--c-positive-dim);color:var(--c-positive)}}
.nar-pill-neg{{background:var(--c-negative-dim);color:var(--c-negative)}}
.nar-pill-neu{{background:var(--c-surface2);color:var(--c-text3)}}
.nar-claims{{font-size:12px;color:var(--c-text3);line-height:1.5}}

/* ── USP gaps ── */
.usp-row{{display:grid;grid-template-columns:20px 1fr 2fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--c-surface2);align-items:center}}
.usp-row:last-child{{border:none}}
.usp-dot{{width:8px;height:8px;border-radius:50%}}
.usp-ok{{background:var(--c-positive)}}
.usp-miss{{background:var(--c-negative)}}
.usp-name{{font-size:13px;font-weight:600;color:var(--c-text)}}
.usp-detail{{font-size:12px;color:var(--c-text3)}}

/* ── Heatmap ── */
.heat-tbl{{width:100%;border-collapse:collapse}}
.heat-tbl th{{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--c-text3);font-weight:600;padding:12px 10px;border-bottom:1px solid var(--c-border);text-align:center}}
.heat-tbl th:first-child{{text-align:left;padding-left:16px}}
.heat-tbl td{{padding:10px;text-align:center;font-size:12px;font-weight:700;border-bottom:1px solid var(--c-surface2)}}
.heat-tbl td:first-child{{text-align:left;padding-left:16px;font-weight:500}}
.heat-tbl tr:last-child td{{border:none}}
.h0{{color:var(--c-text4)}}
.h1{{color:var(--c-positive);background:rgba(61,122,95,.05)}}
.h2{{color:var(--c-positive);background:rgba(61,122,95,.1)}}
.h3{{color:var(--c-positive);background:rgba(61,122,95,.16)}}

/* ── Excerpts ── */
.exc{{padding:14px 18px;border-left:2px solid var(--c-border);margin-bottom:10px;border-radius:0 6px 6px 0;background:var(--c-surface2)}}
.exc:last-child{{margin:0}}
.exc-pos{{border-left-color:var(--c-positive)}}
.exc-neg{{border-left-color:var(--c-negative)}}
.exc-text{{font-size:13px;color:var(--c-text2);line-height:1.65}}
.exc-meta{{font-size:11px;color:var(--c-text3);margin-top:6px;font-weight:500;display:flex;align-items:center;gap:6px}}
.exc-logo{{width:16px;height:16px;flex-shrink:0}}
.exc-logo svg{{width:16px;height:16px;display:block}}

/* ── Queries ── */
.qsect{{margin-top:52px;padding-top:44px;border-top:1px solid var(--c-border)}}
.qcard{{background:var(--c-surface);border:1px solid var(--c-border);border-radius:var(--r2);margin-bottom:12px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.03)}}
.qcard-q{{font-size:13px;font-weight:600;padding:14px 20px;border-bottom:1px solid var(--c-surface2);display:flex;align-items:center;gap:10px;flex-wrap:wrap;color:var(--c-text)}}
.qbadge{{font-size:9px;font-weight:700;padding:2px 6px;border-radius:4px;text-transform:uppercase;letter-spacing:.05em}}
.qb-s{{background:var(--c-accent-dim);color:var(--c-text2)}}
.qb-c{{background:var(--c-surface2);color:var(--c-text3)}}
.qresp{{border-bottom:1px solid var(--c-surface2)}}
.qresp:last-child{{border:none}}
.qresp summary{{cursor:pointer;padding:10px 20px;font-size:12px;color:var(--c-text3);display:flex;gap:8px;align-items:baseline;transition:background .15s}}
.qresp summary:hover{{background:var(--c-surface2)}}
.qp-logo{{width:18px;height:18px;flex-shrink:0}}
.qp-logo svg{{width:18px;height:18px;display:block}}
.qresp .qp{{font-weight:600;color:var(--c-text2)}}
.qresp .qm{{color:var(--c-text3);font-size:10px}}
.qresp .qprev{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--c-text3)}}
.qresp-body{{padding:14px 20px 18px;font-size:12px;color:var(--c-text2);line-height:1.7;white-space:pre-wrap;max-height:420px;overflow-y:auto;background:var(--c-bg);border-top:1px solid var(--c-surface2)}}

/* ── Footer ── */
.foot{{margin-top:56px;padding-top:24px;border-top:1px solid var(--c-border);display:flex;justify-content:space-between;font-size:11px;color:var(--c-text3)}}

@media(max-width:800px){{
.wrap{{padding:32px 20px 60px}}
.hero{{grid-template-columns:1fr;text-align:center;gap:24px}}
.hero-ring{{margin:0 auto}}
.kpis{{grid-template-columns:repeat(2,1fr)}}
.kpis .kpi:last-child{{grid-column:span 2}}
.g2,.g3{{grid-template-columns:1fr}}
.nar-row{{grid-template-columns:1fr;gap:6px}}
.usp-row{{grid-template-columns:20px 1fr}}
.usp-detail{{grid-column:span 2}}
}}
@media print{{
body{{background:#fff}}
.panel{{box-shadow:none;border-color:#e0e0e0}}
.kpis{{box-shadow:none}}
.qsect{{page-break-before:always}}
}}
</style>
</head>
<body>
<div class="wrap">

<div class="mast">
<div class="mast-brand">
<div class="mast-icon"><svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg></div>
<h1>GEO Analysis<strong>{brand}</strong></h1>
</div>
<div class="mast-meta">Report ID: {e(a.run_id)}<br>{a.analyzed_at[:10]} &middot; {n_providers} AI models</div>
</div>

<div class="hero">
<div class="hero-ring">
<svg viewBox="0 0 140 140">
<circle class="trk" cx="70" cy="70" r="56"/>
<circle class="val" cx="70" cy="70" r="56" stroke="{sc}" stroke-dasharray="{circ:.0f}" stroke-dashoffset="{circ * (1 - score / 100):.0f}"/>
</svg>
<div class="hero-center">
<div class="hero-score" style="color:{sc}">{score:.0f}</div>
<div class="hero-of">/100</div>
</div>
</div>
<div class="hero-right">
<h2>{brand}</h2>
<div class="hero-grade"><em style="background:{sc}15;color:{sc}">{grade}</em>{grade_w}</div>
<div class="f-wrap">{findings}</div>
</div>
</div>

<div class="kpis">
<div class="kpi"><div class="kpi-val">{mr:.0f}%</div><div class="kpi-label">Mention Rate</div><div class="kpi-sub">{a.mention_rate.total_mentions} / {a.mention_rate.total_responses} responses</div></div>
<div class="kpi"><div class="kpi-val">{ms:.1f}%</div><div class="kpi-label">Mindshare</div><div class="kpi-sub">Rank #{a.mindshare.rank} of {a.mindshare.total_brands_detected}</div></div>
<div class="kpi"><div class="kpi-val" style="color:var(--c-{sl})">{sl.title()}</div><div class="kpi-label">Sentiment</div><div class="kpi-sub">Score: {so:.2f}</div></div>
<div class="kpi"><div class="kpi-val">{a.sentiment.confidence:.0%}</div><div class="kpi-label">Confidence</div><div class="kpi-sub">{a.sentiment.total_sentences} sentences</div></div>
<div class="kpi"><div class="kpi-val">{a.sentiment.positive_count}<span style="color:var(--c-text4);font-size:14px;font-weight:500"> / {a.sentiment.negative_count}</span></div><div class="kpi-label">Positive / Negative</div><div class="kpi-sub">{a.sentiment.neutral_count} neutral</div></div>
</div>

<div class="sect"><h3>Provider Performance</h3>
<div class="g3">
<div class="panel"><div class="panel-head">Mention Rate</div><div class="panel-body">{mr_rows}</div></div>
<div class="panel"><div class="panel-head">Mindshare</div><div class="panel-body">{ms_rows}</div></div>
<div class="panel"><div class="panel-head">Sentiment</div><div class="panel-body">{sent_rows}</div></div>
</div></div>

{comp_html}

<div class="sect"><h3>Assessment</h3>
<div class="g2">
<div class="panel"><div class="panel-head">Strengths</div><div class="panel-body">{str_items}</div></div>
<div class="panel"><div class="panel-head">Weaknesses</div><div class="panel-body">{wk_items}</div></div>
</div></div>

<div class="sect"><h3>Recommendations</h3>
<div class="panel"><div class="panel-body">{rec_items}</div></div></div>

{self._narrative_html(a)}
{self._excerpts_html(a)}
{self._query_results_html(ctx)}

<div class="foot"><span>Generated by Voyage GEO</span><span>{a.analyzed_at[:10]}</span></div>
</div>
</body></html>"""

        path = run_dir / "reports" / "report.html"
        path.write_text(html)

    def _competitor_html(self, a, comp_rows: str) -> str:
        return ""  # Now built inline in _render_html

    def _narrative_html(self, a) -> str:
        n = a.narrative
        if not n.claims:
            return ""
        e = html_mod.escape
        parts = []

        if n.brand_themes:
            rows = ""
            for attr, claims in n.brand_themes.items():
                pos = sum(1 for c in claims if c.sentiment == "positive")
                neg = sum(1 for c in claims if c.sentiment == "negative")
                neu = sum(1 for c in claims if c.sentiment == "neutral")
                pills = ""
                if pos: pills += f'<span class="nar-pill nar-pill-pos">{pos} pos</span>'
                if neg: pills += f'<span class="nar-pill nar-pill-neg">{neg} neg</span>'
                if neu: pills += f'<span class="nar-pill nar-pill-neu">{neu} neu</span>'
                sample = "; ".join(e(c.claim) for c in claims[:2])
                rows += f'<div class="nar-row"><div class="nar-attr">{e(attr)}</div><div class="nar-pills">{pills}</div><div class="nar-claims">{sample}</div></div>'
            parts.append(f'<div class="sect"><h3>AI Narrative — {e(a.brand)}</h3><div class="panel"><div class="panel-body">{rows}</div></div></div>')

        if n.gaps:
            gap_rows = ""
            for g in n.gaps:
                cls = "usp-ok" if g.covered else "usp-miss"
                gap_rows += f'<div class="usp-row"><div class="usp-dot {cls}"></div><div class="usp-name">{e(g.usp)}</div><div class="usp-detail">{e(g.detail)}</div></div>'
            parts.append(f'<div class="sect"><h3>USP Coverage — {n.coverage_score*100:.0f}%</h3><div class="panel"><div class="panel-body">{gap_rows}</div></div></div>')

        if n.competitor_themes:
            all_attrs: set[str] = set()
            for m in n.competitor_themes.values():
                all_attrs.update(m.keys())
            sa = sorted(all_attrs)
            hdr = "".join(f"<th>{e(at)}</th>" for at in sa)
            brows = ""
            for brand, am in sorted(n.competitor_themes.items()):
                is_t = brand.lower() == a.brand.lower()
                cls = ' class="t-hl"' if is_t else ""
                nm = f"<strong>{e(brand)}</strong>" if is_t else e(brand)
                cells = "".join(f'<td class="h{min(am.get(at,0),3)}">{am.get(at,0) or ""}</td>' for at in sa)
                brows += f"<tr{cls}><td>{nm}</td>{cells}</tr>"
            parts.append(f'<div class="sect"><h3>Competitive Narrative Map</h3><div class="panel"><table class="heat-tbl"><thead><tr><th>Brand</th>{hdr}</tr></thead><tbody>{brows}</tbody></table></div></div>')

        return "\n".join(parts)

    def _generate_charts(self, a) -> str:
        return ""

    def _excerpts_html(self, a) -> str:
        e = html_mod.escape
        has_pos = bool(a.sentiment.top_positive)
        has_neg = bool(a.sentiment.top_negative)
        if not has_pos and not has_neg:
            return ""
        pos_h = "".join(f'<div class="exc exc-pos"><div class="exc-text">{e(x.text[:300])}</div><div class="exc-meta"><span class="exc-logo">{_provider_logo(x.provider)}</span>{e(x.provider)} &middot; {x.score:.2f}</div></div>' for x in a.sentiment.top_positive[:5])
        neg_h = "".join(f'<div class="exc exc-neg"><div class="exc-text">{e(x.text[:300])}</div><div class="exc-meta"><span class="exc-logo">{_provider_logo(x.provider)}</span>{e(x.provider)} &middot; {x.score:.2f}</div></div>' for x in a.sentiment.top_negative[:5])
        left = f'<div class="panel"><div class="panel-head">Top Positive</div><div class="panel-body">{pos_h}</div></div>' if has_pos else ""
        right = f'<div class="panel"><div class="panel-head">Top Negative</div><div class="panel-body">{neg_h}</div></div>' if has_neg else ""
        return f'<div class="sect"><h3>Sentiment Excerpts</h3><div class="g2">{left}{right}</div></div>'

    def _query_results_html(self, ctx: RunContext) -> str:
        if not ctx.execution_run or not ctx.execution_run.results:
            return ""
        e = html_mod.escape
        query_meta: dict[str, dict[str, str]] = {}
        if ctx.query_set:
            for q in ctx.query_set.queries:
                query_meta[q.id] = {"strategy": q.strategy, "category": q.category}
        grouped: dict[str, list] = defaultdict(list)
        order: list[str] = []
        for r in ctx.execution_run.results:
            if r.query_text not in grouped:
                order.append(r.query_text)
            grouped[r.query_text].append(r)

        parts = [f'<div class="qsect"><div class="sect"><h3>Queries &amp; Responses ({len(order)} queries)</h3>']
        for qt in order:
            resps = grouped[qt]
            meta = query_meta.get(resps[0].query_id, {})
            badges = ""
            if meta.get("strategy"):
                badges += f'<span class="qbadge qb-s">{e(meta["strategy"])}</span>'
            if meta.get("category"):
                badges += f'<span class="qbadge qb-c">{e(meta["category"])}</span>'
            inner = ""
            for r in resps:
                prev = e((r.response or "")[:100]) + ("..." if len(r.response or "") > 100 else "")
                logo = _provider_logo(r.provider)
                inner += f'<details class="qresp"><summary><span class="qp-logo">{logo}</span><span class="qp">{e(r.provider)}</span><span class="qm">{e(r.model)}</span><span class="qprev">{prev}</span></summary><div class="qresp-body">{e(r.response or "(no response)")}</div></details>'
            parts.append(f'<div class="qcard"><div class="qcard-q">{e(qt)}{badges}</div>{inner}</div>')
        parts.append("</div></div>")
        return "\n".join(parts)

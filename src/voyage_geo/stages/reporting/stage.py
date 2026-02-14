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

# Provider logo SVGs — official brand icons from Simple Icons (CC0) + LobeHub
# Each is a 20x20 SVG: colored rounded-rect background + white logo path (scaled from 24x24)
_T = 'translate(3,3) scale(0.583)'  # centers a 24x24 path inside a 20x20 box with padding

PROVIDER_LOGOS: dict[str, str] = {
    "chatgpt": f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#10a37f"/><path transform="{_T}" fill="white" d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/></svg>',
    "claude": f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#D4956B"/><path transform="{_T}" fill="white" d="M17.3041 3.541h-3.6718l6.696 16.918H24Zm-10.6082 0L0 20.459h3.7442l1.3693-3.5527h7.0052l1.3693 3.5528h3.7442L10.5363 3.5409Zm-.3712 10.2232 2.2914-5.9456 2.2914 5.9456Z"/></svg>',
    "gemini": f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#8E75B2"/><path transform="{_T}" fill="white" d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"/></svg>',
    "perplexity-or": f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#1FB8CD"/><path transform="{_T}" fill="white" d="M22.3977 7.0896h-2.3106V.0676l-7.5094 6.3542V.1577h-1.1554v6.1966L4.4904 0v7.0896H1.6023v10.3976h2.8882V24l6.932-6.3591v6.2005h1.1554v-6.0469l6.9318 6.1807v-6.4879h2.8882V7.0896zm-3.4657-4.531v4.531h-5.355l5.355-4.531zm-13.2862.0676 4.8691 4.4634H5.6458V2.6262zM2.7576 16.332V8.245h7.8476l-6.1149 6.1147v1.9723H2.7576zm2.8882 5.0404v-3.8852h.0001v-2.6488l5.7763-5.7764v7.0111l-5.7764 5.2993zm12.7086.0248-5.7766-5.1509V9.0618l5.7766 5.7766v6.5588zm2.8882-5.0652h-1.733v-1.9723L13.3948 8.245h7.8478v8.087z"/></svg>',
    "perplexity": f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#1FB8CD"/><path transform="{_T}" fill="white" d="M22.3977 7.0896h-2.3106V.0676l-7.5094 6.3542V.1577h-1.1554v6.1966L4.4904 0v7.0896H1.6023v10.3976h2.8882V24l6.932-6.3591v6.2005h1.1554v-6.0469l6.9318 6.1807v-6.4879h2.8882V7.0896zm-3.4657-4.531v4.531h-5.355l5.355-4.531zm-13.2862.0676 4.8691 4.4634H5.6458V2.6262zM2.7576 16.332V8.245h7.8476l-6.1149 6.1147v1.9723H2.7576zm2.8882 5.0404v-3.8852h.0001v-2.6488l5.7763-5.7764v7.0111l-5.7764 5.2993zm12.7086.0248-5.7766-5.1509V9.0618l5.7766 5.7766v6.5588zm2.8882-5.0652h-1.733v-1.9723L13.3948 8.245h7.8478v8.087z"/></svg>',
    "deepseek": f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#4D6BFE"/><path transform="{_T}" fill="white" d="M23.748 4.482c-.254-.124-.364.113-.512.234-.051.039-.094.09-.137.136-.372.397-.806.657-1.373.626-.829-.046-1.537.214-2.163.848-.133-.782-.575-1.248-1.247-1.548-.352-.156-.708-.311-.955-.65-.172-.241-.219-.51-.305-.774-.055-.16-.11-.323-.293-.35-.2-.031-.278.136-.356.276-.313.572-.434 1.202-.422 1.84.027 1.436.633 2.58 1.838 3.393.137.093.172.187.129.323-.082.28-.18.552-.266.833-.055.179-.137.217-.329.14a5.526 5.526 0 01-1.736-1.18c-.857-.828-1.631-1.742-2.597-2.458a11.365 11.365 0 00-.689-.471c-.985-.957.13-1.743.388-1.836.27-.098.093-.432-.779-.428-.872.004-1.67.295-2.687.684a3.055 3.055 0 01-.465.137 9.597 9.597 0 00-2.883-.102c-1.885.21-3.39 1.102-4.497 2.623C.082 8.606-.231 10.684.152 12.85c.403 2.284 1.569 4.175 3.36 5.653 1.858 1.533 3.997 2.284 6.438 2.14 1.482-.085 3.133-.284 4.994-1.86.47.234.962.327 1.78.397.63.059 1.236-.03 1.705-.128.735-.156.684-.837.419-.961-2.155-1.004-1.682-.595-2.113-.926 1.096-1.296 2.746-2.642 3.392-7.003.05-.347.007-.565 0-.845-.004-.17.035-.237.23-.256a4.173 4.173 0 001.545-.475c1.396-.763 1.96-2.015 2.093-3.517.02-.23-.004-.467-.247-.588zM11.581 18c-2.089-1.642-3.102-2.183-3.52-2.16-.392.024-.321.471-.235.763.09.288.207.486.371.739.114.167.192.416-.113.603-.673.416-1.842-.14-1.897-.167-1.361-.802-2.5-1.86-3.301-3.307-.774-1.393-1.224-2.887-1.298-4.482-.02-.386.093-.522.477-.592a4.696 4.696 0 011.529-.039c2.132.312 3.946 1.265 5.468 2.774.868.86 1.525 1.887 2.202 2.891.72 1.066 1.494 2.082 2.48 2.914.348.292.625.514.891.677-.802.09-2.14.11-3.054-.614zm1-6.44a.306.306 0 01.415-.287.302.302 0 01.2.288.306.306 0 01-.31.307.303.303 0 01-.304-.308zm3.11 1.596c-.2.081-.399.151-.59.16a1.245 1.245 0 01-.798-.254c-.274-.23-.47-.358-.552-.758a1.73 1.73 0 01.016-.588c.07-.327-.008-.537-.239-.727-.187-.156-.426-.199-.688-.199a.559.559 0 01-.254-.078c-.11-.054-.2-.19-.114-.358.028-.054.16-.186.192-.21.356-.202.767-.136 1.146.016.352.144.618.408 1.001.782.391.451.462.576.685.914.176.265.336.537.445.848.067.195-.019.354-.25.452z"/></svg>',
    "grok": f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#1a1a1a"/><path transform="{_T}" fill="white" d="M6.469 8.776L16.512 23h-4.464L2.005 8.776H6.47zm-.004 7.9l2.233 3.164L6.467 23H2l4.465-6.324zM22 2.582V23h-3.659V7.764L22 2.582zM22 1l-9.952 14.095-2.233-3.163L17.533 1H22z"/></svg>',
    "llama": f'<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="20" rx="5" fill="#0467DF"/><path transform="{_T}" fill="white" d="M6.915 4.03c-1.968 0-3.683 1.28-4.871 3.113C.704 9.208 0 11.883 0 14.449c0 .706.07 1.369.21 1.973a6.624 6.624 0 0 0 .265.86 5.297 5.297 0 0 0 .371.761c.696 1.159 1.818 1.927 3.593 1.927 1.497 0 2.633-.671 3.965-2.444.76-1.012 1.144-1.626 2.663-4.32l.756-1.339.186-.325c.061.1.121.196.183.3l2.152 3.595c.724 1.21 1.665 2.556 2.47 3.314 1.046.987 1.992 1.22 3.06 1.22 1.075 0 1.876-.355 2.455-.843a3.743 3.743 0 0 0 .81-.973c.542-.939.861-2.127.861-3.745 0-2.72-.681-5.357-2.084-7.45-1.282-1.912-2.957-2.93-4.716-2.93-1.047 0-2.088.467-3.053 1.308-.652.57-1.257 1.29-1.82 2.05-.69-.875-1.335-1.547-1.958-2.056-1.182-.966-2.315-1.303-3.454-1.303zm10.16 2.053c1.147 0 2.188.758 2.992 1.999 1.132 1.748 1.647 4.195 1.647 6.4 0 1.548-.368 2.9-1.839 2.9-.58 0-1.027-.23-1.664-1.004-.496-.601-1.343-1.878-2.832-4.358l-.617-1.028a44.908 44.908 0 0 0-1.255-1.98c.07-.109.141-.224.211-.327 1.12-1.667 2.118-2.602 3.358-2.602zm-10.201.553c1.265 0 2.058.791 2.675 1.446.307.327.737.871 1.234 1.579l-1.02 1.566c-.757 1.163-1.882 3.017-2.837 4.338-1.191 1.649-1.81 1.817-2.486 1.817-.524 0-1.038-.237-1.383-.794-.263-.426-.464-1.13-.464-2.046 0-2.221.63-4.535 1.66-6.088.454-.687.964-1.226 1.533-1.533a2.264 2.264 0 0 1 1.088-.285z"/></svg>',
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

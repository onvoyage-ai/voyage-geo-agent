"""Leaderboard report renderer — HTML, JSON, CSV, Markdown."""

from __future__ import annotations

import html as html_mod
from typing import TYPE_CHECKING

import structlog

from voyage_geo.stages.reporting.stage import _provider_logo
from voyage_geo.storage.filesystem import FileSystemStorage

if TYPE_CHECKING:
    from voyage_geo.types.leaderboard import LeaderboardResult
    from voyage_geo.types.query import QuerySet
    from voyage_geo.types.result import ExecutionRun

logger = structlog.get_logger()


class LeaderboardRenderer:
    def __init__(self, storage: FileSystemStorage) -> None:
        self.storage = storage

    async def render(
        self,
        run_id: str,
        result: LeaderboardResult,
        formats: list[str],
        execution_run: ExecutionRun | None = None,
        query_set: QuerySet | None = None,
    ) -> None:
        for fmt in formats:
            if fmt == "html":
                await self._render_html(run_id, result, execution_run, query_set)
            elif fmt == "json":
                await self._render_json(run_id, result)
            elif fmt == "csv":
                await self._render_csv(run_id, result)
            elif fmt == "markdown":
                await self._render_markdown(run_id, result)

    async def _render_json(self, run_id: str, result: LeaderboardResult) -> None:
        await self.storage.save_json(run_id, "reports/leaderboard.json", result)

    async def _render_csv(self, run_id: str, result: LeaderboardResult) -> None:
        import csv
        import io

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "rank", "brand", "overall_score", "mention_rate",
            "mindshare", "sentiment_score", "sentiment_label",
        ])
        for entry in result.entries:
            writer.writerow([
                entry.rank,
                entry.brand,
                f"{entry.overall_score:.1f}",
                f"{entry.mention_rate:.3f}",
                f"{entry.mindshare:.3f}",
                f"{entry.sentiment_score:.3f}",
                entry.sentiment_label,
            ])

        await self.storage.save_text(run_id, "reports/leaderboard.csv", buf.getvalue())

    async def _render_markdown(self, run_id: str, result: LeaderboardResult) -> None:
        lines = [
            f"# Leaderboard: {result.category}",
            f"*Generated {result.analyzed_at[:10]} | {len(result.brands)} brands | {result.total_queries} queries | {len(result.providers_used)} providers*\n",
            "## Rankings",
            "| Rank | Brand | Score | Mention Rate | Mindshare | Sentiment |",
            "|------|-------|-------|-------------|-----------|-----------|",
        ]

        for entry in result.entries:
            lines.append(
                f"| {entry.rank} | {entry.brand} | {entry.overall_score:.0f} | "
                f"{entry.mention_rate*100:.0f}% | {entry.mindshare*100:.1f}% | "
                f"{entry.sentiment_label} ({entry.sentiment_score:+.2f}) |"
            )

        # Provider heatmap
        if result.providers_used and result.entries:
            lines.append("\n## Provider Mention Rates")
            header = "| Brand | " + " | ".join(result.providers_used) + " |"
            sep = "|-------|" + "|".join(["-------"] * len(result.providers_used)) + "|"
            lines.append(header)
            lines.append(sep)
            for entry in result.entries:
                cells = []
                for prov in result.providers_used:
                    rate = entry.mention_rate_by_provider.get(prov, 0)
                    cells.append(f"{rate*100:.0f}%")
                lines.append(f"| {entry.brand} | " + " | ".join(cells) + " |")

        await self.storage.save_text(run_id, "reports/leaderboard.md", "\n".join(lines))

    async def _render_html(
        self,
        run_id: str,
        result: LeaderboardResult,
        execution_run: ExecutionRun | None,
        query_set: QuerySet | None,
    ) -> None:
        e = html_mod.escape

        # Header data
        category = e(result.category)
        n_brands = len(result.brands)
        n_queries = result.total_queries
        n_providers = len(result.providers_used)
        date_str = result.analyzed_at[:10]

        # Build ranking table rows
        ranking_rows = ""
        for entry in result.entries:
            score = entry.overall_score
            sc = "#3d7a5f" if score > 60 else "#96742b" if score > 30 else "#b04848"

            mr_pct = entry.mention_rate * 100
            ms_pct = entry.mindshare * 100

            s_cls = (
                "positive" if entry.sentiment_label == "positive"
                else "negative" if entry.sentiment_label == "negative"
                else "neutral"
            )

            # Advocate ranking — all provider logos ordered by mention rate
            adv_html = ""
            if entry.mention_rate_by_provider:
                sorted_provs = sorted(
                    entry.mention_rate_by_provider.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
                logos = ""
                for i, (prov, rate) in enumerate(sorted_provs):
                    on = rate > 0
                    cls = "ar-logo ar-on" if on else "ar-logo ar-off"
                    rank_label = f"#{i+1}" if on else "—"
                    logos += (
                        f'<span class="{cls}" title="{e(prov)}: {rate*100:.0f}%">'
                        f'{_provider_logo(prov)}'
                        f'</span>'
                    )
                adv_html = f'<div class="ar-strip">{logos}</div>'

            ranking_rows += (
                f'<tr>'
                f'<td class="t-rank">{entry.rank}</td>'
                f'<td class="t-name">{e(entry.brand)}</td>'
                f'<td><span class="geo-pill" style="background:{sc}12;color:{sc};border-color:{sc}30">{score:.0f}</span></td>'
                f'<td><div class="t-bar-wrap" style="width:80px">'
                f'<div class="t-bar" style="width:{mr_pct:.0f}%"></div></div>'
                f'<span class="t-pct">{mr_pct:.0f}%</span></td>'
                f'<td><div class="t-bar-wrap" style="width:80px">'
                f'<div class="t-bar t-bar-ms" style="width:{ms_pct:.0f}%"></div></div>'
                f'<span class="t-pct">{ms_pct:.1f}%</span></td>'
                f'<td class="t-sent t-{s_cls}">{entry.sentiment_score:+.2f}</td>'
                f'<td>{adv_html}</td>'
                f'</tr>'
            )

        # Provider heatmap
        heatmap_html = ""
        if result.providers_used and result.entries:
            hdr = "".join(
                f'<th><span class="heat-logo">{_provider_logo(p)}</span>{e(p)}</th>'
                for p in result.providers_used
            )
            h_rows = ""
            for entry in result.entries:
                cells = ""
                for prov in result.providers_used:
                    rate = entry.mention_rate_by_provider.get(prov, 0)
                    pct = rate * 100
                    # Heat class based on rate
                    if rate == 0:
                        hc = "h0"
                    elif rate < 0.25:
                        hc = "h1"
                    elif rate < 0.5:
                        hc = "h2"
                    else:
                        hc = "h3"
                    cells += f'<td class="{hc}">{pct:.0f}%</td>'
                h_rows += f'<tr><td>{e(entry.brand)}</td>{cells}</tr>'

            heatmap_html = (
                f'<div class="sect" id="sect-heatmap">'
                f'<div class="dl-wrap"><h3>Provider Mention Rates</h3>'
                f'<button class="dl-btn" onclick="downloadPNG(\'sect-heatmap\',\'heatmap\')"><svg viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>PNG</button></div>'
                f'<div class="panel"><table class="heat-tbl">'
                f'<thead><tr><th>Brand</th>{hdr}</tr></thead>'
                f'<tbody>{h_rows}</tbody>'
                f'</table></div></div>'
            )

        # Queries table
        queries_html = ""
        if query_set and query_set.queries:
            q_rows = ""
            for i, q in enumerate(query_set.queries, 1):
                q_rows += (
                    f'<tr>'
                    f'<td class="t-rank">{i}</td>'
                    f'<td><span class="q-strat">{e(q.strategy)}</span>'
                    f'<div class="q-cat">{e(q.category)}</div></td>'
                    f'<td class="q-text">{e(q.text)}</td>'
                    f'<td class="q-id">{e(q.id)}</td>'
                    f'</tr>'
                )
            queries_html = (
                f'<div class="sect" id="sect-queries">'
                f'<div class="dl-wrap"><h3>Queries Used</h3>'
                f'<button class="dl-btn" onclick="downloadPNG(\'sect-queries\',\'queries\')"><svg viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>PNG</button></div>'
                f'<div class="panel"><table class="q-tbl">'
                f'<thead><tr><th>#</th><th>Strategy</th><th>Query Prompt</th><th>ID</th></tr></thead>'
                f'<tbody>{q_rows}</tbody>'
                f'</table></div></div>'
            )

        # Results by provider
        provider_results_html = ""
        if execution_run and execution_run.results:
            # Group results by provider
            by_provider: dict[str, list] = {}
            for r in execution_run.results:
                by_provider.setdefault(r.provider, []).append(r)

            # Build query lookup for strategy/category
            query_lookup: dict[str, tuple[str, str]] = {}
            if query_set:
                for q in query_set.queries:
                    query_lookup[q.id] = (q.strategy, q.category)

            prov_sections = ""
            for prov in result.providers_used:
                results_for_prov = by_provider.get(prov, [])
                n_ok = sum(1 for r in results_for_prov if not r.error)
                n_err = sum(1 for r in results_for_prov if r.error)

                cards = ""
                for r in sorted(results_for_prov, key=lambda x: x.query_id):
                    strat, cat = query_lookup.get(r.query_id, ("", ""))
                    strat_badge = f'<span class="q-strat">{e(strat)}</span>' if strat else ""

                    if r.error:
                        resp_body = f'<div class="resp-err">Error: {e(r.error)}</div>'
                    else:
                        # Truncate for display, full text in expandable
                        resp_text = r.response
                        resp_body = f'<div class="resp-text">{e(resp_text)}</div>'

                    latency = f'{r.latency_ms:,}ms' if r.latency_ms else ""
                    model_info = e(r.model) if r.model else ""
                    meta_parts = [x for x in [model_info, latency] if x]

                    cards += (
                        f'<div class="resp-card">'
                        f'<div class="resp-query">{strat_badge} {e(r.query_text)}</div>'
                        f'{resp_body}'
                        f'<div class="resp-meta">{" · ".join(meta_parts)}</div>'
                        f'</div>'
                    )

                badge_text = f'{n_ok} responses'
                if n_err:
                    badge_text += f' · {n_err} errors'

                prov_sections += (
                    f'<details class="prov-detail prov-sect">'
                    f'<summary class="prov-header">'
                    f'<span class="heat-logo">{_provider_logo(prov)}</span>'
                    f'{e(prov)}'
                    f'<span class="prov-badge">{badge_text}</span>'
                    f'</summary>'
                    f'<div class="prov-body">{cards}</div>'
                    f'</details>'
                )

            provider_results_html = (
                f'<div class="sect"><h3>Raw Results by Provider</h3>'
                f'{prov_sections}</div>'
            )

        # Per-brand detail cards
        detail_cards = ""
        for entry in result.entries:
            a = entry.analysis
            score = entry.overall_score
            sc = "#3d7a5f" if score > 60 else "#96742b" if score > 30 else "#b04848"

            strengths = "".join(
                f'<li>{e(s)}</li>' for s in a.summary.strengths
            ) if a.summary.strengths else "<li>None identified</li>"
            weaknesses = "".join(
                f'<li>{e(w)}</li>' for w in a.summary.weaknesses
            ) if a.summary.weaknesses else "<li>None identified</li>"

            # Top positive/negative excerpts
            excerpts = ""
            if a.sentiment.top_positive:
                exc = a.sentiment.top_positive[0]
                excerpts += (
                    f'<div class="exc exc-pos"><div class="exc-text">'
                    f'{e(exc.text[:200])}</div>'
                    f'<div class="exc-meta">{e(exc.provider)} &middot; {exc.score:.2f}</div></div>'
                )
            if a.sentiment.top_negative:
                exc = a.sentiment.top_negative[0]
                excerpts += (
                    f'<div class="exc exc-neg"><div class="exc-text">'
                    f'{e(exc.text[:200])}</div>'
                    f'<div class="exc-meta">{e(exc.provider)} &middot; {exc.score:.2f}</div></div>'
                )

            # Build provider affinity bars — sorted by mention rate descending
            affinity_rows = ""
            sorted_provs = sorted(
                entry.mention_rate_by_provider.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            for prov_name, prov_rate in sorted_provs:
                prov_pct = prov_rate * 100
                bar_color = "#3d7a5f" if prov_rate >= 0.5 else "#96742b" if prov_rate >= 0.25 else "#a8a29e"
                affinity_rows += (
                    f'<div class="pa-row">'
                    f'<span class="pa-logo">{_provider_logo(prov_name)}</span>'
                    f'<span class="pa-name">{e(prov_name)}</span>'
                    f'<div class="pa-bar-track"><div class="pa-bar-fill" style="width:{prov_pct:.0f}%;background:{bar_color}"></div></div>'
                    f'<span class="pa-pct" style="color:{bar_color}">{prov_pct:.0f}%</span>'
                    f'</div>'
                )

            affinity_html = (
                f'<div class="prov-affinity">'
                f'<div class="prov-affinity-title">Provider Affinity</div>'
                f'{affinity_rows}'
                f'</div>'
            ) if affinity_rows else ""

            detail_cards += (
                f'<details class="lb-detail">'
                f'<summary>'
                f'<span class="lb-detail-rank">#{entry.rank}</span>'
                f'<span class="lb-detail-name">{e(entry.brand)}</span>'
                f'<span class="lb-detail-score" style="color:{sc}">{score:.0f}/100</span>'
                f'</summary>'
                f'<div class="lb-detail-body">'
                f'<div class="lb-detail-grid">'
                f'<div>'
                f'<div class="lb-detail-label">GEO Score</div>'
                f'<span class="geo-pill geo-pill-lg" style="background:{sc}12;color:{sc};border-color:{sc}30">{score:.0f}</span>'
                f'</div>'
                f'<div>'
                f'<div class="lb-detail-label">Mention Rate</div>'
                f'<div class="lb-detail-val">{entry.mention_rate*100:.0f}%</div>'
                f'<div class="lb-detail-sub">{a.mention_rate.total_mentions}/{a.mention_rate.total_responses} responses</div>'
                f'</div>'
                f'<div>'
                f'<div class="lb-detail-label">Mindshare</div>'
                f'<div class="lb-detail-val">{entry.mindshare*100:.1f}%</div>'
                f'<div class="lb-detail-sub">Rank #{a.mindshare.rank}/{a.mindshare.total_brands_detected}</div>'
                f'</div>'
                f'<div>'
                f'<div class="lb-detail-label">Sentiment</div>'
                f'<div class="lb-detail-val t-{a.sentiment.label}">{a.sentiment.label.title()}</div>'
                f'<div class="lb-detail-sub">Score: {a.sentiment.overall:.2f}</div>'
                f'</div>'
                f'</div>'
                f'{affinity_html}'
                f'<div class="lb-detail-sw">'
                f'<div><strong>Strengths</strong><ul>{strengths}</ul></div>'
                f'<div><strong>Weaknesses</strong><ul>{weaknesses}</ul></div>'
                f'</div>'
                f'{excerpts}'
                f'</div></details>'
            )

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{category} — GEO Leaderboard</title>
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

/* Masthead — dark gradient */
.mast{{display:flex;align-items:flex-end;justify-content:space-between;padding:36px 40px;border-radius:var(--r2);margin-bottom:40px;background:linear-gradient(135deg,#1a1a2e 0%,#16213e 40%,#0f3460 100%);position:relative;overflow:hidden}}
.mast::before{{content:'';position:absolute;top:-50%;right:-20%;width:60%;height:200%;background:radial-gradient(circle,rgba(255,255,255,.04) 0%,transparent 70%);pointer-events:none}}
.mast-brand{{display:flex;align-items:center;gap:14px;position:relative;z-index:1}}
.mast-icon{{width:40px;height:40px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.15);border-radius:10px;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px)}}
.mast-icon svg{{width:20px;height:20px;fill:rgba(255,255,255,.9)}}
.mast h1{{font-size:13px;font-weight:500;color:rgba(255,255,255,.5);letter-spacing:.02em}}
.mast h1 strong{{color:#fff;font-weight:800;font-size:22px;display:block;margin-top:4px;letter-spacing:-.03em}}
.mast-meta{{text-align:right;font-size:11px;color:rgba(255,255,255,.4);line-height:1.8;letter-spacing:.01em;position:relative;z-index:1}}

/* KPI strip */
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--c-border);border-radius:var(--r2);overflow:hidden;margin-bottom:48px;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.kpi{{background:var(--c-surface);padding:26px 22px}}
.kpi-val{{font-size:24px;font-weight:800;letter-spacing:-.03em;line-height:1;color:var(--c-text)}}
.kpi-label{{font-size:10px;color:var(--c-text3);text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-top:8px}}

/* Sections */
.sect{{margin-bottom:44px}}
.sect h3{{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--c-text3);font-weight:700;margin-bottom:18px;padding-left:1px}}

/* Panel */
.panel{{background:var(--c-surface);border:1px solid var(--c-border);border-radius:var(--r2);overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.03)}}

/* Ranking table */
.comp-tbl{{width:100%;border-collapse:collapse}}
.comp-tbl th{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--c-text3);font-weight:600;text-align:left;padding:13px 16px;border-bottom:1px solid var(--c-border)}}
.comp-tbl td{{padding:11px 16px;border-bottom:1px solid var(--c-surface2);font-size:13px;vertical-align:middle}}
.comp-tbl tr:last-child td{{border:none}}
.comp-tbl tr:hover{{background:var(--c-surface2)}}
.t-rank{{color:var(--c-text3);font-weight:600;width:32px;font-variant-numeric:tabular-nums}}
.t-name{{font-weight:600}}
.t-bar-wrap{{display:inline-block;height:4px;background:var(--c-surface2);border-radius:99px;overflow:hidden;vertical-align:middle;margin-right:8px}}
.t-bar{{height:100%;border-radius:99px;background:var(--c-accent)}}
.t-bar-ms{{background:var(--c-text3)}}
.t-pct{{font-size:12px;font-weight:600;color:var(--c-text2);font-variant-numeric:tabular-nums}}
.t-sent{{font-weight:700;font-variant-numeric:tabular-nums;font-size:12px}}
.t-positive{{color:var(--c-positive)}}
.t-negative{{color:var(--c-negative)}}
.t-neutral{{color:var(--c-text3)}}

/* GEO Score pill */
.geo-pill{{display:inline-block;font-size:14px;font-weight:800;padding:5px 12px;border-radius:8px;border:1px solid;letter-spacing:-.02em;font-variant-numeric:tabular-nums;min-width:42px;text-align:center}}
.geo-pill-lg{{font-size:22px;padding:8px 16px;border-radius:10px;min-width:56px}}

/* AI Consensus dots */
.consensus{{display:flex;align-items:center;gap:8px}}
.consensus-dots{{display:flex;gap:3px;align-items:center}}
.cd{{width:16px;height:16px;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden;border:1.5px solid var(--c-border)}}
.cd svg{{width:10px;height:10px;display:block}}
.cd-on{{border-color:var(--c-positive);background:var(--c-positive-dim)}}
.cd-on svg{{opacity:1}}
.cd-off{{opacity:.3;border-color:var(--c-border)}}
.cd-off svg{{opacity:.25}}
.consensus-count{{font-size:11px;font-weight:700;color:var(--c-text2);white-space:nowrap;font-variant-numeric:tabular-nums}}

/* Advocate ranking strip */
.ar-strip{{display:flex;gap:3px;align-items:center}}
.ar-logo{{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden;transition:transform .15s,box-shadow .15s;border:1.5px solid transparent;position:relative}}
.ar-logo svg{{width:14px;height:14px;display:block}}
.ar-on{{background:var(--c-surface);border-color:var(--c-border2);box-shadow:0 1px 2px rgba(0,0,0,.06)}}
.ar-on:first-child{{border-color:var(--c-positive);box-shadow:0 0 0 2px rgba(43,122,75,.15);transform:scale(1.15);z-index:1}}
.ar-on:hover{{transform:scale(1.2);box-shadow:0 2px 6px rgba(0,0,0,.12);z-index:2}}
.ar-off{{opacity:.2}}

/* Download button */
.dl-wrap{{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}}
.dl-wrap h3{{margin-bottom:0}}
.dl-btn{{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;font-size:11px;font-weight:600;color:var(--c-text3);background:var(--c-surface);border:1px solid var(--c-border);border-radius:6px;cursor:pointer;transition:all .15s;letter-spacing:.02em}}
.dl-btn:hover{{background:var(--c-surface2);color:var(--c-text);border-color:var(--c-border2)}}
.dl-btn svg{{width:14px;height:14px;fill:currentColor}}

/* Heatmap */
.heat-tbl{{width:100%;border-collapse:collapse}}
.heat-tbl th{{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--c-text3);font-weight:600;padding:12px 10px;border-bottom:1px solid var(--c-border);text-align:center}}
.heat-tbl th:first-child{{text-align:left;padding-left:16px}}
.heat-tbl td{{padding:10px;text-align:center;font-size:12px;font-weight:700;border-bottom:1px solid var(--c-surface2)}}
.heat-tbl td:first-child{{text-align:left;padding-left:16px;font-weight:500}}
.heat-tbl tr:last-child td{{border:none}}
.heat-logo{{width:16px;height:16px;display:inline-block;vertical-align:middle;margin-right:4px}}
.heat-logo svg{{width:16px;height:16px;display:block}}
.h0{{color:var(--c-text4)}}
.h1{{color:var(--c-positive);background:rgba(61,122,95,.05)}}
.h2{{color:var(--c-positive);background:rgba(61,122,95,.1)}}
.h3{{color:var(--c-positive);background:rgba(61,122,95,.16)}}

/* Detail cards */
.lb-detail{{background:var(--c-surface);border:1px solid var(--c-border);border-radius:var(--r2);margin-bottom:12px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.03)}}
.lb-detail summary{{cursor:pointer;padding:16px 20px;display:flex;align-items:center;gap:14px;font-size:14px;transition:background .15s}}
.lb-detail summary:hover{{background:var(--c-surface2)}}
.lb-detail-rank{{font-size:12px;font-weight:700;color:var(--c-text3);width:30px}}
.lb-detail-name{{font-weight:700;flex:1;color:var(--c-text)}}
.lb-detail-score{{font-weight:800;font-size:13px}}
.lb-detail-body{{padding:20px 24px;border-top:1px solid var(--c-border)}}
.lb-detail-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:20px}}
.lb-detail-label{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--c-text3);font-weight:600;margin-bottom:8px}}
.lb-detail-val{{font-size:20px;font-weight:800;letter-spacing:-.02em}}
.lb-detail-sub{{font-size:11px;color:var(--c-text3);margin-top:3px}}
.lb-detail-sw{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:16px}}
.lb-detail-sw strong{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--c-text3);font-weight:600}}
.lb-detail-sw ul{{margin-top:8px;padding-left:16px;font-size:12px;color:var(--c-text2);line-height:1.7}}

/* Provider affinity bars (detail cards) */
.prov-affinity{{margin-bottom:20px}}
.prov-affinity-title{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--c-text3);font-weight:600;margin-bottom:12px}}
.pa-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.pa-row:last-child{{margin:0}}
.pa-logo{{width:22px;height:22px;flex-shrink:0;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;background:var(--c-surface2);border:1px solid var(--c-border)}}
.pa-logo svg{{width:14px;height:14px;display:block}}
.pa-name{{font-size:11px;font-weight:600;color:var(--c-text2);width:90px;flex-shrink:0}}
.pa-bar-track{{flex:1;height:8px;background:var(--c-surface2);border-radius:99px;overflow:hidden}}
.pa-bar-fill{{height:100%;border-radius:99px;transition:width .3s}}
.pa-pct{{font-size:11px;font-weight:700;width:36px;text-align:right;flex-shrink:0;font-variant-numeric:tabular-nums}}

/* Excerpts */
.exc{{padding:14px 18px;border-left:2px solid var(--c-border);margin-bottom:10px;border-radius:0 6px 6px 0;background:var(--c-surface2)}}
.exc:last-child{{margin:0}}
.exc-pos{{border-left-color:var(--c-positive)}}
.exc-neg{{border-left-color:var(--c-negative)}}
.exc-text{{font-size:13px;color:var(--c-text2);line-height:1.65}}
.exc-meta{{font-size:11px;color:var(--c-text3);margin-top:6px;font-weight:500}}

/* Queries table */
.q-tbl{{width:100%;border-collapse:collapse}}
.q-tbl th{{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--c-text3);font-weight:600;text-align:left;padding:12px 16px;border-bottom:1px solid var(--c-border)}}
.q-tbl td{{padding:10px 16px;border-bottom:1px solid var(--c-surface2);font-size:13px;vertical-align:top}}
.q-tbl tr:last-child td{{border:none}}
.q-tbl tr:hover{{background:var(--c-surface2)}}
.q-id{{font-family:monospace;font-size:11px;color:var(--c-text3)}}
.q-strat{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;padding:2px 8px;border-radius:4px;background:var(--c-accent-dim);color:var(--c-text2);white-space:nowrap}}
.q-cat{{font-size:10px;color:var(--c-text3);margin-top:2px}}
.q-text{{font-weight:500;line-height:1.5}}

/* Provider results */
.prov-sect{{margin-bottom:16px}}
.prov-header{{cursor:pointer;padding:16px 20px;display:flex;align-items:center;gap:12px;font-size:14px;font-weight:700;background:var(--c-surface);border:1px solid var(--c-border);border-radius:var(--r2);transition:background .15s}}
.prov-header:hover{{background:var(--c-surface2)}}
.prov-header .heat-logo{{width:20px;height:20px}}
.prov-header .heat-logo svg{{width:20px;height:20px}}
.prov-badge{{font-size:11px;font-weight:600;color:var(--c-text3);margin-left:auto}}
.prov-body{{border:1px solid var(--c-border);border-top:none;border-radius:0 0 var(--r2) var(--r2);overflow:hidden}}
.prov-detail[open] .prov-header{{border-radius:var(--r2) var(--r2) 0 0}}
.resp-card{{padding:16px 20px;border-bottom:1px solid var(--c-surface2)}}
.resp-card:last-child{{border:none}}
.resp-query{{font-size:12px;font-weight:700;color:var(--c-text);margin-bottom:6px;display:flex;align-items:center;gap:8px}}
.resp-query .q-strat{{font-size:9px}}
.resp-text{{font-size:12px;color:var(--c-text2);line-height:1.7;white-space:pre-wrap;max-height:200px;overflow-y:auto;background:var(--c-surface2);padding:12px 14px;border-radius:6px}}
.resp-meta{{font-size:10px;color:var(--c-text4);margin-top:6px}}
.resp-err{{color:var(--c-negative);font-weight:600;font-size:12px}}
.resp-toggle{{font-size:11px;color:var(--c-text3);cursor:pointer;text-decoration:underline;margin-top:4px;display:inline-block}}

/* Footer */
.foot{{margin-top:56px;padding-top:24px;border-top:1px solid var(--c-border);display:flex;justify-content:space-between;font-size:11px;color:var(--c-text3)}}

@media(max-width:800px){{
.wrap{{padding:32px 20px 60px}}
.kpis{{grid-template-columns:repeat(2,1fr)}}
.lb-detail-grid{{grid-template-columns:repeat(2,1fr)}}
.lb-detail-sw{{grid-template-columns:1fr}}
}}
@media print{{
body{{background:#fff}}
.panel,.lb-detail{{box-shadow:none;border-color:#e0e0e0}}
.kpis{{box-shadow:none}}
}}
</style>
</head>
<body>
<div class="wrap">

<div class="mast">
<div class="mast-brand">
<div class="mast-icon"><svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg></div>
<h1>GEO Leaderboard<strong>{category}</strong></h1>
</div>
<div class="mast-meta">Run ID: {e(result.run_id)}<br>{date_str} &middot; {n_providers} AI models &middot; {n_queries} queries</div>
</div>

<div class="kpis">
<div class="kpi"><div class="kpi-val">{n_brands}</div><div class="kpi-label">Brands Analyzed</div></div>
<div class="kpi"><div class="kpi-val">{n_queries}</div><div class="kpi-label">Shared Queries</div></div>
<div class="kpi"><div class="kpi-val">{n_providers}</div><div class="kpi-label">AI Providers</div></div>
<div class="kpi"><div class="kpi-val">{e(result.entries[0].brand) if result.entries else '—'}</div><div class="kpi-label">#1 Ranked</div></div>
</div>

<div class="sect" id="sect-rankings">
<div class="dl-wrap"><h3>Rankings</h3><button class="dl-btn" onclick="downloadPNG('sect-rankings','rankings')"><svg viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>PNG</button></div>
<div class="panel">
<table class="comp-tbl">
<thead><tr>
<th></th><th>Brand</th><th>GEO Score</th><th>Mentions</th><th>Mindshare</th><th>Sentiment</th><th>Advocate</th>
</tr></thead>
<tbody>{ranking_rows}</tbody>
</table>
</div></div>

{heatmap_html}

{queries_html}

{provider_results_html}

<div class="sect"><h3>Brand Details</h3>
{detail_cards}
</div>

<div class="foot"><span>Generated by Voyage GEO</span><span>{date_str}</span></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script>
function downloadPNG(sectionId, filename) {{
  var el = document.getElementById(sectionId);
  var btn = el.querySelector('.dl-btn');
  var origText = btn.innerHTML;
  btn.innerHTML = 'Capturing...';
  btn.style.pointerEvents = 'none';
  html2canvas(el, {{
    backgroundColor: '#f8f8f7',
    scale: 2,
    useCORS: true,
    logging: false,
  }}).then(function(canvas) {{
    var link = document.createElement('a');
    link.download = filename + '.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
    btn.innerHTML = origText;
    btn.style.pointerEvents = '';
  }}).catch(function() {{
    btn.innerHTML = origText;
    btn.style.pointerEvents = '';
  }});
}}
</script>
</body></html>"""

        await self.storage.save_text(run_id, "reports/leaderboard.html", html)

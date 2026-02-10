import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import Handlebars from 'handlebars';
import type { ReportRenderer, ReportData } from './types.js';
import type { FileSystemStorage } from '../../../storage/filesystem.js';

const TEMPLATE = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GEO Report: {{brand.name}}</title>
<style>
:root { --primary: #4f46e5; --bg: #f9fafb; --card: #fff; --text: #111827; --muted: #6b7280; --border: #e5e7eb; --green: #059669; --red: #dc2626; --yellow: #d97706; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
.container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
h1 { font-size: 2rem; margin-bottom: 0.5rem; }
h2 { font-size: 1.4rem; margin: 2rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--primary); }
.meta { color: var(--muted); margin-bottom: 2rem; }
.score-card { display: inline-flex; align-items: center; gap: 0.5rem; padding: 1rem 1.5rem; background: var(--primary); color: #fff; border-radius: 12px; font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
.card-label { font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
.card-value { font-size: 1.8rem; font-weight: 700; margin-top: 0.25rem; }
.positive { color: var(--green); } .negative { color: var(--red); } .neutral { color: var(--yellow); }
ul { padding-left: 1.5rem; margin: 0.5rem 0; }
li { margin: 0.3rem 0; }
table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
th { background: var(--bg); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; }
.badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }
.badge-positive { background: #d1fae5; color: #065f46; }
.badge-negative { background: #fee2e2; color: #991b1b; }
.badge-neutral { background: #fef3c7; color: #92400e; }
.footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.85rem; }
</style>
</head>
<body>
<div class="container">
<h1>GEO Analysis: {{brand.name}}</h1>
<div class="meta">Run ID: {{runId}} | Generated: {{generatedAt}}</div>

<div class="score-card">AI Visibility Score: {{analysis.summary.overallScore}}%</div>

<h2>Executive Summary</h2>
<p><strong>{{analysis.summary.headline}}</strong></p>
<h3 style="margin-top:1rem">Key Findings</h3>
<ul>
{{#each analysis.summary.keyFindings}}<li>{{this}}</li>{{/each}}
</ul>

{{#if analysis.summary.strengths.length}}
<h3 style="margin-top:1rem">Strengths</h3>
<ul>{{#each analysis.summary.strengths}}<li>{{this}}</li>{{/each}}</ul>
{{/if}}

{{#if analysis.summary.weaknesses.length}}
<h3 style="margin-top:1rem">Weaknesses</h3>
<ul>{{#each analysis.summary.weaknesses}}<li>{{this}}</li>{{/each}}</ul>
{{/if}}

{{#if analysis.summary.recommendations.length}}
<h3 style="margin-top:1rem">Recommendations</h3>
<ul>{{#each analysis.summary.recommendations}}<li>{{this}}</li>{{/each}}</ul>
{{/if}}

<h2>Metrics Overview</h2>
<div class="grid">
{{#if analysis.mentionRate}}
<div class="card">
<div class="card-label">Mention Rate</div>
<div class="card-value">{{analysis.mentionRate.overall}}%</div>
<div style="color:var(--muted);font-size:0.85rem">{{analysis.mentionRate.totalMentions}}/{{analysis.mentionRate.totalResponses}} responses</div>
</div>
{{/if}}
{{#if analysis.mindshare}}
<div class="card">
<div class="card-label">Mindshare</div>
<div class="card-value">{{analysis.mindshare.overall}}%</div>
<div style="color:var(--muted);font-size:0.85rem">Rank #{{analysis.mindshare.rank}}</div>
</div>
{{/if}}
{{#if analysis.sentiment}}
<div class="card">
<div class="card-label">Sentiment</div>
<div class="card-value {{analysis.sentiment.label}}">{{analysis.sentiment.label}}</div>
<div style="color:var(--muted);font-size:0.85rem">Score: {{formatNumber analysis.sentiment.overall}}</div>
</div>
{{/if}}
{{#if analysis.citations}}
<div class="card">
<div class="card-label">Citations</div>
<div class="card-value">{{analysis.citations.totalCitations}}</div>
<div style="color:var(--muted);font-size:0.85rem">{{analysis.citations.uniqueSourcesCited}} unique sources</div>
</div>
{{/if}}
</div>

{{#if analysis.mentionRate.byProvider}}
<h2>Mention Rate by Provider</h2>
<table>
<thead><tr><th>Provider</th><th>Mention Rate</th></tr></thead>
<tbody>
{{#each analysis.mentionRate.byProvider}}<tr><td>{{@key}}</td><td>{{this}}%</td></tr>{{/each}}
</tbody>
</table>
{{/if}}

{{#if analysis.competitorAnalysis.competitors}}
<h2>Competitor Comparison</h2>
<table>
<thead><tr><th>Brand</th><th>Mention Rate</th><th>Sentiment</th><th>Mindshare</th></tr></thead>
<tbody>
{{#each analysis.competitorAnalysis.competitors}}
<tr>
<td><strong>{{this.name}}</strong></td>
<td>{{this.mentionRate}}%</td>
<td>{{formatNumber this.sentiment}}</td>
<td>{{this.mindshare}}%</td>
</tr>
{{/each}}
</tbody>
</table>
{{/if}}

{{#if analysis.positioning}}
<h2>Brand Positioning</h2>
<p>Primary position: <strong>{{analysis.positioning.primaryPosition}}</strong></p>
{{#if analysis.positioning.attributes.length}}
<table>
<thead><tr><th>Attribute</th><th>Frequency</th><th>Sentiment</th></tr></thead>
<tbody>
{{#each analysis.positioning.attributes}}
<tr><td>{{this.attribute}}</td><td>{{this.frequency}}</td><td>{{formatNumber this.sentiment}}</td></tr>
{{/each}}
</tbody>
</table>
{{/if}}
{{/if}}

<div class="footer">
Generated by <strong>Voyage GEO</strong> — Open Source Generative Engine Optimization
</div>
</div>
</body>
</html>`;

export class HtmlRenderer implements ReportRenderer {
  name = 'html';
  format = 'html';

  async render(data: ReportData, storage: FileSystemStorage): Promise<string> {
    Handlebars.registerHelper('formatNumber', (num: number) => {
      if (typeof num !== 'number') return String(num);
      return num.toFixed(3);
    });

    const template = Handlebars.compile(TEMPLATE);
    const html = template(data);

    const filePath = join(storage.getRunPath(data.runId), 'reports', 'report.html');
    await writeFile(filePath, html, 'utf-8');

    return html;
  }
}

import type { ReportRenderer, ReportData } from './types.js';
import type { FileSystemStorage } from '../../../storage/filesystem.js';

export class JsonRenderer implements ReportRenderer {
  name = 'json';
  format = 'json';

  async render(data: ReportData, storage: FileSystemStorage): Promise<string> {
    const report = {
      meta: {
        runId: data.runId,
        brand: data.brand.name,
        generatedAt: data.generatedAt,
        website: data.brand.website,
      },
      summary: data.analysis.summary,
      mindshare: data.analysis.mindshare,
      mentionRate: data.analysis.mentionRate,
      sentiment: data.analysis.sentiment,
      positioning: data.analysis.positioning,
      citations: data.analysis.citations,
      competitors: data.analysis.competitorAnalysis,
    };

    const json = JSON.stringify(report, null, 2);
    await storage.saveJSON(data.runId, 'reports/report.json', report);
    return json;
  }
}

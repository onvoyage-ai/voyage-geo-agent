import type { ReportRenderer, ReportData } from './types.js';
import type { FileSystemStorage } from '../../../storage/filesystem.js';

export class CsvRenderer implements ReportRenderer {
  name = 'csv';
  format = 'csv';

  async render(data: ReportData, storage: FileSystemStorage): Promise<string> {
    // Summary CSV
    const summaryData = [
      {
        metric: 'Overall Score',
        value: data.analysis.summary.overallScore,
      },
      {
        metric: 'Mention Rate',
        value: data.analysis.mentionRate?.overall ?? 'N/A',
      },
      {
        metric: 'Mindshare',
        value: data.analysis.mindshare?.overall ?? 'N/A',
      },
      {
        metric: 'Sentiment',
        value: data.analysis.sentiment?.overall ?? 'N/A',
      },
      {
        metric: 'Sentiment Label',
        value: data.analysis.sentiment?.label ?? 'N/A',
      },
      {
        metric: 'Citation Rate',
        value: data.analysis.citations?.citationRate ?? 'N/A',
      },
      {
        metric: 'Competitor Rank',
        value: data.analysis.competitorAnalysis?.brandRank ?? 'N/A',
      },
    ];

    await storage.saveCSV(data.runId, 'reports/summary.csv', summaryData);

    // Competitor comparison CSV
    if (data.analysis.competitorAnalysis?.competitors) {
      await storage.saveCSV(
        data.runId,
        'reports/competitors.csv',
        data.analysis.competitorAnalysis.competitors.map((c) => ({
          brand: c.name,
          mentionRate: c.mentionRate,
          sentiment: c.sentiment,
          mindshare: c.mindshare,
        })),
      );
    }

    return 'CSV reports generated';
  }
}

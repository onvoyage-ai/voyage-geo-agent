import type { Analyzer } from './types.js';
import type { QueryResult } from '../../../types/result.js';
import type { BrandProfile } from '../../../types/brand.js';
import type { CitationScore, CitationSource } from '../../../types/analysis.js';
import { groupBy, percentage } from '../statistics.js';

const URL_REGEX = /https?:\/\/[^\s)<>]+/g;

export class CitationAnalyzer implements Analyzer {
  name = 'citation';

  analyze(results: QueryResult[], _profile: BrandProfile): CitationScore {
    const validResults = results.filter((r) => !r.error && r.response);

    const sourceCounts = new Map<string, { count: number; providers: Set<string> }>();
    let totalCitations = 0;
    let responsesWithCitations = 0;

    for (const result of validResults) {
      const urls = result.response.match(URL_REGEX) || [];
      if (urls.length > 0) {
        responsesWithCitations++;
      }

      for (const url of urls) {
        totalCitations++;
        try {
          const hostname = new URL(url).hostname.replace(/^www\./, '');
          const existing = sourceCounts.get(hostname) || { count: 0, providers: new Set() };
          existing.count++;
          existing.providers.add(result.provider);
          sourceCounts.set(hostname, existing);
        } catch {
          // Invalid URL, skip
        }
      }
    }

    const citationRate = percentage(responsesWithCitations, validResults.length);

    // By provider
    const byProvider: Record<string, number> = {};
    const providerGroups = groupBy(validResults, (r) => r.provider);
    for (const [provider, providerResults] of providerGroups) {
      let providerCitations = 0;
      for (const result of providerResults) {
        const urls = result.response.match(URL_REGEX) || [];
        providerCitations += urls.length;
      }
      byProvider[provider] = providerCitations;
    }

    // Top sources
    const topSources: CitationSource[] = Array.from(sourceCounts.entries())
      .map(([source, data]) => ({
        source,
        count: data.count,
        providers: Array.from(data.providers),
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return {
      totalCitations,
      uniqueSourcesCited: sourceCounts.size,
      citationRate,
      byProvider,
      topSources,
    };
  }
}

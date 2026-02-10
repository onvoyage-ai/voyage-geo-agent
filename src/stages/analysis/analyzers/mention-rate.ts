import type { Analyzer } from './types.js';
import type { QueryResult } from '../../../types/result.js';
import type { BrandProfile } from '../../../types/brand.js';
import type { MentionRateScore } from '../../../types/analysis.js';
import { containsBrand } from '../../../utils/text.js';
import { groupBy, percentage } from '../statistics.js';

export class MentionRateAnalyzer implements Analyzer {
  name = 'mention-rate';

  analyze(results: QueryResult[], profile: BrandProfile): MentionRateScore {
    const validResults = results.filter((r) => !r.error && r.response);
    const totalResponses = validResults.length;

    let totalMentions = 0;
    for (const result of validResults) {
      if (containsBrand(result.response, profile.name)) {
        totalMentions++;
      }
    }

    const overall = percentage(totalMentions, totalResponses);

    // By provider
    const byProvider: Record<string, number> = {};
    const providerGroups = groupBy(validResults, (r) => r.provider);
    for (const [provider, providerResults] of providerGroups) {
      let count = 0;
      for (const r of providerResults) {
        if (containsBrand(r.response, profile.name)) count++;
      }
      byProvider[provider] = percentage(count, providerResults.length);
    }

    // By category
    const byCategory: Record<string, number> = {};

    return {
      overall,
      byProvider,
      byCategory,
      totalMentions,
      totalResponses,
    };
  }
}

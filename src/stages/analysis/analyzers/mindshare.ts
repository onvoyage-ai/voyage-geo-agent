import type { Analyzer } from './types.js';
import type { QueryResult } from '../../../types/result.js';
import type { BrandProfile } from '../../../types/brand.js';
import type { MindshareScore } from '../../../types/analysis.js';
import { containsBrand, extractBrandMentions } from '../../../utils/text.js';
import { groupBy, percentage } from '../statistics.js';

export class MindshareAnalyzer implements Analyzer {
  name = 'mindshare';

  analyze(results: QueryResult[], profile: BrandProfile): MindshareScore {
    const validResults = results.filter((r) => !r.error && r.response);
    const allBrands = [profile.name, ...profile.competitors];

    // Count responses mentioning each brand
    const brandMentionCounts = new Map<string, number>();
    for (const brand of allBrands) {
      let count = 0;
      for (const result of validResults) {
        if (containsBrand(result.response, brand)) {
          count++;
        }
      }
      brandMentionCounts.set(brand, count);
    }

    const totalMentions = Array.from(brandMentionCounts.values()).reduce((s, v) => s + v, 0);
    const brandMentions = brandMentionCounts.get(profile.name) || 0;
    const overall = totalMentions > 0 ? percentage(brandMentions, totalMentions) : 0;

    // By provider
    const byProvider: Record<string, number> = {};
    const providerGroups = groupBy(validResults, (r) => r.provider);
    for (const [provider, providerResults] of providerGroups) {
      const mentions = extractBrandMentions(
        providerResults.map((r) => r.response).join(' '),
        allBrands,
      );
      const providerTotal = Array.from(mentions.values()).reduce((s, v) => s + v, 0);
      const providerBrand = mentions.get(profile.name) || 0;
      byProvider[provider] = providerTotal > 0 ? percentage(providerBrand, providerTotal) : 0;
    }

    // By category (using query text to infer category)
    const byCategory: Record<string, number> = {};

    // Rank
    const sorted = Array.from(brandMentionCounts.entries())
      .sort(([, a], [, b]) => b - a);
    const rank = sorted.findIndex(([name]) => name === profile.name) + 1;

    return {
      overall,
      byProvider,
      byCategory,
      rank: rank || 1,
      totalBrandsDetected: allBrands.length,
    };
  }
}

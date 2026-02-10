import type { Analyzer } from './types.js';
import type { QueryResult } from '../../../types/result.js';
import type { BrandProfile } from '../../../types/brand.js';
import type { PositioningScore, PositionAttribute } from '../../../types/analysis.js';
import { containsBrand, extractSentences } from '../../../utils/text.js';
import { groupBy } from '../statistics.js';
import Sentiment from 'sentiment';

const sentimentAnalyzer = new Sentiment();

const POSITION_KEYWORDS = [
  'leader', 'best', 'top', 'popular', 'powerful', 'innovative', 'reliable',
  'affordable', 'premium', 'enterprise', 'simple', 'easy', 'fast', 'secure',
  'scalable', 'flexible', 'modern', 'comprehensive', 'lightweight', 'robust',
  'free', 'open-source', 'collaborative', 'intuitive', 'customizable',
];

export class PositioningAnalyzer implements Analyzer {
  name = 'positioning';

  analyze(results: QueryResult[], profile: BrandProfile): PositioningScore {
    const validResults = results.filter((r) => !r.error && r.response);

    // Find attributes associated with the brand
    const attributeCounts = new Map<string, { count: number; sentiments: number[] }>();

    for (const result of validResults) {
      const sentences = extractSentences(result.response)
        .filter((s) => containsBrand(s, profile.name));

      for (const sentence of sentences) {
        const lower = sentence.toLowerCase();
        for (const keyword of POSITION_KEYWORDS) {
          if (lower.includes(keyword)) {
            const existing = attributeCounts.get(keyword) || { count: 0, sentiments: [] };
            existing.count++;
            existing.sentiments.push(sentimentAnalyzer.analyze(sentence).comparative);
            attributeCounts.set(keyword, existing);
          }
        }
      }
    }

    // Sort by frequency
    const attributes: PositionAttribute[] = Array.from(attributeCounts.entries())
      .map(([attribute, data]) => ({
        attribute,
        frequency: data.count,
        sentiment: data.sentiments.reduce((a, b) => a + b, 0) / data.sentiments.length,
      }))
      .sort((a, b) => b.frequency - a.frequency);

    const primaryPosition = attributes.length > 0
      ? attributes.slice(0, 3).map((a) => a.attribute).join(', ')
      : 'unpositioned';

    // By provider
    const byProvider: Record<string, string> = {};
    const providerGroups = groupBy(validResults, (r) => r.provider);
    for (const [provider, providerResults] of providerGroups) {
      const providerAttributes = new Map<string, number>();
      for (const result of providerResults) {
        const sentences = extractSentences(result.response)
          .filter((s) => containsBrand(s, profile.name));
        for (const sentence of sentences) {
          const lower = sentence.toLowerCase();
          for (const keyword of POSITION_KEYWORDS) {
            if (lower.includes(keyword)) {
              providerAttributes.set(keyword, (providerAttributes.get(keyword) || 0) + 1);
            }
          }
        }
      }
      const top = Array.from(providerAttributes.entries())
        .sort(([, a], [, b]) => b - a)
        .slice(0, 3)
        .map(([k]) => k)
        .join(', ');
      byProvider[provider] = top || 'unpositioned';
    }

    return {
      primaryPosition,
      attributes: attributes.slice(0, 10),
      byProvider,
    };
  }
}

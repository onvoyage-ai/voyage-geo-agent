import Sentiment from 'sentiment';
import type { Analyzer } from './types.js';
import type { QueryResult } from '../../../types/result.js';
import type { BrandProfile } from '../../../types/brand.js';
import type { CompetitorAnalysis, CompetitorScore } from '../../../types/analysis.js';
import { containsBrand, extractSentences, countOccurrences } from '../../../utils/text.js';
import { percentage, mean } from '../statistics.js';

const sentimentAnalyzer = new Sentiment();

export class CompetitorAnalyzer implements Analyzer {
  name = 'competitor';

  analyze(results: QueryResult[], profile: BrandProfile): CompetitorAnalysis {
    const validResults = results.filter((r) => !r.error && r.response);
    const allBrands = [profile.name, ...profile.competitors];

    const scores: CompetitorScore[] = allBrands.map((brand) => {
      let mentionCount = 0;
      let totalOccurrences = 0;
      const sentiments: number[] = [];

      for (const result of validResults) {
        if (containsBrand(result.response, brand)) {
          mentionCount++;
          totalOccurrences += countOccurrences(result.response, brand);

          const sentences = extractSentences(result.response)
            .filter((s) => containsBrand(s, brand));
          for (const sentence of sentences) {
            sentiments.push(sentimentAnalyzer.analyze(sentence).comparative);
          }
        }
      }

      return {
        name: brand,
        mentionRate: percentage(mentionCount, validResults.length),
        sentiment: mean(sentiments),
        mindshare: totalOccurrences,
      };
    });

    // Sort by mindshare (total occurrences)
    scores.sort((a, b) => b.mindshare - a.mindshare);

    // Normalize mindshare to percentages
    const totalMindshare = scores.reduce((s, c) => s + c.mindshare, 0);
    if (totalMindshare > 0) {
      for (const score of scores) {
        score.mindshare = percentage(score.mindshare, totalMindshare);
      }
    }

    const brandRank = scores.findIndex((s) => s.name === profile.name) + 1;

    return {
      competitors: scores,
      brandRank: brandRank || 1,
    };
  }
}

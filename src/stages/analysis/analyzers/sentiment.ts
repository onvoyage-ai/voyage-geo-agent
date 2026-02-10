import Sentiment from 'sentiment';
import type { Analyzer } from './types.js';
import type { QueryResult } from '../../../types/result.js';
import type { BrandProfile } from '../../../types/brand.js';
import type { SentimentScore, SentimentExcerpt } from '../../../types/analysis.js';
import { containsBrand, extractSentences } from '../../../utils/text.js';
import { groupBy, mean, standardDeviation } from '../statistics.js';

const sentiment = new Sentiment();

interface ScoredSentence {
  text: string;
  score: number;
  provider: string;
  category?: string;
}

function scoreLabel(score: number): 'positive' | 'neutral' | 'negative' {
  if (score > 0.05) return 'positive';
  if (score < -0.05) return 'negative';
  return 'neutral';
}

export class SentimentAnalyzer implements Analyzer {
  name = 'sentiment';

  analyze(results: QueryResult[], profile: BrandProfile): SentimentScore {
    const validResults = results.filter((r) => !r.error && r.response);
    const allSentences: ScoredSentence[] = [];

    for (const result of validResults) {
      const sentences = extractSentences(result.response)
        .filter((s) => containsBrand(s, profile.name));

      for (const sentence of sentences) {
        const analysis = sentiment.analyze(sentence);
        allSentences.push({
          text: sentence,
          score: analysis.comparative,
          provider: result.provider,
        });
      }
    }

    const scores = allSentences.map((s) => s.score);
    const overall = mean(scores);
    const label = scoreLabel(overall);
    const stddev = standardDeviation(scores);
    // Confidence: higher when stddev is low and we have enough samples
    const sampleFactor = Math.min(allSentences.length / 10, 1);
    const varianceFactor = Math.max(0, 1 - stddev);
    const confidence = Math.round(sampleFactor * varianceFactor * 100) / 100;

    let positiveCount = 0;
    let neutralCount = 0;
    let negativeCount = 0;
    for (const s of allSentences) {
      const l = scoreLabel(s.score);
      if (l === 'positive') positiveCount++;
      else if (l === 'negative') negativeCount++;
      else neutralCount++;
    }

    // By provider
    const byProvider: Record<string, number> = {};
    const byProviderLabel: Record<string, 'positive' | 'neutral' | 'negative'> = {};
    const providerGroups = groupBy(allSentences, (s) => s.provider);
    for (const [provider, providerSentences] of providerGroups) {
      const providerScore = mean(providerSentences.map((s) => s.score));
      byProvider[provider] = providerScore;
      byProviderLabel[provider] = scoreLabel(providerScore);
    }

    // By category — use queryId to look up category from query results
    const byCategory: Record<string, number> = {};
    const categoryGroups = groupBy(validResults, (r) => {
      // Extract category from queryId prefix: kw=keyword, ps=persona, cp=competitor, in=intent
      const prefix = r.queryId.split('-')[0];
      const map: Record<string, string> = { kw: 'keyword', ps: 'persona', cp: 'competitor', in: 'intent' };
      return map[prefix] || 'unknown';
    });
    for (const [category, catResults] of categoryGroups) {
      const catScores: number[] = [];
      for (const result of catResults) {
        const sentences = extractSentences(result.response)
          .filter((s) => containsBrand(s, profile.name));
        for (const sentence of sentences) {
          catScores.push(sentiment.analyze(sentence).comparative);
        }
      }
      if (catScores.length > 0) {
        byCategory[category] = mean(catScores);
      }
    }

    // Top positive & negative excerpts
    const sorted = [...allSentences].sort((a, b) => b.score - a.score);
    const topPositive: SentimentExcerpt[] = sorted
      .filter((s) => s.score > 0.05)
      .slice(0, 5)
      .map((s) => ({ text: s.text.slice(0, 200), score: s.score, provider: s.provider }));

    const topNegative: SentimentExcerpt[] = sorted
      .filter((s) => s.score < -0.05)
      .slice(-5)
      .reverse()
      .map((s) => ({ text: s.text.slice(0, 200), score: s.score, provider: s.provider }));

    return {
      overall,
      label,
      confidence,
      byProvider,
      byProviderLabel,
      byCategory,
      positiveCount,
      neutralCount,
      negativeCount,
      totalSentences: allSentences.length,
      topPositive,
      topNegative,
    };
  }
}

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { BrandProfile } from '../../src/types/brand.js';
import type { QueryResult } from '../../src/types/result.js';
import { MindshareAnalyzer } from '../../src/stages/analysis/analyzers/mindshare.js';
import { MentionRateAnalyzer } from '../../src/stages/analysis/analyzers/mention-rate.js';
import { SentimentAnalyzer } from '../../src/stages/analysis/analyzers/sentiment.js';
import { CompetitorAnalyzer } from '../../src/stages/analysis/analyzers/competitor.js';
import { CitationAnalyzer } from '../../src/stages/analysis/analyzers/citation.js';
import { PositioningAnalyzer } from '../../src/stages/analysis/analyzers/positioning.js';

const profile: BrandProfile = JSON.parse(
  readFileSync(resolve('test/fixtures/brand-profile.json'), 'utf-8'),
);

const results: QueryResult[] = JSON.parse(
  readFileSync(resolve('test/fixtures/query-results.json'), 'utf-8'),
);

describe('MindshareAnalyzer', () => {
  const analyzer = new MindshareAnalyzer();

  it('should calculate mindshare scores', () => {
    const score = analyzer.analyze(results, profile);
    expect(score.overall).toBeGreaterThan(0);
    expect(score.byProvider).toHaveProperty('openai');
    expect(score.byProvider).toHaveProperty('anthropic');
    expect(score.rank).toBeGreaterThanOrEqual(1);
    expect(score.totalBrandsDetected).toBeGreaterThan(0);
  });

  it('should return zero for empty results', () => {
    const score = analyzer.analyze([], profile);
    expect(score.overall).toBe(0);
  });
});

describe('MentionRateAnalyzer', () => {
  const analyzer = new MentionRateAnalyzer();

  it('should calculate mention rates', () => {
    const score = analyzer.analyze(results, profile);
    expect(score.overall).toBeGreaterThan(0);
    expect(score.totalMentions).toBeGreaterThan(0);
    expect(score.totalResponses).toBe(results.length);
    expect(score.byProvider).toHaveProperty('openai');
  });

  it('should return zero for empty results', () => {
    const score = analyzer.analyze([], profile);
    expect(score.overall).toBe(0);
    expect(score.totalMentions).toBe(0);
  });
});

describe('SentimentAnalyzer', () => {
  const analyzer = new SentimentAnalyzer();

  it('should calculate sentiment scores with enhanced detail', () => {
    const score = analyzer.analyze(results, profile);
    expect(score.label).toMatch(/positive|neutral|negative/);
    expect(typeof score.overall).toBe('number');
    expect(typeof score.confidence).toBe('number');
    expect(score.confidence).toBeGreaterThanOrEqual(0);
    expect(score.confidence).toBeLessThanOrEqual(1);
    expect(score.totalSentences).toBeGreaterThanOrEqual(0);
    expect(score.positiveCount + score.neutralCount + score.negativeCount).toBe(score.totalSentences);
    expect(Array.isArray(score.topPositive)).toBe(true);
    expect(Array.isArray(score.topNegative)).toBe(true);
  });

  it('should provide per-provider labels', () => {
    const score = analyzer.analyze(results, profile);
    for (const [provider, label] of Object.entries(score.byProviderLabel)) {
      expect(['positive', 'neutral', 'negative']).toContain(label);
      expect(score.byProvider).toHaveProperty(provider);
    }
  });
});

describe('CompetitorAnalyzer', () => {
  const analyzer = new CompetitorAnalyzer();

  it('should compare brand against competitors', () => {
    const analysis = analyzer.analyze(results, profile);
    expect(analysis.competitors.length).toBeGreaterThan(0);
    expect(analysis.brandRank).toBeGreaterThanOrEqual(1);

    const notionScore = analysis.competitors.find((c) => c.name === 'Notion');
    expect(notionScore).toBeDefined();
    expect(notionScore!.mentionRate).toBeGreaterThan(0);
  });
});

describe('CitationAnalyzer', () => {
  const analyzer = new CitationAnalyzer();

  it('should detect citations from URLs', () => {
    const resultsWithUrls: QueryResult[] = [
      {
        ...results[0],
        response: 'Check out https://notion.so for more info. Also see https://monday.com/features.',
      },
    ];
    const score = analyzer.analyze(resultsWithUrls, profile);
    expect(score.totalCitations).toBe(2);
    expect(score.uniqueSourcesCited).toBe(2);
    expect(score.citationRate).toBe(100);
  });

  it('should handle results with no URLs', () => {
    const score = analyzer.analyze(results, profile);
    expect(score.totalCitations).toBeGreaterThanOrEqual(0);
  });
});

describe('PositioningAnalyzer', () => {
  const analyzer = new PositioningAnalyzer();

  it('should extract positioning attributes', () => {
    const score = analyzer.analyze(results, profile);
    expect(typeof score.primaryPosition).toBe('string');
    expect(score.byProvider).toHaveProperty('openai');
  });
});

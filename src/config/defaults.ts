import type { VoyageGeoConfig } from './schema.js';

export const DEFAULT_CONFIG: VoyageGeoConfig = {
  brand: undefined,
  website: undefined,
  competitors: [],
  providers: {
    openai: {
      name: 'openai',
      enabled: true,
      model: 'gpt-4o-mini',
      maxTokens: 512,
      temperature: 0.7,
      rateLimit: { requestsPerMinute: 500, tokensPerMinute: 200000 },
    },
    anthropic: {
      name: 'anthropic',
      enabled: true,
      model: 'claude-haiku-4-5-20251001',
      maxTokens: 512,
      temperature: 0.7,
      rateLimit: { requestsPerMinute: 500, tokensPerMinute: 200000 },
    },
    google: {
      name: 'google',
      enabled: true,
      model: 'gemini-2.0-flash',
      maxTokens: 512,
      temperature: 0.7,
      rateLimit: { requestsPerMinute: 500, tokensPerMinute: 200000 },
    },
    perplexity: {
      name: 'perplexity',
      enabled: true,
      model: 'sonar',
      maxTokens: 512,
      temperature: 0.7,
      rateLimit: { requestsPerMinute: 50, tokensPerMinute: 100000 },
    },
  },
  execution: {
    concurrency: 10,
    retries: 2,
    retryDelayMs: 500,
    timeoutMs: 15000,
    iterations: 1,
  },
  queries: {
    count: 20,
    strategies: ['keyword', 'persona', 'competitor', 'intent'],
    categories: ['recommendation', 'comparison', 'best-of', 'how-to', 'review', 'alternative', 'general'],
  },
  analysis: {
    analyzers: ['mindshare', 'mention-rate', 'sentiment', 'positioning', 'citation', 'competitor'],
  },
  report: {
    formats: ['html', 'json'],
    includeCharts: true,
    includeRawData: false,
  },
  outputDir: './data/runs',
  logLevel: 'info',
};

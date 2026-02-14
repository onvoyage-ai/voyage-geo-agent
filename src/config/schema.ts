import { z } from 'zod';

export const providerConfigSchema = z.object({
  name: z.string(),
  enabled: z.boolean().default(true),
  apiKey: z.string().optional(),
  model: z.string().optional(),
  baseURL: z.string().optional(),
  maxTokens: z.number().default(2048),
  temperature: z.number().default(0.7),
  rateLimit: z.object({
    requestsPerMinute: z.number().default(60),
    tokensPerMinute: z.number().default(100000),
  }).default({}),
});

export const executionConfigSchema = z.object({
  concurrency: z.number().default(3),
  retries: z.number().default(3),
  retryDelayMs: z.number().default(1000),
  timeoutMs: z.number().default(30000),
  iterations: z.number().default(1),
});

export const queryConfigSchema = z.object({
  count: z.number().default(20),
  strategies: z.array(z.enum(['keyword', 'persona', 'competitor', 'intent'])).default([
    'keyword',
    'persona',
    'competitor',
    'intent',
  ]),
  categories: z.array(z.enum([
    'recommendation',
    'comparison',
    'best-of',
    'how-to',
    'review',
    'alternative',
    'general',
  ])).default([
    'recommendation',
    'comparison',
    'best-of',
    'how-to',
    'review',
    'alternative',
    'general',
  ]),
});

export const analysisConfigSchema = z.object({
  analyzers: z.array(z.enum([
    'mindshare',
    'mention-rate',
    'sentiment',
    'positioning',
    'rank-position',
    'citation',
    'competitor',
  ])).default([
    'mindshare',
    'mention-rate',
    'sentiment',
    'positioning',
    'rank-position',
    'citation',
    'competitor',
  ]),
});

export const reportConfigSchema = z.object({
  formats: z.array(z.enum(['html', 'json', 'csv', 'markdown'])).default(['html', 'json']),
  includeCharts: z.boolean().default(true),
  includeRawData: z.boolean().default(false),
});

export const voyageGeoConfigSchema = z.object({
  brand: z.string().optional(),
  website: z.string().optional(),
  competitors: z.array(z.string()).default([]),
  providers: z.record(z.string(), providerConfigSchema).default({}),
  execution: executionConfigSchema.default({}),
  queries: queryConfigSchema.default({}),
  analysis: analysisConfigSchema.default({}),
  report: reportConfigSchema.default({}),
  outputDir: z.string().default('./data/runs'),
  logLevel: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

export type ProviderConfig = z.infer<typeof providerConfigSchema>;
export type ExecutionConfig = z.infer<typeof executionConfigSchema>;
export type QueryConfig = z.infer<typeof queryConfigSchema>;
export type AnalysisConfig = z.infer<typeof analysisConfigSchema>;
export type ReportConfig = z.infer<typeof reportConfigSchema>;
export type VoyageGeoConfig = z.infer<typeof voyageGeoConfigSchema>;

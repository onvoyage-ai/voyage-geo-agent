import { describe, it, expect } from 'vitest';
import { voyageGeoConfigSchema } from '../../src/config/schema.js';
import { DEFAULT_CONFIG } from '../../src/config/defaults.js';

describe('Config Schema', () => {
  it('should validate default config', () => {
    const result = voyageGeoConfigSchema.safeParse(DEFAULT_CONFIG);
    expect(result.success).toBe(true);
  });

  it('should apply defaults for empty input', () => {
    const result = voyageGeoConfigSchema.parse({});
    expect(result.outputDir).toBe('./data/runs');
    expect(result.logLevel).toBe('info');
    expect(result.execution.concurrency).toBe(3);
    expect(result.execution.retries).toBe(3);
    expect(result.queries.count).toBe(20);
  });

  it('should accept partial overrides', () => {
    const result = voyageGeoConfigSchema.parse({
      brand: 'TestBrand',
      execution: { concurrency: 5 },
    });
    expect(result.brand).toBe('TestBrand');
    expect(result.execution.concurrency).toBe(5);
    expect(result.execution.retries).toBe(3); // default
  });

  it('should reject invalid log level', () => {
    const result = voyageGeoConfigSchema.safeParse({
      logLevel: 'verbose', // invalid
    });
    expect(result.success).toBe(false);
  });

  it('should reject invalid report format', () => {
    const result = voyageGeoConfigSchema.safeParse({
      report: { formats: ['pdf'] }, // invalid
    });
    expect(result.success).toBe(false);
  });
});

describe('Default Config', () => {
  it('should have all four providers', () => {
    expect(DEFAULT_CONFIG.providers).toHaveProperty('openai');
    expect(DEFAULT_CONFIG.providers).toHaveProperty('anthropic');
    expect(DEFAULT_CONFIG.providers).toHaveProperty('google');
    expect(DEFAULT_CONFIG.providers).toHaveProperty('perplexity');
  });

  it('should have all strategies enabled', () => {
    expect(DEFAULT_CONFIG.queries.strategies).toEqual([
      'keyword', 'persona', 'competitor', 'intent',
    ]);
  });

  it('should have all analyzers enabled', () => {
    expect(DEFAULT_CONFIG.analysis.analyzers).toEqual([
      'mindshare', 'mention-rate', 'sentiment', 'positioning', 'citation', 'competitor',
    ]);
  });
});

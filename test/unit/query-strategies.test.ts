import { describe, it, expect, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { BrandProfile } from '../../src/types/brand.js';
import type { AIProvider } from '../../src/providers/types.js';
import { KeywordStrategy } from '../../src/stages/query-generation/strategies/keyword.js';
import { PersonaStrategy } from '../../src/stages/query-generation/strategies/persona.js';
import { CompetitorStrategy } from '../../src/stages/query-generation/strategies/competitor.js';
import { IntentStrategy } from '../../src/stages/query-generation/strategies/intent.js';
import { parseAIQueries } from '../../src/stages/query-generation/strategies/parse.js';

const profile: BrandProfile = JSON.parse(
  readFileSync(resolve('test/fixtures/brand-profile.json'), 'utf-8'),
);

// Mock provider that returns pipe-delimited query lines
function createMockProvider(lines: string[]): AIProvider {
  return {
    name: 'mock',
    displayName: 'Mock',
    query: vi.fn().mockResolvedValue({
      text: lines.join('\n'),
      model: 'mock-model',
      provider: 'mock',
      latencyMs: 100,
    }),
    healthCheck: vi.fn(),
    isConfigured: vi.fn().mockReturnValue(true),
  };
}

describe('parseAIQueries', () => {
  it('should parse well-formed pipe-delimited lines', () => {
    const text = [
      'What is the best CRM in 2026? | best-of | discovery',
      'Is Notion any good? | review | evaluation',
      'Top project management tools | recommendation | discovery',
    ].join('\n');

    const queries = parseAIQueries(text, 'keyword', 'kw', 10);
    expect(queries).toHaveLength(3);
    expect(queries[0].text).toBe('What is the best CRM in 2026?');
    expect(queries[0].category).toBe('best-of');
    expect(queries[0].intent).toBe('discovery');
    expect(queries[0].strategy).toBe('keyword');
    expect(queries[0].id).toMatch(/^kw-/);
  });

  it('should handle numbered lines', () => {
    const text = [
      '1. Best CRM for startups? | recommendation | startup',
      '2) Which project tool is cheapest? | recommendation | budget',
    ].join('\n');

    const queries = parseAIQueries(text, 'keyword', 'kw', 10);
    expect(queries).toHaveLength(2);
    expect(queries[0].text).toBe('Best CRM for startups?');
  });

  it('should default to general for unknown categories', () => {
    const text = 'Some query here | unknown-cat | some-intent';
    const queries = parseAIQueries(text, 'keyword', 'kw', 10);
    expect(queries[0].category).toBe('general');
  });

  it('should respect maxCount', () => {
    const text = Array.from({ length: 20 }, (_, i) =>
      `Query ${i + 1} about tools | recommendation | discovery`,
    ).join('\n');

    const queries = parseAIQueries(text, 'keyword', 'kw', 5);
    expect(queries).toHaveLength(5);
  });

  it('should skip lines that are too short', () => {
    const text = [
      'Short | best-of | x',
      'This is a reasonable query about software tools | recommendation | discovery',
    ].join('\n');

    const queries = parseAIQueries(text, 'keyword', 'kw', 10);
    expect(queries).toHaveLength(1);
  });

  it('should parse persona field as metadata', () => {
    const text = 'What CRM is best for my startup? | recommendation | startup | startup-founder';
    const queries = parseAIQueries(text, 'persona', 'ps', 10);
    expect(queries[0].metadata?.persona).toBe('startup-founder');
  });
});

describe('KeywordStrategy', () => {
  it('should call provider and return parsed queries', async () => {
    const mockLines = [
      'What is the best Productivity Software? | best-of | discovery',
      'Is Notion worth using in 2026? | review | evaluation',
      'Top note-taking tools for teams | recommendation | team',
      'Best free productivity apps | best-of | budget',
      'How do I pick a project management tool? | how-to | education',
    ];
    const provider = createMockProvider(mockLines);
    const strategy = new KeywordStrategy();

    const queries = await strategy.generate(profile, 5, provider);
    expect(queries.length).toBeGreaterThan(0);
    expect(queries.every((q) => q.strategy === 'keyword')).toBe(true);
    expect(provider.query).toHaveBeenCalledOnce();
  });
});

describe('PersonaStrategy', () => {
  it('should call provider and return persona queries', async () => {
    const mockLines = [
      'We need a project tool that scales, any recs? | recommendation | startup | startup-founder',
      'Which productivity platform has SOC 2? | best-of | compliance | enterprise-buyer',
      'Cheapest option for a 20-person team? | recommendation | budget | cost-optimizer',
    ];
    const provider = createMockProvider(mockLines);
    const strategy = new PersonaStrategy();

    const queries = await strategy.generate(profile, 5, provider);
    expect(queries.length).toBeGreaterThan(0);
    expect(queries.every((q) => q.strategy === 'persona')).toBe(true);
  });
});

describe('CompetitorStrategy', () => {
  it('should call provider and return competitor queries', async () => {
    const mockLines = [
      'Notion vs Confluence — which is better for docs? | comparison | head-to-head',
      'Should I use Notion or Coda for my team? | comparison | decision',
      'Thinking of switching from Evernote to Notion | alternative | switching',
    ];
    const provider = createMockProvider(mockLines);
    const strategy = new CompetitorStrategy();

    const queries = await strategy.generate(profile, 5, provider);
    expect(queries.length).toBeGreaterThan(0);
    expect(queries.every((q) => q.strategy === 'competitor')).toBe(true);
  });
});

describe('IntentStrategy', () => {
  it('should call provider and return intent queries', async () => {
    const mockLines = [
      'Tell me about Notion | review | navigational',
      'Best productivity software to buy right now | recommendation | commercial',
      'How has the project management market changed? | general | informational',
      'Is Notion safe for sensitive data? | review | trust',
      'Does Notion have a free plan? | general | transactional',
    ];
    const provider = createMockProvider(mockLines);
    const strategy = new IntentStrategy();

    const queries = await strategy.generate(profile, 5, provider);
    expect(queries.length).toBeGreaterThan(0);
    expect(queries.every((q) => q.strategy === 'intent')).toBe(true);
  });
});

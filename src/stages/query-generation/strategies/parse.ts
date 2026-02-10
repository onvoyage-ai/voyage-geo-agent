import { randomBytes } from 'node:crypto';
import type { GeneratedQuery, QueryCategory, QueryStrategy } from '../../../types/query.js';

const VALID_CATEGORIES = new Set<QueryCategory>([
  'recommendation', 'comparison', 'best-of', 'how-to', 'review', 'alternative', 'general',
]);

/**
 * Parse AI-generated query lines into GeneratedQuery objects.
 * Expected format per line: <query text> | <category> | <intent> [| <persona>]
 * Gracefully handles malformed lines by using defaults.
 */
export function parseAIQueries(
  text: string,
  strategy: QueryStrategy,
  prefix: string,
  maxCount: number,
): GeneratedQuery[] {
  const queries: GeneratedQuery[] = [];
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);

  for (const line of lines) {
    if (queries.length >= maxCount) break;

    // Skip lines that look like headers, numbering prefixes, or markdown
    const cleaned = line.replace(/^\d+[\.\)]\s*/, '').replace(/^[-*]\s*/, '').trim();
    if (!cleaned || cleaned.startsWith('#') || cleaned.startsWith('```')) continue;

    const parts = cleaned.split('|').map((p) => p.trim());
    if (parts.length < 2) continue;

    const queryText = parts[0];
    if (!queryText || queryText.length < 10) continue; // skip very short/empty lines

    const rawCategory = parts[1]?.toLowerCase().trim() as QueryCategory;
    const category: QueryCategory = VALID_CATEGORIES.has(rawCategory) ? rawCategory : 'general';
    const intent = parts[2]?.toLowerCase().trim() || 'general';
    const persona = parts[3]?.toLowerCase().trim();

    const metadata: Record<string, unknown> = {};
    if (persona) metadata.persona = persona;

    queries.push({
      id: `${prefix}-${randomBytes(4).toString('hex')}`,
      text: queryText,
      category,
      strategy,
      intent,
      ...(Object.keys(metadata).length > 0 ? { metadata } : {}),
    });
  }

  return queries;
}

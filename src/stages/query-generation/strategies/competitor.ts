import type { BrandProfile } from '../../../types/brand.js';
import type { GeneratedQuery } from '../../../types/query.js';
import type { AIProvider } from '../../../providers/types.js';
import type { QueryStrategyInterface } from './types.js';
import { parseAIQueries } from './parse.js';

const YEAR = new Date().getFullYear();

const buildPrompt = (profile: BrandProfile, count: number): string => {
  const competitors = profile.competitors.length > 0
    ? profile.competitors.join(', ')
    : 'major alternatives in the space';

  return `You are a GEO (Generative Engine Optimization) specialist. Generate ${count} realistic AI chatbot queries focused on COMPETITIVE COMPARISONS in the "${profile.category}" space.

BRAND CONTEXT:
- Brand: ${profile.name}
- Category: ${profile.category}
- Industry: ${profile.industry}
- Known competitors: ${competitors}
- Keywords: ${profile.keywords.join(', ') || profile.category}
- Year: ${YEAR}

QUERY TYPES TO MIX:
- Head-to-head: "${profile.name} vs [competitor] — which is better?"
- Decision queries: "Should I use X or Y?", "Trying to decide between X and Y"
- Switching: "Thinking of switching from [competitor] to ${profile.name}", "Is [competitor] still the best or should I look at alternatives?"
- Alternative-seeking: "[competitor] alternatives", "Something better than [competitor]?"
- Value comparison: "Which has better pricing, X or Y?", "X vs Y for the money"
- Use-case comparison: "X vs Y for [specific use case from keywords]"
- Justification: "Why would someone choose X over Y?", "What does X do that Y doesn't?"
- Team/scale: "X vs Y for large teams", "Which scales better?"

RULES:
- Use the ACTUAL competitor names listed above — rotate through them
- Queries should sound like real people asking AI chatbots for help deciding
- Mix ${profile.name} appearing first and second in comparisons
- Some queries should not mention ${profile.name} at all — just compare competitors or ask for alternatives
- Conversational, natural phrasing — not templated
- Include ${YEAR} naturally in a few queries
- Do NOT use placeholder brackets

FORMAT (one per line):
<query text> | <category> | <intent>

Categories: comparison, alternative, recommendation, review, general
Intent: head-to-head, decision, switching, migration, evaluation, cost, use-case, justification, trust, team

Generate exactly ${count} queries now:`;
};

export class CompetitorStrategy implements QueryStrategyInterface {
  name = 'competitor';

  async generate(profile: BrandProfile, count: number, provider: AIProvider): Promise<GeneratedQuery[]> {
    const prompt = buildPrompt(profile, count);
    const response = await provider.query(prompt);
    return parseAIQueries(response.text, 'competitor', 'cp', count);
  }
}

import type { BrandProfile } from '../../../types/brand.js';
import type { GeneratedQuery } from '../../../types/query.js';
import type { AIProvider } from '../../../providers/types.js';
import type { QueryStrategyInterface } from './types.js';
import { parseAIQueries } from './parse.js';

const YEAR = new Date().getFullYear();

const buildPrompt = (profile: BrandProfile, count: number): string => `You are a GEO (Generative Engine Optimization) specialist. Generate ${count} realistic search queries that real users would type into an AI chatbot (ChatGPT, Claude, Gemini, Perplexity) when researching the "${profile.category}" space.

BRAND CONTEXT:
- Brand: ${profile.name}
- Category: ${profile.category}
- Industry: ${profile.industry}
- Keywords: ${profile.keywords.join(', ') || profile.category}
- USPs: ${profile.uniqueSellingPoints.join(', ') || 'N/A'}
- Target audience: ${profile.targetAudience.join(', ') || 'general'}
- Year: ${YEAR}

QUERY TYPES TO MIX:
- Discovery: "What's the best X?", "Top X tools", generic category exploration
- Evaluation: reputation checks, trust signals, expert opinions
- Feature-driven: queries about specific capabilities or use cases (use the keywords above)
- Brand-specific: direct questions about ${profile.name} — reviews, worth it?, pros/cons
- Pricing/value: affordability, free tiers, cost comparisons
- Problem-framing: "I need help with [problem], what tool?", "How do companies solve [keyword]?"
- Industry-specific: queries for startups, enterprise, small business, specific verticals

RULES:
- Write them exactly as a real person would ask an AI chatbot — conversational, natural, sometimes messy
- Mix short queries ("best ${profile.category} ${YEAR}") with longer conversational ones
- Some should mention ${profile.name} by name, most should be generic category queries
- Include the current year ${YEAR} in a few queries naturally
- Do NOT use placeholder brackets like {brand} or {category}
- Each query must be on its own line
- For each query, append a pipe | followed by a category from: recommendation, comparison, best-of, how-to, review, alternative, general
- Then another pipe | followed by a short intent label (e.g. discovery, evaluation, feature, budget, trust, scaling, etc.)

FORMAT (one per line):
<query text> | <category> | <intent>

Generate exactly ${count} queries now:`;

export class KeywordStrategy implements QueryStrategyInterface {
  name = 'keyword';

  async generate(profile: BrandProfile, count: number, provider: AIProvider): Promise<GeneratedQuery[]> {
    const prompt = buildPrompt(profile, count);
    const response = await provider.query(prompt);
    return parseAIQueries(response.text, 'keyword', 'kw', count);
  }
}

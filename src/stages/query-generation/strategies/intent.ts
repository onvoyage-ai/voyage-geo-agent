import type { BrandProfile } from '../../../types/brand.js';
import type { GeneratedQuery } from '../../../types/query.js';
import type { AIProvider } from '../../../providers/types.js';
import type { QueryStrategyInterface } from './types.js';
import { parseAIQueries } from './parse.js';

const YEAR = new Date().getFullYear();

const buildPrompt = (profile: BrandProfile, count: number): string => `You are a GEO (Generative Engine Optimization) specialist. Generate ${count} realistic AI chatbot queries covering DIFFERENT SEARCH INTENTS for the "${profile.category}" space and the brand "${profile.name}".

BRAND CONTEXT:
- Brand: ${profile.name}
- Category: ${profile.category}
- Industry: ${profile.industry}
- Description: ${profile.description || 'N/A'}
- Keywords: ${profile.keywords.join(', ') || profile.category}
- USPs: ${profile.uniqueSellingPoints.join(', ') || 'N/A'}
- Year: ${YEAR}

INTENT TYPES TO COVER (distribute queries across these):
1. NAVIGATIONAL — user wants to learn about ${profile.name} specifically ("Tell me about ${profile.name}", "What does ${profile.name} do?")
2. COMMERCIAL — high purchase intent, ready to buy ("Which ${profile.category} should I go with?", "Best ${profile.category} to buy right now")
3. INFORMATIONAL — learning about the space ("How has the ${profile.category} market changed?", "What makes a good ${profile.category}?")
4. PROBLEM-SOLVING — user has a specific pain point and needs solutions ("I need [keyword] for my business, what are my options?")
5. TRUST/SAFETY — concerns about reliability, security, reputation ("Is ${profile.name} safe?", "Any issues with ${profile.name}?")
6. TRANSACTIONAL — ready to get started ("How do I sign up for ${profile.name}?", "Does ${profile.name} have a free trial?")

RULES:
- Distribute queries roughly evenly across the 6 intent types
- Sound like real people talking to AI chatbots — casual, direct, sometimes informal
- Mix brand-specific queries (mentioning ${profile.name}) with generic category queries
- Use the actual keywords and context above to make queries specific and realistic
- Include ${YEAR} in some queries where natural
- Do NOT use placeholder brackets
- Vary sentence structure — questions, commands, statements

FORMAT (one per line):
<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: navigational, commercial, informational, problem-solving, trust, security, transactional

Generate exactly ${count} queries now:`;

export class IntentStrategy implements QueryStrategyInterface {
  name = 'intent';

  async generate(profile: BrandProfile, count: number, provider: AIProvider): Promise<GeneratedQuery[]> {
    const prompt = buildPrompt(profile, count);
    const response = await provider.query(prompt);
    return parseAIQueries(response.text, 'intent', 'in', count);
  }
}

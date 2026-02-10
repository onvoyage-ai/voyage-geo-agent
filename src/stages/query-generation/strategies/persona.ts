import type { BrandProfile } from '../../../types/brand.js';
import type { GeneratedQuery } from '../../../types/query.js';
import type { AIProvider } from '../../../providers/types.js';
import type { QueryStrategyInterface } from './types.js';
import { parseAIQueries } from './parse.js';

const YEAR = new Date().getFullYear();

const buildPrompt = (profile: BrandProfile, count: number): string => `You are a GEO (Generative Engine Optimization) specialist. Generate ${count} realistic AI chatbot queries from different USER PERSONAS researching "${profile.category}" solutions.

BRAND CONTEXT:
- Brand: ${profile.name}
- Category: ${profile.category}
- Industry: ${profile.industry}
- Keywords: ${profile.keywords.join(', ') || profile.category}
- Competitors: ${profile.competitors.join(', ') || 'N/A'}
- Target audience: ${profile.targetAudience.join(', ') || 'general'}
- Year: ${YEAR}

PERSONAS TO ROTATE THROUGH:
1. Startup Founder — bootstrapped, needs something that scales, cost-conscious but growth-focused
2. Enterprise Buyer — needs compliance (SOC 2, SSO, audit logs), evaluating for 1000+ employees
3. Budget-Conscious Manager — mid-size team, tight budget, needs bang for buck
4. Technical Lead / Developer — cares about APIs, integrations, webhooks, developer experience
5. Frustrated Switcher — unhappy with current tool, looking for something better
6. First-Timer — never used this kind of tool, needs guidance, values simplicity
7. Agency / Consultant — managing multiple clients, needs multi-tenant or white-label features

RULES:
- Each query should sound like a REAL person with that persona's concerns asking an AI chatbot
- Be specific to the persona's pain points — a startup founder asks differently than an enterprise buyer
- Some should mention ${profile.name} directly, most should be generic category queries
- Conversational and natural — not robotic or formulaic
- Vary the phrasing — don't start every query the same way
- Do NOT use placeholder brackets
- Include persona tag in metadata

FORMAT (one per line):
<query text> | <category> | <intent> | <persona>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: any short descriptive label (startup, compliance, budget, technical, switching, onboarding, etc.)
Persona: startup-founder, enterprise-buyer, cost-optimizer, technical-evaluator, frustrated-user, first-timer, agency

Generate exactly ${count} queries now:`;

export class PersonaStrategy implements QueryStrategyInterface {
  name = 'persona';

  async generate(profile: BrandProfile, count: number, provider: AIProvider): Promise<GeneratedQuery[]> {
    const prompt = buildPrompt(profile, count);
    const response = await provider.query(prompt);
    return parseAIQueries(response.text, 'persona', 'ps', count);
  }
}

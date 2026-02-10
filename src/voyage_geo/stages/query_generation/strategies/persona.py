"""Persona strategy — AI-generated queries from different user personas."""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _build_prompt(profile: BrandProfile, count: int) -> str:
    return f"""You are a GEO specialist. Generate {count} realistic AI chatbot queries from different USER PERSONAS researching "{profile.category}" solutions.

CATEGORY CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords) or profile.category}
- Target audience: {", ".join(profile.target_audience) or "general"}
- Year: {YEAR}

PERSONAS TO ROTATE THROUGH:
1. Startup Founder — bootstrapped, needs something that scales, cost-conscious but growth-focused
2. Enterprise Buyer — needs compliance (SOC 2, SSO, audit logs), evaluating for 1000+ employees
3. Budget-Conscious Manager — mid-size team, tight budget, needs bang for buck
4. Technical Lead / Developer — cares about APIs, integrations, webhooks, developer experience
5. Frustrated Switcher — unhappy with current tool, looking for something better
6. First-Timer — never used this kind of tool, needs guidance, values simplicity
7. Agency / Consultant — managing multiple clients, needs multi-tenant or white-label features

RULES:
- CRITICAL: NEVER mention any specific brand or company name. These queries should sound like someone who hasn't chosen a product yet.
- Each query should sound like a REAL person with that persona's concerns
- Be specific to the persona's pain points
- Conversational and natural — not robotic
- Vary the phrasing

FORMAT (one per line):
<query text> | <category> | <intent> | <persona>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Persona: startup-founder, enterprise-buyer, cost-optimizer, technical-evaluator, frustrated-user, first-timer, agency

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "persona", "ps", count)

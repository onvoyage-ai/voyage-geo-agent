"""Intent strategy — AI-generated queries covering navigational, commercial, informational, etc."""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _build_prompt(profile: BrandProfile, count: int) -> str:
    return f"""You are a GEO specialist. Generate {count} realistic AI chatbot queries covering DIFFERENT SEARCH INTENTS for the "{profile.category}" space.

CATEGORY CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Description: {profile.description or "N/A"}
- Keywords: {", ".join(profile.keywords) or profile.category}
- Key capabilities: {", ".join(profile.unique_selling_points) or "N/A"}
- Year: {YEAR}

INTENT TYPES TO COVER (distribute evenly):
1. COMMERCIAL — high purchase intent, ready to buy
2. INFORMATIONAL — learning about the space
3. PROBLEM-SOLVING — user has a specific pain point
4. TRUST/SAFETY — concerns about reliability, security
5. TRANSACTIONAL — ready to get started, sign up
6. COMPARATIVE — evaluating multiple options, wants to understand trade-offs

RULES:
- CRITICAL: NEVER include any specific brand or company name in the query text. All queries must be generic.
- Distribute queries roughly evenly across the 6 intent types
- Sound like real people talking to AI chatbots
- Use the actual keywords and context above
- Include {YEAR} in some queries where natural
- Vary sentence structure

FORMAT (one per line):
<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: commercial, informational, problem-solving, trust, security, transactional, comparative

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "intent", "in", count)

"""Competitor strategy — AI-generated head-to-head and switching queries."""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _build_prompt(profile: BrandProfile, count: int) -> str:
    competitors = ", ".join(profile.competitors) if profile.competitors else "major alternatives in the space"
    return f"""You are a GEO specialist. Generate {count} realistic AI chatbot queries about the COMPETITIVE LANDSCAPE in the "{profile.category}" space.

CATEGORY CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Known players in the space: {competitors}
- Keywords: {", ".join(profile.keywords) or profile.category}
- Year: {YEAR}

QUERY TYPES TO MIX:
- Alternative-seeking: "[known player] alternatives", "what else is like [known player]?"
- Head-to-head between competitors: "[player A] vs [player B]"
- Landscape overview: "top {profile.category} tools {YEAR}", "who are the main players in {profile.category}?"
- Switching: "thinking of switching from [known player], what are my options?"
- Value comparison: "which {profile.category} tool has the best pricing?"
- Use-case comparison: "[known player] vs others for [specific use case]"

RULES:
- CRITICAL: NEVER mention {profile.name} in any query. We want to see if AI models recommend it organically.
- You CAN and SHOULD use the competitor names listed above — rotate through them
- Sound like real people asking AI chatbots for help deciding
- Conversational, natural phrasing
- Include {YEAR} in a few queries

FORMAT (one per line):
<query text> | <category> | <intent>

Categories: comparison, alternative, recommendation, review, general
Intent: head-to-head, decision, switching, migration, evaluation, cost, use-case, landscape, trust

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "competitor", "cp", count)

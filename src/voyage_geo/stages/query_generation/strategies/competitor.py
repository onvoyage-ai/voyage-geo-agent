"""Competitor strategy — queries about alternatives and head-to-head comparisons."""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _build_prompt(profile: BrandProfile, count: int) -> str:
    competitors = ", ".join(profile.competitors) if profile.competitors else "major alternatives in the space"
    return f"""Generate {count} search queries about the competitive landscape in "{profile.category}".

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Known competitors: {competitors}
- Year: {YEAR}

These queries CAN and SHOULD mention competitor names from the list above. The goal is to see if AI models recommend {profile.name} when someone asks about competitors.

EXAMPLES of realistic competitor queries (for "spend management platform", competitors: Ramp, Divvy, Airbase):
- ramp alternatives {YEAR} | alternative | switching
- divvy vs other corporate card options | comparison | head-to-head
- what are the best alternatives to airbase | alternative | discovery
- companies like ramp but cheaper | alternative | pricing
- is there something better than divvy for startups | alternative | evaluation
- top corporate card platforms besides ramp | best-of | landscape

YOUR QUERIES MUST BE:
- SHORT: 5-15 words max
- NATURAL: how real people ask chatbots for competitor info
- Use competitor names from the list — rotate through them

RULES:
- NEVER mention {profile.name} — that's the brand we're measuring
- Keep queries short and direct
- Each query on its own line:

<query text> | <category> | <intent>

Categories: comparison, alternative, recommendation, review, best-of, general
Intent: head-to-head, switching, discovery, pricing, evaluation, landscape

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "competitor", "cp", count)

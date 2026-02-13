"""Keyword strategy — short, natural discovery and evaluation queries."""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _build_prompt(profile: BrandProfile, count: int) -> str:
    return f"""Generate {count} search queries that real people would type into ChatGPT, Perplexity, or Google when looking for a {profile.category}.

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords[:6]) or profile.category}
- Year: {YEAR}

GOOD EXAMPLES (for a "project management tool"):
- best project management tool for small teams
- what do companies use to track projects
- is there a free alternative to expensive PM software
- recommend a simple task app for remote teams
- what should i look for in project management software

BAD EXAMPLES — do NOT generate queries like these:
- "project management tool reviews and user experiences" ← keyword stuffing, not a real question
- "best affordable project management software solutions for teams" ← too many adjectives crammed together
- "comprehensive project management platform with collaboration features" ← sounds like ad copy

YOUR QUERIES MUST BE:
- SHORT: 5-12 words. Real people don't write long queries.
- CONVERSATIONAL: written as a question or casual request, not a keyword string. If it doesn't sound like something you'd say out loud, it's wrong.
- PURCHASE-ORIENTED: the person is looking to discover, evaluate, or buy something
- VARIED: mix "best X", "X for [use case]", "how to choose X", "recommend me X", pricing questions

RULES:
- NEVER include any brand or company name
- NO keyword stuffing — don't cram multiple descriptors together ("personalized adaptive learning platform reviews")
- NO backstories, no multi-sentence queries
- NO quotation marks around the query text
- Queries should be QUESTIONS or REQUESTS, not noun phrases
- Each query on its own line in this format:

<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: discovery, evaluation, pricing, use-case, problem-solving

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "keyword", "kw", count)

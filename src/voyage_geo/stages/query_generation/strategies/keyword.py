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

EXAMPLES of realistic queries (for a "project management tool"):
- best project management tool for small teams
- project management software with good free tier
- what do companies use to track projects in 2026
- affordable alternative to expensive PM tools
- simple task management app for remote teams

YOUR QUERIES MUST BE:
- SHORT: 5-15 words max. Real people don't write paragraphs.
- NATURAL: exactly how someone would type into a chatbot — lowercase, casual
- PURCHASE-ORIENTED: the person is looking to discover, evaluate, or buy something in this category
- VARIED: mix "best X", "X for [use case]", "how to choose X", "X recommendations", pricing questions

RULES:
- NEVER include any brand or company name
- NO backstories, no "my wife and I", no multi-sentence queries
- NO quotation marks around the query text
- Each query on its own line in this format:

<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: discovery, evaluation, pricing, use-case, problem-solving

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "keyword", "kw", count)

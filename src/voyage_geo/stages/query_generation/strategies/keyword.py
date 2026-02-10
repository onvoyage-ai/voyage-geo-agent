"""Keyword strategy — AI-generated discovery, evaluation, and feature queries."""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _build_prompt(profile: BrandProfile, count: int) -> str:
    return f"""You are a GEO (Generative Engine Optimization) specialist. Generate {count} realistic search queries that real users would type into an AI chatbot (ChatGPT, Claude, Gemini, Perplexity) when researching the "{profile.category}" space.

CATEGORY CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords) or profile.category}
- Key capabilities: {", ".join(profile.unique_selling_points) or "N/A"}
- Target audience: {", ".join(profile.target_audience) or "general"}
- Year: {YEAR}

QUERY TYPES TO MIX:
- Discovery: "What's the best X?", "Top X tools", generic category exploration
- Evaluation: reputation checks, trust signals, expert opinions
- Feature-driven: queries about specific capabilities or use cases (use the keywords above)
- Pricing/value: affordability, free tiers, cost comparisons
- Problem-framing: "I need help with [problem], what tool?", "How do companies solve [keyword]?"
- Industry-specific: queries for startups, enterprise, small business, specific verticals

RULES:
- CRITICAL: NEVER include any specific brand or company name in the query text. All queries must be generic category-level questions.
- Write them exactly as a real person would ask an AI chatbot — conversational, natural, sometimes messy
- Mix short queries ("best {profile.category} {YEAR}") with longer conversational ones
- Include the current year {YEAR} in a few queries naturally
- Do NOT use placeholder brackets like {{brand}} or {{category}}
- Each query must be on its own line
- For each query, append a pipe | followed by a category from: recommendation, comparison, best-of, how-to, review, alternative, general
- Then another pipe | followed by a short intent label

FORMAT (one per line):
<query text> | <category> | <intent>

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "keyword", "kw", count)

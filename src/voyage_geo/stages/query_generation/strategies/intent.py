"""Intent strategy — queries covering commercial, informational, and transactional intents."""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _build_prompt(profile: BrandProfile, count: int) -> str:
    return f"""Generate {count} search queries for "{profile.category}" covering different search intents.

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords[:6]) or profile.category}
- USPs in the space: {", ".join(profile.unique_selling_points[:4]) or "N/A"}
- Year: {YEAR}

INTENT TYPES to distribute across:
1. COMMERCIAL — ready to buy or sign up ("best X to buy", "top rated X", "X worth the money")
2. INFORMATIONAL — learning about the category ("what is X", "how does X work", "X explained")
3. PROBLEM-SOLVING — has a specific pain point ("how to fix [problem]", "tool for [pain point]")
4. TRUST — concerns about quality/safety ("is X safe", "X reviews", "most reliable X")
5. TRANSACTIONAL — ready to act ("X near me", "book X", "X pricing", "X free trial")
6. COMPARATIVE — weighing options ("X vs Y", "which X is best for", "pros and cons of X")

EXAMPLES of realistic intent-driven queries (for "cloud storage"):
- is cloud storage safe for sensitive documents | general | trust
- best cloud storage for photographers {YEAR} | best-of | commercial
- how to choose between cloud storage providers | how-to | comparative
- cheap cloud storage with good security | recommendation | commercial
- what happens if a cloud storage company shuts down | general | trust
- cloud storage pricing comparison | comparison | transactional

YOUR QUERIES MUST BE:
- SHORT: 5-15 words max
- NATURAL: typed by a real person into ChatGPT or Perplexity
- Each intent should lead the AI to potentially recommend specific products/brands

RULES:
- NEVER include any brand or company name
- NO long stories or multi-sentence queries
- Each query on its own line:

<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: commercial, informational, problem-solving, trust, transactional, comparative

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "intent", "in", count)

"""Persona strategy — queries from different buyer angles, still short and natural."""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _build_prompt(profile: BrandProfile, count: int) -> str:
    return f"""Generate {count} search queries for "{profile.category}" from different buyer perspectives.

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords[:6]) or profile.category}
- Target buyers: {", ".join(profile.target_audience[:4]) or "general"}
- Year: {YEAR}

BUYER ANGLES to rotate through:
1. Budget buyer — wants the cheapest or best-value option
2. Premium buyer — wants the best quality, willing to pay more
3. First-timer — doesn't know the category well, needs guidance
4. Switcher — unhappy with current choice, looking for something better
5. Specific use case — has a particular need (team size, occasion, feature)

GOOD EXAMPLES (for "CRM software"):
- best crm for a 5 person sales team | recommendation | use-case | budget-buyer
- what crm do big companies actually use | recommendation | evaluation | premium-buyer
- i've never used a crm, where do i start | how-to | discovery | first-timer
- looking for something better than my current crm | alternative | switching | switcher
- which crm has the best mobile app | recommendation | use-case | specific-use-case

BAD EXAMPLES — do NOT generate these:
- "affordable CRM software solutions for growing businesses" ← keyword stuffing, not a question
- "as a startup founder looking for a CRM that integrates with..." ← backstory, too long

YOUR QUERIES MUST BE:
- SHORT: 5-12 words. The persona influences the ANGLE, not the length.
- CONVERSATIONAL: sounds like something you'd say to ChatGPT — questions and requests, not keyword strings
- PURCHASE-ORIENTED: they want to find, evaluate, or choose something

RULES:
- NEVER include any brand or company name
- NO keyword stuffing, NO multi-sentence queries, NO backstories
- Each query on its own line:

<query text> | <category> | <intent> | <persona>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: discovery, evaluation, pricing, switching, use-case
Persona: budget-buyer, premium-buyer, first-timer, switcher, specific-use-case

Generate exactly {count} queries:"""


async def generate(profile: BrandProfile, count: int, provider: BaseProvider) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "persona", "ps", count)

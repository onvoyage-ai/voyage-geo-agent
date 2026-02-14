"""Leaderboard query generation — every query is designed to elicit brand recommendations.

Unlike single-brand GEO queries (which are generic and test organic mention), leaderboard
queries exist to FORCE AI models to name, rank, and compare brands. Every query should
produce a response that mentions specific companies/products by name.

Strategies:
- direct-rec: "best X", "top X", "recommend X" — straightforward recommendation asks
- vertical: vary by sub-niche/vertical within the category
- comparison: ask AI to explicitly rank, compare, or pick winners
- scenario: realistic buyer situations where someone needs specific recommendations
"""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _direct_rec_prompt(profile: BrandProfile, count: int) -> str:
    return f"""Generate {count} search queries that DIRECTLY ask for recommendations in the "{profile.category}" space.

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords[:6]) or profile.category}
- Year: {YEAR}

THE GOAL: Every query must be one that will make an AI model respond with a LIST OF SPECIFIC BRAND NAMES. If the query could be answered without naming any companies, it's useless — don't generate it.

GOOD EXAMPLES (for "venture capital firms"):
- who are the best VC firms right now
- top venture capital firms to pitch to in {YEAR}
- recommend the best VCs for startups
- which are the most respected VC firms
- list the top 10 venture capital investors

BAD EXAMPLES — NEVER generate queries like these:
- "how does venture capital work" ← educational, won't name specific firms
- "what should I look for in an investor" ← advice, not recommendations
- "is venture capital worth it" ← philosophical, no brand names

YOUR QUERIES MUST:
- Be 5-12 words, conversational
- ALWAYS ask for specific companies/brands/products by requesting "best", "top", "recommend", "which", "who", "list"
- Produce a response where the AI HAS to name multiple brands

RULES:
- NEVER include any specific brand or company name in the query
- Each query on its own line:

<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: discovery, evaluation, ranking

Generate exactly {count} queries:"""


def _vertical_prompt(profile: BrandProfile, count: int) -> str:
    return f"""Generate {count} search queries asking for the best "{profile.category}" for DIFFERENT SPECIFIC VERTICALS/NICHES.

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords[:6]) or profile.category}
- Year: {YEAR}

THE GOAL: Each query targets a different sub-niche, vertical, segment, or use case within "{profile.category}". The AI must respond with specific brand names that serve that niche.

GOOD EXAMPLES (for "venture capital firms"):
- best VC firms for biotech startups
- top investors for fintech companies
- which VCs focus on enterprise SaaS
- best venture capital for consumer apps
- top VCs for hardware startups
- which investors specialize in AI companies
- best VCs for climate tech

BAD EXAMPLES:
- "how to find investors in biotech" ← asks how, not who
- "biotech startup funding landscape" ← noun phrase, won't get brand names

VARY across different verticals, industries, stages, geographies, company sizes, and sectors. Each query should target a DIFFERENT niche.

YOUR QUERIES MUST:
- Be 5-14 words, conversational
- Ask "best X for Y", "top X in Y", "which X focus on Y"
- ALWAYS produce a response with specific brand/company names

RULES:
- NEVER include any specific brand or company name
- Each query on its own line:

<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: vertical-discovery, niche-evaluation, segment-ranking

Generate exactly {count} queries:"""


def _comparison_prompt(profile: BrandProfile, count: int) -> str:
    return f"""Generate {count} search queries that ask AI to RANK, COMPARE, or PICK WINNERS in the "{profile.category}" space.

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords[:6]) or profile.category}
- Year: {YEAR}

THE GOAL: Force the AI to create rankings, tier lists, comparisons, and "best of" lists. The response MUST contain multiple brand names in a ranked or compared format.

GOOD EXAMPLES (for "venture capital firms"):
- rank the top 10 VC firms by reputation
- which VC firms have the best track record
- who are the most successful venture capitalists
- tier list of venture capital firms
- which VCs have the best portfolio companies
- most active VC firms this year
- which investors close deals the fastest

BAD EXAMPLES:
- "how to evaluate a VC firm" ← educational, won't produce rankings
- "pros and cons of venture capital" ← about the concept, not specific firms

YOUR QUERIES MUST:
- Be 5-14 words
- Use ranking language: "rank", "top", "tier list", "most", "best track record", "compare", "versus"
- ALWAYS produce a response with ranked/compared brand names

RULES:
- NEVER include any specific brand or company name
- Each query on its own line:

<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: ranking, comparison, evaluation

Generate exactly {count} queries:"""


def _scenario_prompt(profile: BrandProfile, count: int) -> str:
    return f"""Generate {count} search queries from SPECIFIC BUYER SCENARIOS where the person needs recommendations for "{profile.category}".

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords[:6]) or profile.category}
- Year: {YEAR}

THE GOAL: Each query comes from a specific situation where someone NEEDS to pick a specific brand/company. The scenario gives enough context that the AI will recommend specific names.

GOOD EXAMPLES (for "venture capital firms"):
- I'm raising a $5M Series A, which VCs should I pitch
- we're a 3-person team pre-revenue, who invests at this stage
- my startup is in healthcare AI, which investors should I target
- I need a lead investor for a $20M round, who's best
- first-time founder in Europe, which VCs should I approach
- I want a VC who actually helps with recruiting, who does that

BAD EXAMPLES:
- "how do I prepare a pitch deck" ← doesn't ask for specific firms
- "what's a good valuation for Series A" ← about deal terms, not firms
- "I'm a founder exploring funding options" ← too vague, no recommendation request

YOUR QUERIES MUST:
- Be 8-18 words, conversational first-person
- Describe a SPECIFIC SITUATION + ask for specific recommendations
- ALWAYS produce a response with specific brand/company names
- The situation should make it clear the person wants NAMES, not advice

RULES:
- NEVER include any specific brand or company name
- Each query on its own line:

<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: scenario-discovery, scenario-evaluation, scenario-selection

Generate exactly {count} queries:"""


LEADERBOARD_STRATEGIES = {
    "direct-rec": _direct_rec_prompt,
    "vertical": _vertical_prompt,
    "comparison": _comparison_prompt,
    "scenario": _scenario_prompt,
}


async def generate_leaderboard_queries(
    profile: BrandProfile,
    total_count: int,
    provider: BaseProvider,
) -> list[GeneratedQuery]:
    """Generate queries optimized for leaderboard — every query forces brand recommendations."""
    strategies = list(LEADERBOARD_STRATEGIES.items())
    per_strategy = -(-total_count // len(strategies))  # ceil div

    all_queries: list[GeneratedQuery] = []

    prefix_map = {
        "direct-rec": "dr",
        "vertical": "vt",
        "comparison": "cp",
        "scenario": "sc",
    }

    for strategy_name, prompt_fn in strategies:
        prompt = prompt_fn(profile, per_strategy)
        response = await provider.query(prompt)
        prefix = prefix_map.get(strategy_name, strategy_name[:2])
        queries = parse_ai_queries(response.text, strategy_name, prefix, per_strategy)  # type: ignore[arg-type]
        all_queries.extend(queries)

    return all_queries[:total_count]

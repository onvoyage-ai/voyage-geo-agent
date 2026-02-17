"""Leaderboard query generation — mirrors how real people actually ask AI for recommendations.

The goal is to measure organic AI mindshare: which brands do AI models naturally surface
when a real person asks a genuine question? Every query should read like something an
actual user would type into ChatGPT, Claude, or Perplexity — not like an engineered prompt.

Strategies:
- discovery: broad, natural questions someone asks when starting their search in a category
- vertical: questions from someone with a specific need, use case, or domain in mind
"""

from __future__ import annotations

from datetime import UTC, datetime

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery

YEAR = datetime.now(UTC).year


def _discovery_prompt(profile: BrandProfile, count: int) -> str:
    return f"""You are given a category: "{profile.category}"

Your task is to infer {count} search queries that a real person would type into an AI assistant (like ChatGPT, Claude, or Perplexity) when they are genuinely trying to discover or choose something in this space.

Context:
- Category: {profile.category}
- Industry: {profile.industry}
- Related terms: {", ".join(profile.keywords[:6]) or profile.category}
- Year: {YEAR}

Requirements:
- Each query should represent a real user intent — the kind of thing someone actually types when they need help deciding
- Phrase queries the way real people talk to AI: natural, concise, conversational
- Vary the angle — some people are just starting to explore, others are closer to a decision
- Do not use artificial phrasing like "list the top 10" or "rank the best" — real people rarely talk that way
- Do not include any specific brand or company name in the query text

CRITICAL — every query MUST pass this test:
The AI's response will inevitably contain specific names. If a query could be fully answered with general advice, criteria, or opinions WITHOUT naming specific brands/companies/institutions, it is USELESS for our purpose. Do not generate it.

BAD queries that fail this test:
- "how do i figure out which university is best for me" ← advice about methodology, no names needed
- "are prestigious universities still worth it" ← philosophical debate, no names needed
- "what should i look for when comparing options" ← evaluation criteria, no names needed
- "do rankings actually mean anything" ← meta-discussion about rankings, no names needed

Also BAD — geographic filters that exclude major players:
- "which ones outside the US are good" ← suppresses the biggest names from responses
- "best options in Europe only" ← artificially limits which brands can appear

GOOD EXAMPLES (for "venture capital firms"):
- which vcs are worth pitching to right now
- who are the good investors for early stage startups
- what venture capital firms actually add value beyond money
- best vcs that are actively investing in {YEAR}
- who should i talk to if im raising a seed round

Output format — each query on its own line:
<query text> | <category> | <intent>

Categories: recommendation, best-of, general
Intent: discovery, evaluation, exploration

Generate exactly {count} queries:"""


def _vertical_prompt(profile: BrandProfile, count: int) -> str:
    return f"""You are given a category: "{profile.category}"

Your task is to infer {count} search queries from people who have a specific need, use case, or domain in mind within this category. Each person knows what they want — they just need to find the right fit.

Context:
- Category: {profile.category}
- Industry: {profile.industry}
- Related terms: {", ".join(profile.keywords[:6]) or profile.category}
- Year: {YEAR}

Requirements:
- Each query should come from a different angle — different fields, needs, goals, or constraints
- Phrase queries naturally, the way someone with domain knowledge actually asks
- The person has a specific context (their field, their problem, their situation) but hasn't decided on a brand yet
- Do not repeat the same sentence structure — vary how the questions are framed
- Do not include any specific brand or company name in the query text

CRITICAL — every query MUST pass this test:
The AI's response will inevitably contain specific names. If a query could be fully answered with general advice, criteria, or opinions WITHOUT naming specific brands/companies/institutions, it is USELESS for our purpose. Do not generate it.

BAD queries that fail this test:
- "what should i consider when picking a program" ← criteria-seeking, no names needed
- "how do i break into this field" ← career advice, no names needed
- "is it worth specializing in X" ← opinion question, no names needed

Also BAD — geographic filters that exclude major players:
- "best options in europe for X" ← artificially limits responses to one region
- "outside of the US who is good at X" ← suppresses dominant players from appearing
Instead, let the AI surface names from any geography organically.

GOOD EXAMPLES (for "venture capital firms"):
- who invests in climate tech startups these days
- good vcs for a b2b saas company doing $2m arr
- which investors actually understand deep tech
- im in healthcare ai who should i be talking to
- best investors for consumer social apps

Output format — each query on its own line:
<query text> | <category> | <intent>

Categories: recommendation, best-of, general
Intent: vertical-discovery, niche-evaluation, domain-search

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
    "discovery": _discovery_prompt,
    "vertical": _vertical_prompt,
}


async def generate_leaderboard_queries(
    profile: BrandProfile,
    total_count: int,
    provider: BaseProvider,
) -> list[GeneratedQuery]:
    """Generate natural user queries that mirror how real people ask AI for recommendations."""
    strategies = list(LEADERBOARD_STRATEGIES.items())
    per_strategy = -(-total_count // len(strategies))  # ceil div

    all_queries: list[GeneratedQuery] = []

    prefix_map = {
        "discovery": "ds",
        "vertical": "vt",
    }

    for strategy_name, prompt_fn in strategies:
        prompt = prompt_fn(profile, per_strategy)
        response = await provider.query(prompt)
        prefix = prefix_map.get(strategy_name, strategy_name[:2])
        queries = parse_ai_queries(response.text, strategy_name, prefix, per_strategy)  # type: ignore[arg-type]
        all_queries.extend(queries)

    return all_queries[:total_count]

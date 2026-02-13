# Adding a New Query Strategy

Query strategies generate different types of search queries to test brand visibility. All strategies generate **brand-blind queries** — the target brand name must never appear in query text.

## 1. Create the Strategy

Create `src/voyage_geo/stages/query_generation/strategies/<name>.py`:

```python
"""My strategy — description of what angle this covers."""

from __future__ import annotations

from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery


def _build_prompt(profile: BrandProfile, count: int) -> str:
    return f"""Generate {count} search queries for "{profile.category}".

CONTEXT:
- Category: {profile.category}
- Industry: {profile.industry}
- Keywords: {", ".join(profile.keywords[:6]) or profile.category}

YOUR QUERIES MUST BE:
- SHORT: 5-12 words
- CONVERSATIONAL: sounds like something you'd say to ChatGPT
- NEVER include any brand or company name

Each query on its own line:
<query text> | <category> | <intent>

Categories: recommendation, comparison, best-of, how-to, review, alternative, general
Intent: discovery, evaluation, pricing, use-case, problem-solving

Generate exactly {count} queries:"""


async def generate(
    profile: BrandProfile, count: int, provider: BaseProvider
) -> list[GeneratedQuery]:
    prompt = _build_prompt(profile, count)
    response = await provider.query(prompt)
    return parse_ai_queries(response.text, "my-strategy", "ms", count)
```

## 2. Register the Strategy

In `src/voyage_geo/stages/query_generation/stage.py`, add to `STRATEGY_MAP`:

```python
from voyage_geo.stages.query_generation.strategies import my_strategy

STRATEGY_MAP = {
    # ... existing strategies
    "my-strategy": my_strategy,
}
```

## 3. Update Config

Add your strategy name to the default strategies list in `src/voyage_geo/config/schema.py`.

## Built-in Strategies

| Strategy | Description | Default |
|----------|-------------|---------|
| `keyword` | Generic discovery and evaluation queries using category keywords | Yes |
| `persona` | Queries from different buyer angles (budget, premium, first-timer, switcher) | Yes |
| `intent` | Covers commercial, informational, trust, transactional, and comparative intents | Yes |
| `competitor` | Queries mentioning competitor names (auto-enabled for SaaS/software only) | No |

## Design Principles

- **Brand-blind**: Queries never mention the target brand — the goal is to measure organic recommendations
- **Short and natural**: 5-12 words, conversational tone — what real people actually type into ChatGPT
- **No keyword stuffing**: Avoid stacking adjectives and nouns ("affordable enterprise CRM solutions")
- **Purchase-oriented**: Queries should lead to product recommendations, not abstract discussions

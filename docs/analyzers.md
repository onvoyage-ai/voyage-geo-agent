# Adding a New Analyzer

Analyzers process query results to extract specific metrics about brand visibility.

## 1. Create the Analyzer

Create `src/voyage_geo/stages/analysis/analyzers/<name>.py`:

```python
"""My Analyzer — measures something about brand visibility."""

from __future__ import annotations

from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult


class MyAnalyzer:
    name = "my-analyzer"

    def analyze(
        self,
        results: list[QueryResult],
        profile: BrandProfile,
        **kwargs,
    ) -> dict:
        valid = [r for r in results if not r.error and r.response]

        # Your analysis logic here
        return {
            "overall": 0,
            "by_provider": {},
        }
```

## 2. Register the Analyzer

In `src/voyage_geo/stages/analysis/stage.py`, add to `ANALYZER_MAP`:

```python
from voyage_geo.stages.analysis.analyzers.my_analyzer import MyAnalyzer

ANALYZER_MAP: dict[str, type] = {
    # ... existing analyzers
    "my-analyzer": MyAnalyzer,
}
```

## 3. Add to Config Schema

In `src/voyage_geo/config/schema.py`, add to the analyzers list in the default config.

## 4. Add Result Type

If your analyzer produces a new data shape, add it to `src/voyage_geo/types/analysis.py` and update `AnalysisResult`.

## Built-in Analyzers

| Analyzer | What it measures |
|----------|-----------------|
| `mindshare` | Brand's share of AI "attention" vs competitors |
| `mention-rate` | How often the brand is mentioned in responses |
| `sentiment` | Positive/negative/neutral sentiment of brand mentions |
| `positioning` | How AI models describe and position the brand |
| `competitor` | Comparison of brand metrics against competitors |
| `narrative` | What themes AI models associate with the brand, USP coverage gaps |

## Useful Utilities

From `src/voyage_geo/utils/text.py`:
- `contains_brand(text, brand)` — check if text mentions brand
- `extract_sentences(text)` — split text into sentences
- `count_occurrences(text, term)` — count term occurrences
- `extract_competitors_with_llm(text, provider)` — LLM-based competitor extraction
- `extract_narratives_with_llm(text, provider)` — LLM-based claim extraction

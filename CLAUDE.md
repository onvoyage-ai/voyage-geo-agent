# Voyage GEO — Development Guide

## What This Is

Voyage GEO is an open source GEO (Generative Engine Optimization) tool, designed to be used through Claude Code. It analyzes how AI models (ChatGPT, Claude, Gemini, Perplexity) reference and recommend brands. Think of it as SEO analytics, but for AI search engines.

## How to Use (AI Agent Skills)

Skills work with Claude Code, OpenClaw, and any agent supporting `SKILL.md`. Install with:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Onvoyage-AI/voyage-geo-agent/main/install-skills.sh)
```

Two slash commands:

- `/geo-run` — Full GEO analysis. Handles setup, brand research, query generation, execution, analysis, and reporting.
- `/geo-leaderboard` — Category-wide brand comparison. Ranks all brands in a category by AI visibility.

Start with `/geo-run`.

## Architecture

**Python pipeline-based tool** with 5 stages:

```
[Brand Input] → Research → Generate Queries → Run Against AI Models → Analyze Results → Generate Reports
```

### Key Patterns

- **Provider plugin system** — `BaseProvider` ABC in `src/voyage_geo/providers/base.py`
- **Pipeline + RunContext** — stages run sequentially, each saving output to disk
- **Registry pattern** — providers, analyzers, query strategies are all pluggable
- **Pydantic v2 models** — `src/voyage_geo/config/schema.py` is the single source of truth for config types
- **File-based storage** — each run is a self-contained directory under `data/runs/`
- **VADER sentiment** — production-grade sentiment analysis via vaderSentiment
- **Async throughout** — all providers use async SDKs (AsyncOpenAI, AsyncAnthropic, google-genai async)

### Directory Layout

```
src/voyage_geo/
  __init__.py           # Package root + version
  cli.py                # CLI entry (Typer + Rich)
  config/               # Pydantic schemas, defaults, config loader
  core/                 # Engine, pipeline, context, errors
  providers/            # AI model providers (openai, anthropic, google, perplexity)
  stages/               # 5 pipeline stages
    research/           # Stage 1: Brand research + web scraping
    query_generation/   # Stage 2: Generate search queries (4 AI-powered strategies)
    execution/          # Stage 3: Run queries against providers
    analysis/           # Stage 4: Analyze results (6 analyzers)
    reporting/          # Stage 5: Generate reports (HTML/JSON/CSV/Markdown + plotly charts)
  storage/              # File-based persistence
  types/                # Shared Pydantic type definitions
  utils/                # Text helpers, Rich progress displays
```

## CLI Reference

```bash
python3 -m voyage_geo run -b "<brand>" -w "<url>" -p openai,anthropic,google -f html,json,csv,markdown
python3 -m voyage_geo providers            # list configured providers
python3 -m voyage_geo providers --test     # health check providers
python3 -m voyage_geo research "<brand>" -w "<url>"
python3 -m voyage_geo report -r <run-id> -f html,json,csv,markdown
python3 -m voyage_geo leaderboard "<category>" -p chatgpt,claude -q 20 -f html,json,csv,markdown
python3 -m voyage_geo leaderboard "<category>" --brands "A,B,C" --max-brands 10
python3 -m voyage_geo runs                 # list past runs
python3 -m voyage_geo version
```

**Important:** Use `voyage-geo` or `python3 -m voyage_geo` to run the CLI. The flag for report formats is `--formats` (not `--format`). The `providers` subcommand has no `--list` flag — just run it bare.

## Install

```bash
pip install voyage-geo          # From PyPI
pip install -e ".[dev]"         # From source with dev dependencies
```

## Build & Test

```bash
pip install -e ".[dev]"     # Install with dev dependencies
python3 -m pytest tests/ -v # Run tests
python3 -m mypy src/voyage_geo/ --ignore-missing-imports  # Type checking
python3 -m ruff check src/ tests/  # Linting
```

## Extension Points

| What | Interface | Where |
|------|-----------|-------|
| AI Provider | `BaseProvider` ABC | `src/voyage_geo/providers/<name>_provider.py` |
| Query Strategy | Function in strategies/ | `src/voyage_geo/stages/query_generation/strategies/` |
| Analyzer | `Analyzer` Protocol | `src/voyage_geo/stages/analysis/analyzers/` |
| Report Format | Method in ReportingStage | `src/voyage_geo/stages/reporting/stage.py` |

## Design Decisions

### Brand-blind queries (query generation)

All four query strategies (keyword, persona, competitor, intent) generate **brand-blind** queries — the target brand name must NEVER appear in query text. The purpose of GEO is to measure whether AI models *organically* recommend a brand when asked generic category questions. Asking "Is Brex good?" and getting "yes" tells us nothing.

- **keyword** — generic discovery, evaluation, feature-driven, pricing, problem-framing queries using category/industry/keywords context only
- **persona** — queries from different user personas (startup founder, enterprise buyer, etc.) who haven't chosen a product yet; no brand or competitor names in context
- **competitor** — queries about the competitive landscape that CAN mention competitor names (from `profile.competitors`) but NEVER the target brand; measures if AI recommends the target brand when someone asks about alternatives
- **intent** — covers commercial, informational, problem-solving, trust, transactional, and comparative intents; the old NAVIGATIONAL intent was removed because it was inherently brand-specific

Every strategy prompt includes the rule: `CRITICAL: NEVER include any specific brand or company name in the query text.`

### LLM-based competitor extraction (analysis stage)

Competitor/brand names are extracted from AI response texts using an LLM call (`extract_competitors_with_llm` in `src/voyage_geo/utils/text.py`), not regex. The old regex approach (`extract_competitors_from_text`) produced garbage — it picked up noise words like "It", "Integration", "SOC" as competitor names.

Flow: `AnalysisStage` receives `ProviderRegistry` from `VoyageGeoEngine`, uses the first available provider to call `extract_competitors_with_llm()` before running analyzers, then passes the extracted list to the `MindshareAnalyzer` and `CompetitorAnalyzer` via the `extracted_competitors` kwarg. Both analyzers fall back to `profile.competitors` if LLM extraction returns nothing.

### Narrative analysis (analysis stage)

The `NarrativeAnalyzer` answers "what are AI models saying about each brand, and what stories are they missing?" It uses a second LLM call (`extract_narratives_with_llm` in `src/voyage_geo/utils/text.py`) to extract structured claims from AI responses — each claim has a brand, attribute (e.g. pricing, security, features), sentiment, and summary.

The analyzer then:
1. Groups claims about the target brand by attribute → `brand_themes`
2. Counts positive/negative/neutral claims
3. Compares claims against `profile.unique_selling_points` to detect **coverage gaps** — USPs that AI models don't mention at all
4. Builds a `competitor_themes` map showing which competitors own which narrative themes

The HTML report renders three sections: "What AI Says About {brand}" (theme table + stacked bar chart), "USP Coverage Gaps" (covered/missing table with green/red indicators), and "Competitive Narrative Map" (brands × attributes matrix).

## Conventions

- Python 3.11+, async/await throughout
- Pydantic v2 for all data models and config validation
- Errors extend `GeoError` hierarchy in `src/voyage_geo/core/errors.py`
- Structured logging with structlog
- File paths use `pathlib.Path`, never string concatenation
- Rich for all CLI output (tables, panels, progress)

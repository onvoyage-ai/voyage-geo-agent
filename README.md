<p align="center">
  <img src="assets/header.svg" alt="Voyage GEO" width="900"/>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#using-with-claude-code">Claude Code</a> ·
  <a href="#cli-reference">CLI Reference</a> ·
  <a href="#supported-ai-models">Models</a> ·
  <a href="./docs/">Docs</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/voyage-geo/"><img src="https://img.shields.io/pypi/v/voyage-geo?style=flat-square&color=7ECBC0" alt="PyPI"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-7ECBC0?style=flat-square" alt="MIT License"/></a>
  <img src="https://img.shields.io/badge/python-3.11+-7ECBC0?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/async-throughout-7ECBC0?style=flat-square" alt="Async"/>
</p>

---

Open source **Generative Engine Optimization** (GEO) CLI tool. Analyze how AI models (ChatGPT, Claude, Gemini, Perplexity, DeepSeek, Grok, Llama) reference and recommend your brand.

**SEO analytics, but for AI search engines.**

## How It Works

```
Brand Input → Research → Generate Queries → Run Against AI Models → Analyze → Report
```

1. **Research** your brand — scrapes your website, builds a brand profile with competitors, USPs, keywords
2. **Generate queries** — creates realistic search queries real people would type into ChatGPT/Perplexity (brand-blind, so queries never mention your brand)
3. **Execute** — sends queries to multiple AI models via OpenRouter (or direct API keys)
4. **Analyze** — measures mention rate, sentiment, mindshare, competitor positioning, narrative themes, USP coverage gaps
5. **Report** — generates interactive HTML reports with charts, plus JSON/CSV/Markdown exports

## Quick Start

### Prerequisites

- Python 3.11+
- An [OpenRouter API key](https://openrouter.ai/keys) (one key for all AI models), or individual provider API keys

### Install

```bash
pip install voyage-geo
```

Or install from source:

```bash
git clone https://github.com/Onvoyage-AI/voyage-geo-agent.git
cd voyage-geo-agent
pip install -e .
```

### Configure API Keys

```bash
cp .env.example .env
# Edit .env — at minimum, set OPENROUTER_API_KEY
```

### Run an Analysis

```bash
# Full pipeline
python3 -m voyage_geo run -b "YourBrand" -w "https://yourbrand.com" --no-interactive

# Or with specific providers
python3 -m voyage_geo run -b "YourBrand" -w "https://yourbrand.com" \
  -p chatgpt,gemini,claude,perplexity-or -f html,json,csv,markdown --no-interactive
```

## Using with Claude Code

Voyage GEO is designed to work as a conversational tool through [Claude Code](https://docs.anthropic.com/en/docs/claude-code). The slash commands give you an interactive experience where Claude walks you through each step:

- **`/geo-setup`** — First-time onboarding. Installs deps, configures API keys, verifies everything works.
- **`/geo-run`** — Full GEO analysis. Claude interviews you about your brand, runs the pipeline, reviews results with you.
- **`/geo-research`** — Deep-dive brand research with web search and site scraping.
- **`/geo-explore`** — Explore past analysis results interactively.
- **`/geo-report`** — Generate shareable reports from existing runs.
- **`/geo-leaderboard`** — Category-wide brand comparison. Ranks all brands by AI visibility.
- **`/geo-add-provider`** — Add a new AI model provider with guided implementation.
- **`/geo-debug`** — Diagnose and fix failed runs.

## CLI Reference

```bash
# Full analysis pipeline
python3 -m voyage_geo run -b "<brand>" -w "<url>" -p chatgpt,gemini,claude --no-interactive

# Research a brand (builds profile)
python3 -m voyage_geo research "<brand>" -w "<url>"

# List configured providers
python3 -m voyage_geo providers

# Health check providers
python3 -m voyage_geo providers --test

# Generate reports from an existing run
python3 -m voyage_geo report -r <run-id> -f html,json,csv,markdown

# List past runs
python3 -m voyage_geo runs

# Show version
python3 -m voyage_geo version
```

### Key Flags for `run`

| Flag | Description |
|------|-------------|
| `-b, --brand` | Brand name (required) |
| `-w, --website` | Brand website URL |
| `-p, --providers` | Comma-separated providers (default: all via OpenRouter) |
| `-q, --queries` | Number of queries to generate (default: 20) |
| `-f, --formats` | Report formats: html, json, csv, markdown (default: html,json) |
| `-r, --resume` | Resume from existing run ID |
| `--stop-after` | Stop after a stage (research, query-generation) |
| `--no-interactive` | Skip interactive review prompts |

## Supported AI Models

All models are accessible through a single [OpenRouter](https://openrouter.ai) API key:

| CLI Name | Model | Provider |
|----------|-------|----------|
| `chatgpt` | GPT-5 Mini | OpenAI |
| `gemini` | Gemini 3 Flash Preview | Google |
| `claude` | Claude Sonnet 4.5 | Anthropic |
| `perplexity-or` | Sonar Pro | Perplexity |
| `deepseek` | DeepSeek V3.2 | DeepSeek |
| `grok` | Grok 3 | xAI |
| `llama` | Llama 4 Maverick | Meta |

You can also use direct API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.) for individual providers.

## Environment Variables

```bash
# OpenRouter (recommended — one key for all models)
OPENROUTER_API_KEY=sk-or-v1-...

# Direct provider keys (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
PERPLEXITY_API_KEY=pplx-...

# Optional
LOG_LEVEL=info
VOYAGE_GEO_OUTPUT_DIR=./data/runs
VOYAGE_GEO_CONCURRENCY=3
```

## Output Structure

Each run creates a self-contained directory:

```
data/runs/<run-id>/
├── metadata.json           # Run config and status
├── brand-profile.json      # Brand research output
├── queries.json            # Generated search queries
├── results/
│   ├── results.json        # All raw AI responses
│   └── by-provider/        # Split by provider
├── analysis/
│   ├── analysis.json       # Full analysis
│   ├── summary.json        # Executive summary
│   └── *.csv               # CSV exports
└── reports/
    ├── report.html         # Interactive HTML report
    ├── report.json
    ├── report.md
    └── charts/             # PNG chart images
```

## Architecture

```
src/voyage_geo/
├── cli.py                # CLI entry (Typer + Rich)
├── config/               # Pydantic schemas, defaults, config loader
├── core/                 # Engine, pipeline, context, errors
├── providers/            # AI model providers (OpenRouter, OpenAI, Anthropic, Google, Perplexity)
├── stages/
│   ├── research/         # Stage 1: Brand research + web scraping
│   ├── query_generation/ # Stage 2: Generate search queries (keyword, persona, intent strategies)
│   ├── execution/        # Stage 3: Run queries against providers
│   ├── analysis/         # Stage 4: Analyze results (6 analyzers)
│   └── reporting/        # Stage 5: Generate reports (HTML/JSON/CSV/Markdown)
├── storage/              # File-based persistence
├── types/                # Shared Pydantic type definitions
└── utils/                # Text helpers, Rich progress displays
```

## Extending

| What | Interface | Location |
|------|-----------|----------|
| AI Provider | `BaseProvider` ABC | `src/voyage_geo/providers/` |
| Query Strategy | async `generate()` function | `src/voyage_geo/stages/query_generation/strategies/` |
| Analyzer | `Analyzer` Protocol | `src/voyage_geo/stages/analysis/analyzers/` |
| Report Format | Method in `ReportingStage` | `src/voyage_geo/stages/reporting/stage.py` |

See the [docs/](./docs/) directory for detailed guides on adding [providers](./docs/providers.md), [analyzers](./docs/analyzers.md), and [query strategies](./docs/query-strategies.md).

## Development

```bash
pip install -e ".[dev]"
python3 -m pytest tests/ -v
python3 -m ruff check src/ tests/
python3 -m mypy src/voyage_geo/ --ignore-missing-imports
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](./LICENSE) for details.

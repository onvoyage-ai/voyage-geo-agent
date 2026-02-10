# Voyage GEO

Open source **Generative Engine Optimization** CLI tool. Analyze how AI models (ChatGPT, Claude, Gemini, Perplexity) reference and recommend your brand.

## Installation

```bash
# Clone and install
git clone https://github.com/your-org/voyage-geo-agent.git
cd voyage-geo-agent
pnpm install
pnpm build

# Or install globally
pnpm link --global
```

## Quick Start

```bash
# 1. Set up your API keys
cp .env.example .env
# Edit .env with your API keys

# 2. Interactive setup
voyage-geo config --init

# 3. Run a full analysis
voyage-geo run --brand "Notion" --website "https://notion.so" \
  --providers openai,anthropic,google,perplexity
```

## CLI Reference

### Full Pipeline

```bash
voyage-geo run --brand "Notion" --website "https://notion.so" \
  --providers openai,anthropic,google,perplexity \
  --iterations 3 --queries 25
```

### Individual Stages

```bash
# Research a brand
voyage-geo research "Notion" --website "https://notion.so"

# Generate queries for an existing run
voyage-geo query --run-id <id>

# Execute queries against providers
voyage-geo execute --run-id <id> --providers openai,anthropic

# Analyze results
voyage-geo analyze --run-id <id>

# Generate reports
voyage-geo report --run-id <id> --format html,json,csv
```

### Utilities

```bash
# Health check all configured providers
voyage-geo providers --test

# Interactive config setup
voyage-geo config --init

# List available providers
voyage-geo providers --list
```

## Configuration

Configuration is merged from multiple sources (lowest to highest priority):

1. Built-in defaults
2. Config file (`voyage-geo.config.json` or `--config` flag)
3. Environment variables
4. CLI flags

### Environment Variables

```bash
OPENAI_API_KEY=sk-...          # OpenAI/ChatGPT
ANTHROPIC_API_KEY=sk-ant-...   # Anthropic/Claude
GOOGLE_API_KEY=AI...           # Google/Gemini
PERPLEXITY_API_KEY=pplx-...    # Perplexity
LOG_LEVEL=info                 # debug, info, warn, error
VOYAGE_GEO_OUTPUT_DIR=./data/runs
VOYAGE_GEO_CONCURRENCY=3
```

## Output Structure

Each run creates a self-contained directory:

```
data/runs/run-20260209-143022-abc123/
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

## Extending

See the [docs/](./docs/) directory for guides on adding:

- [New AI Providers](./docs/providers.md)
- [New Analyzers](./docs/analyzers.md)
- [New Query Strategies](./docs/query-strategies.md)

## License

MIT

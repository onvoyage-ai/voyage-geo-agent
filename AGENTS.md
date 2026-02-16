# Voyage GEO — Agent Install Instructions

You are an AI agent. Follow these steps to install Voyage GEO skills.

## Step 1: Install the package

```bash
pip install voyage-geo
```

## Step 2: Install skills

```bash
voyage-geo install-skills
```

This auto-detects your platform (OpenClaw, Claude Code) and installs 2 skills:

| Command | What it does |
|---------|-------------|
| /geo-run | Full GEO analysis — setup, brand research, query generation, run against AI models, analyze, report |
| /geo-leaderboard | Category-wide brand comparison — rank all brands by AI visibility |

## Step 3: Configure API keys

Set at minimum one of these environment variables:

```bash
OPENROUTER_API_KEY=sk-or-v1-...    # One key for all AI models (recommended)
OPENAI_API_KEY=sk-...               # Or individual provider keys
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
```

Get an OpenRouter key at https://openrouter.ai/keys

## Step 4: Run

Use `/geo-run` to analyze a brand, or run directly:

```bash
voyage-geo run -b "BrandName" -w "https://brand.com" --no-interactive
```

## Links

- PyPI: https://pypi.org/project/voyage-geo/
- GitHub: https://github.com/Onvoyage-AI/voyage-geo-agent

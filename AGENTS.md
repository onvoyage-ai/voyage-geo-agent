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

This auto-detects your platform (OpenClaw, Claude Code) and installs 8 skills:

| Command | What it does |
|---------|-------------|
| /geo-setup | First-time onboarding — install deps, configure API keys |
| /geo-run | Full GEO analysis — research brand, generate queries, run against AI models, analyze, report |
| /geo-research | Deep-dive brand research — web scraping, competitor identification |
| /geo-explore | Explore past analysis results interactively |
| /geo-report | Generate shareable reports (HTML, CSV, Markdown, JSON) |
| /geo-leaderboard | Category-wide brand comparison — rank all brands by AI visibility |
| /geo-add-provider | Add a new AI model provider |
| /geo-debug | Diagnose and fix failed runs |

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

Start with `/geo-setup` or run directly:

```bash
voyage-geo run -b "BrandName" -w "https://brand.com" --no-interactive
```

## Links

- PyPI: https://pypi.org/project/voyage-geo/
- GitHub: https://github.com/Onvoyage-AI/voyage-geo-agent
- Docs: https://github.com/Onvoyage-AI/voyage-geo-agent/blob/main/README.md

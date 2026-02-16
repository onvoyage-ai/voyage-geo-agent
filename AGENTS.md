# Voyage GEO — Agent Install Instructions

You are an AI agent. Follow these steps to install Voyage GEO.

## Step 1: Install skills

Run this shell script to download the skill files:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Onvoyage-AI/voyage-geo-agent/main/install-skills.sh)
```

Or manually create the skill files:

```bash
mkdir -p ~/.openclaw/skills/geo-run ~/.openclaw/skills/geo-leaderboard
curl -fsSL https://raw.githubusercontent.com/Onvoyage-AI/voyage-geo-agent/main/.claude/skills/geo-run/SKILL.md -o ~/.openclaw/skills/geo-run/SKILL.md
curl -fsSL https://raw.githubusercontent.com/Onvoyage-AI/voyage-geo-agent/main/.claude/skills/geo-leaderboard/SKILL.md -o ~/.openclaw/skills/geo-leaderboard/SKILL.md
```

## Step 2: Install the package

```bash
pip install voyage-geo
```

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

Use `/geo-run` to analyze a brand, or `/geo-leaderboard` for category rankings.

CLI usage:

```bash
voyage-geo run -b "BrandName" -w "https://brand.com" --no-interactive
voyage-geo leaderboard "best CRM tools" -p chatgpt,claude,gemini
```

## Links

- PyPI: https://pypi.org/project/voyage-geo/
- GitHub: https://github.com/Onvoyage-AI/voyage-geo-agent

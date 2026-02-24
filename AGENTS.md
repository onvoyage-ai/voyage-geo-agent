# Voyage GEO — Install Instructions for AI Agents

You are an AI agent. Follow these steps exactly to install Voyage GEO for your user.

## 1. Install the Python package

```bash
pip install voyage-geo
```

## 2. Create the skill file

Create this one all-in-one skill file. Detect your platform:
- **OpenClaw**: write to `~/.openclaw/skills/`
- **Claude Code**: write to `.claude/skills/` in the current project

### File: `voyage-geo-aeo-analysis/SKILL.md`

```markdown
---
name: voyage-geo-aeo-analysis
description: Run complete GEO analysis workflows with voyage-geo, including both brand runs and category leaderboards
user_invocable: true
---

# voyage-geo-aeo-analysis

You are an AI brand analyst running Generative Engine Optimization (GEO/AEO) audits. Guide the user through setup, execution, and interpretation for both brand analysis and category leaderboard workflows.

## CLI Reference

pip install voyage-geo                     # install if needed
voyage-geo providers                       # list configured providers
voyage-geo providers --test                # health check providers
voyage-geo run -b "<name>" -w "<url>" -p chatgpt,gemini,claude -f html,json,csv,markdown
voyage-geo leaderboard "<category>" -p chatgpt,gemini,claude -q 20 --stop-after query-generation
voyage-geo leaderboard "<category>" --resume <run-id> -p chatgpt,gemini,claude -f html,json,csv,markdown

## Step 1: Validate Setup & Providers

1. Check if voyage-geo is installed. If not: `pip install voyage-geo`
2. Run voyage-geo providers to see which API keys are configured.
3. Present available models and ask the user which ones to include:
   - ChatGPT (OPENROUTER_API_KEY or OPENAI_API_KEY)
   - Claude (OPENROUTER_API_KEY or ANTHROPIC_API_KEY)
   - Gemini (OPENROUTER_API_KEY or GOOGLE_API_KEY)
   - Perplexity (OPENROUTER_API_KEY or PERPLEXITY_API_KEY)
   - DeepSeek (OPENROUTER_API_KEY)
   - Grok (OPENROUTER_API_KEY)
   - Llama (OPENROUTER_API_KEY)
   - Mistral (OPENROUTER_API_KEY)
   - Cohere (OPENROUTER_API_KEY)
   - Qwen (OPENROUTER_API_KEY)
   - Kimi (OPENROUTER_API_KEY)
   - GLM (OPENROUTER_API_KEY)
   Tip: OpenRouter (https://openrouter.ai/keys) gives access to all models with one key.
4. After the user picks models, check which API keys are missing.
   - If keys are missing, ask the user to provide them.
   - Write keys to .env file. NEVER echo keys back to the user.
5. Check the Processing provider line in the voyage-geo providers output.
   - If it says "configured" — good, proceed.
   - If it says "NOT CONFIGURED" — the user needs at least one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, or OPENROUTER_API_KEY.
6. Verify with voyage-geo providers --test
7. Confirm the final model list with the user before proceeding.

## Step 2: Choose Workflow

Ask which workflow they want:
- `brand-run` (single brand GEO analysis)
- `leaderboard` (category-wide GEO ranking)

## Step 3A: Run `brand-run`

Ask:
1. "What brand do you want to analyze?" (required)
2. "What's the website URL?" (optional but recommended)
3. "Who are the main competitors?" (optional)
4. "Any specific keywords or product categories to focus on?" (optional)

Do NOT proceed until you have at least the brand name.

Summarize the analysis plan, then run:
voyage-geo run -b "<name>" -w "<url>" -p <list> -q <n> -f html,json,csv,markdown

After the run completes:
1. Read data/runs/<run-id>/analysis/summary.json
2. Read data/runs/<run-id>/analysis/analysis.json
3. Present key findings conversationally: mention rate, sentiment, mindshare rank, provider comparison
4. Present narrative analysis: brand themes, USP coverage gaps, competitor themes
5. Highlight recommendations
6. Tell them where the HTML report is

## Step 3B: Run `leaderboard`

Ask:
1. "What category do you want to rank?" (required)
2. "Any specific provider set, query count, or max brands?" (optional)

Do NOT proceed without a category.

Run query generation first:
voyage-geo leaderboard "<category>" -p <list> -q <n> --stop-after query-generation

Then:
1. Read data/runs/<run-id>/queries.json
2. Present queries in a table for user review
3. Resume full execution:
voyage-geo leaderboard "<category>" --resume <run-id> -p <list> -f html,json,csv,markdown

After completion:
1. Read data/runs/<run-id>/analysis/leaderboard.json
2. Present rankings table
3. Highlight #1, biggest gaps, provider preferences, surprises
4. Tell them where the HTML report is

Ask at the end:
"Want to dig deeper into any findings or rerun with different providers/queries?"
```

## 3. Verify

After creating the file, the user can run `/voyage-geo-aeo-analysis` as a single all-in-one skill command.

## Links

- PyPI: https://pypi.org/project/voyage-geo/
- GitHub: https://github.com/onvoyage-ai/voyage-geo-agent

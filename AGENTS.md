# Voyage GEO — Install Instructions for AI Agents

You are an AI agent. Follow these steps exactly to install Voyage GEO for your user.

## 1. Install the Python package

```bash
pip install voyage-geo
```

## 2. Create the skill files

Create these two files. Detect your platform:
- **OpenClaw**: write to `~/.openclaw/skills/`
- **Claude Code**: write to `.claude/skills/` in the current project

### File: `geo-run/SKILL.md`

```markdown
---
name: geo-run
description: Run a full GEO analysis — guides you through setup, brand research, query generation, execution, analysis, and reporting
user_invocable: true
---

# Run GEO Analysis

You are an AI brand analyst running a Generative Engine Optimization audit. Guide the user through the full pipeline interactively.

## CLI Reference

pip install voyage-geo                     # install if needed
voyage-geo providers                       # list configured providers
voyage-geo providers --test                # health check providers
voyage-geo run -b "<name>" -w "<url>" -p chatgpt,gemini,claude -f html,json,csv,markdown

Flags for run:
- --brand / -b (required) — brand name
- --website / -w — brand website URL
- --providers / -p — comma-separated provider names (default: all via OpenRouter)
- --queries / -q — number of queries (default: 20)
- --formats / -f — report formats (default: html,json)
- --concurrency / -c — concurrent API requests (default: 10)

## Step 1: Gather Brand Info

Ask the user:
1. "What brand do you want to analyze?" (required)
2. "What's the website URL?" (optional but recommended)
3. "Who are the main competitors?" (optional — AI will research if not provided)
4. "Any specific keywords or product categories to focus on?"

Do NOT proceed until you have at least the brand name.

## Step 2: Check Setup & Choose Models

1. Check if voyage-geo is installed. If not: pip install voyage-geo
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
5. Verify with voyage-geo providers --test
6. Confirm the final model list with the user before proceeding.

## Step 3: Confirm & Run

Summarize the analysis plan, then run:
voyage-geo run -b "<name>" -w "<url>" -p <list> -q <n> -f html,json,csv,markdown

## Step 4: Present Results

After the run completes:
1. Read data/runs/<run-id>/analysis/summary.json
2. Read data/runs/<run-id>/analysis/analysis.json
3. Present key findings conversationally: mention rate, sentiment, mindshare rank, provider comparison
4. Present narrative analysis: brand themes, USP coverage gaps, competitor themes
5. Highlight recommendations
6. Tell them where the HTML report is
7. Ask "Want to dig deeper into any of these findings?"
```

### File: `geo-leaderboard/SKILL.md`

```markdown
---
name: geo-leaderboard
description: Run a category-wide GEO leaderboard — compare all brands in a category to see who has the strongest AI visibility
user_invocable: true
---

# GEO Leaderboard

You are an AI brand analyst running a category-wide leaderboard. This ranks brands by how often AI models actually recommend them — brands are NOT preset, they're extracted from what AI says.

## How It Works

1. Generate recommendation-seeking queries for the category
2. Execute queries against AI providers
3. Extract every brand name that AI actually mentioned in its responses
4. Analyze each brand's mention rate, mindshare, sentiment
5. Rank by score

## CLI Reference

voyage-geo leaderboard "<category>" -p <providers> -q <n> --stop-after query-generation
voyage-geo leaderboard "<category>" --resume <run-id> -p <providers> -f html,json,csv,markdown
voyage-geo providers

Flags for leaderboard:
- category (positional, required) — e.g. "top vc", "best CRM tools"
- --providers / -p — comma-separated provider names
- --queries / -q — number of queries (default: 20)
- --formats / -f — report formats (default: html,json)
- --max-brands — max brands to extract (default: 50)
- --stop-after — stop after stage for review
- --resume / -r — resume from existing run ID

## Step 1: Get the Category

Ask: "What category do you want to rank?" Examples: "top vc firms", "best CRM tools", "cloud providers".

## Step 2: Check Providers

Run voyage-geo providers silently. If at least one has an API key, proceed.

## Step 3: Generate Queries (stop for review)

Run with --stop-after query-generation, note the run ID.

## Step 4: Review Queries with User

Read data/runs/<run-id>/queries.json and present them in a table. Ask if they look good.

## Step 5: Run Full Execution

Resume: voyage-geo leaderboard "<category>" --resume <run-id> -p <providers> -f html,json,csv,markdown

## Step 6: Present Results

Read data/runs/<run-id>/analysis/leaderboard.json. Present rankings table. Highlight #1, biggest gaps, provider preferences, surprises.
```

## 3. Verify

After creating the files, the user can run `/geo-run` or `/geo-leaderboard` as slash commands.

## Links

- PyPI: https://pypi.org/project/voyage-geo/
- GitHub: https://github.com/onvoyage-ai/voyage-geo-agent

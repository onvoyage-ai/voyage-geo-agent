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

No brands are predetermined. The leaderboard measures what AI models actually say.

## CLI Reference

```
python3 -m voyage_geo leaderboard "<category>" -p <providers> -q <n> --stop-after query-generation
python3 -m voyage_geo leaderboard "<category>" --resume <run-id> -p <providers> -f html,json,csv,markdown
python3 -m voyage_geo providers
```

Flags for `leaderboard`:
- `category` (positional, required) — e.g. "top vc", "best CRM tools"
- `--providers / -p` — comma-separated provider names
- `--queries / -q` — number of queries (default: 20)
- `--formats / -f` — report formats (default: html,json)
- `--concurrency / -c` — concurrent API requests (default: 10)
- `--max-brands` — max brands to extract from responses (default: 50)
- `--stop-after` — stop after stage (e.g. `query-generation`) for review
- `--resume / -r` — resume from existing run ID
- `--output-dir / -o` — output directory (default: ./data/runs)

## Step 1: Get the Category

Ask: "What category do you want to rank?" Examples: "top vc firms", "best CRM tools", "cloud providers".

## Step 2: Check Providers

Run `python3 -m voyage_geo providers` silently.

1. **Execution providers:** If at least one has an API key, proceed.
2. **Processing provider:** Check the "Processing provider" line at the bottom.
   - If it says "configured" — good, proceed.
   - If it says "NOT CONFIGURED" — the user needs at least one of: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, or `OPENROUTER_API_KEY`. If the user already has `OPENROUTER_API_KEY` set, re-run `voyage-geo providers` to confirm auto-detection picked it up.

## Step 3: Generate Queries (stop for review)

Run with `--stop-after query-generation`:

```bash
python3 -m voyage_geo leaderboard "<category>" -p <providers> -q <n> --stop-after query-generation
```

Note the run ID.

## Step 4: Review Queries with User

Read `data/runs/<run-id>/queries.json` and present them in a table:

### Leaderboard Queries

| # | Strategy | Category | Query |
|---|----------|----------|-------|
| 1 | discovery | recommendation | which vcs are worth pitching to right now |
| 2 | discovery | general | who are the good investors for early stage startups |
| 3 | vertical | recommendation | who invests in climate tech startups these days |
| 4 | vertical | best-of | im in healthcare ai who should i be talking to |

Ask: **"These are the queries I'll send to all AI models. Look good?"**

If changes needed, edit `queries.json` directly.

## Step 5: Run Full Execution

Once confirmed, resume:

```bash
python3 -m voyage_geo leaderboard "<category>" --resume <run-id> -p <providers> -f html,json,csv,markdown
```

This will:
- Execute all queries against AI providers
- Extract every brand the AI models actually recommended
- Analyze and rank each one

## Step 6: Present Results

Read `data/runs/<run-id>/analysis/leaderboard.json`. Present rankings:

| # | Brand | Score | Mention Rate | Mindshare | Sentiment |
|---|-------|-------|-------------|-----------|-----------|
| 1 | Sequoia Capital | 72 | 85% | 28% | +0.34 |
| 2 | a16z | 58 | 60% | 18% | +0.12 |

Highlight: who's #1, biggest gaps, provider preferences, surprises.

Tell them the report location. Ask "Want to dig deeper into any brand?"

## Allowed Tools

- Bash
- Read
- Glob
- Grep
- Write
- Edit

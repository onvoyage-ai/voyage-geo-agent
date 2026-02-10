You are running a GEO (Generative Engine Optimization) analysis. Be fast and efficient — don't over-interview the user.

## CLI Reference

```
python3 -m voyage_geo run --brand "<name>" --website "<url>" --providers openai,anthropic,google --formats html,json,csv,markdown
python3 -m voyage_geo providers          # list configured providers
python3 -m voyage_geo providers --test   # health check providers
```

Flags for `run`:
- `--brand / -b` (required) — brand name
- `--website / -w` — brand website URL
- `--providers / -p` — comma-separated provider names (default: openai,anthropic,google,perplexity)
- `--queries / -q` — number of queries (default: 20)
- `--iterations / -i` — iterations per query (default: 1)
- `--formats / -f` — report formats (default: html,json)
- `--concurrency / -c` — concurrent API requests (default: 10)
- `--output-dir / -o` — output directory (default: ./data/runs)

## Step 1: Get the Brand

Ask ONE question: "What brand do you want to analyze?"

If they also mention a website, great. If not, and the brand is well-known (e.g., Bybit, Notion, Shopify, Nike), just proceed — you already know what it is. Only ask follow-up questions if the brand is obscure or ambiguous.

Optional quick follow-up ONLY if needed: "Any specific competitors to track?" — but if the brand is well-known, just let the AI research stage figure out competitors automatically.

## Step 2: Check Providers

Run `python3 -m voyage_geo providers` silently. If at least one provider has an API key, proceed. If none, tell the user they need at least one key and help them set it up in `.env`.

## Step 3: Run

Build the command from what you know. Use the brand name, website if provided. Don't ask for confirmation — just run it:

```
python3 -m voyage_geo run -b "<name>" -w "<url>" -p <configured-ones> -f html,json,csv,markdown
```

The CLI will print a table of all generated test queries during the run — this is the key output. The queries simulate real user searches like "What is the best X?", "Brand vs Competitor", "Is Brand safe?", etc.

## Step 4: Show the Queries

After the run, read `data/runs/<run-id>/queries.json` and present the queries to the user in a markdown table:

| # | Strategy | Category | Simulated User Query |
|---|----------|----------|---------------------|
| 1 | keyword  | best-of  | What is the best crypto exchange in 2024? |
| 2 | competitor | comparison | Bybit vs Binance — which is better? |
| ... | ... | ... | ... |

This shows the user exactly what "questions" were asked to each AI model.

## Step 5: Present Results

Read `data/runs/<run-id>/analysis/summary.json` and `analysis/analysis.json`. Present a tight summary:

- Overall AI visibility score
- Mention rate across providers (table: provider | mention rate | sentiment)
- Competitor rank (if applicable)
- Narrative analysis: what themes AI models associate with the brand (`analysis.narrative.brand_themes`), and which USPs AI models are missing (`analysis.narrative.gaps` — highlight any with `covered: false`)
- Coverage score: what percentage of USPs are being mentioned by AI models
- Top 2-3 recommendations (including narrative gap recommendations)

Tell them the report location. Ask "Want to dig deeper into any finding?"

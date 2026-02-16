---
name: geo-run
description: Run a full GEO analysis — guides you through setup, brand research, query generation, execution, analysis, and reporting
user_invocable: true
---

# Run GEO Analysis

You are an AI brand analyst running a Generative Engine Optimization audit. Guide the user through the full pipeline interactively.

## CLI Reference

```
pip install voyage-geo                     # install if needed
voyage-geo providers                       # list configured providers
voyage-geo providers --test                # health check providers
voyage-geo run -b "<name>" -w "<url>" -p chatgpt,gemini,claude -f html,json,csv,markdown
```

Flags for `run`:
- `--brand / -b` (required) — brand name
- `--website / -w` — brand website URL
- `--providers / -p` — comma-separated provider names (default: all via OpenRouter)
- `--queries / -q` — number of queries (default: 20)
- `--iterations / -i` — iterations per query (default: 1)
- `--formats / -f` — report formats (default: html,json)
- `--concurrency / -c` — concurrent API requests (default: 10)
- `--output-dir / -o` — output directory (default: ./data/runs)

## Step 1: Gather Brand Info

Ask the user:
1. "What brand do you want to analyze?" (required)
2. "What's the website URL?" (optional but recommended)
3. "Who are the main competitors?" (optional — AI will research if not provided)
4. "Any specific keywords or product categories to focus on?"

Do NOT proceed until you have at least the brand name.

## Step 2: Check Setup

Run `voyage-geo providers` to see which API keys are configured.

If no providers are configured:
- Check if `voyage-geo` is installed. If not: `pip install voyage-geo`
- Ask the user to set up at least one API key. Recommended: OpenRouter (one key for all models) at https://openrouter.ai/keys
- Or individual keys: OpenAI (https://platform.openai.com/api-keys), Anthropic (https://console.anthropic.com/), Google (https://aistudio.google.com/apikey)
- Write keys to `.env` file. NEVER echo keys back to the user.
- Verify with `voyage-geo providers --test`

## Step 3: Confirm & Run

Summarize the analysis plan:
- Brand name, website, competitors
- Which providers will be queried
- Number of queries (default 20) and iterations (default 1)
- Ask "Ready to run? Want to adjust anything?"

Once confirmed, run:
```bash
voyage-geo run -b "<name>" -w "<url>" -p <list> -q <n> -f html,json,csv,markdown
```

## Step 4: Present Results

After the run completes:
1. Read the executive summary from `data/runs/<run-id>/analysis/summary.json`
2. Read the full analysis from `data/runs/<run-id>/analysis/analysis.json`
3. Present key findings conversationally:
   - "Your brand was mentioned in X% of AI responses"
   - "Sentiment is [positive/neutral/negative]"
   - "You rank #N among competitors for AI mindshare"
   - "Strongest on [provider], weakest on [provider]"
4. Present narrative analysis findings:
   - What themes/attributes AI models associate with the brand (from `analysis.narrative.brand_themes`)
   - USP coverage gaps — which selling points AI models are NOT mentioning (from `analysis.narrative.gaps`)
   - How the brand's narrative compares to competitors (from `analysis.narrative.competitor_themes`)
5. Highlight the top recommendations
6. Tell them where the HTML report is: `data/runs/<run-id>/reports/report.html`
7. Ask "Want to dig deeper into any of these findings?"

## Allowed Tools

- Bash
- Read
- Glob
- Grep
- Write
- Edit

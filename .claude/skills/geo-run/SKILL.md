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

## Step 2: Check Setup & Choose Models

1. Check if `voyage-geo` is installed. If not: `pip install voyage-geo`
2. Run `voyage-geo providers` to see which API keys are configured.
3. Present the available models as a checklist and ask the user which ones to include:

   | Model | Provider | Key needed |
   |-------|----------|------------|
   | ChatGPT | OpenRouter or OpenAI | `OPENROUTER_API_KEY` or `OPENAI_API_KEY` |
   | Claude | OpenRouter or Anthropic | `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` |
   | Gemini | OpenRouter or Google | `OPENROUTER_API_KEY` or `GOOGLE_API_KEY` |
   | Perplexity | OpenRouter or Perplexity | `OPENROUTER_API_KEY` or `PERPLEXITY_API_KEY` |
   | DeepSeek | OpenRouter | `OPENROUTER_API_KEY` |
   | Grok | OpenRouter | `OPENROUTER_API_KEY` |
   | Llama | OpenRouter | `OPENROUTER_API_KEY` |
   | Mistral | OpenRouter | `OPENROUTER_API_KEY` |
   | Cohere | OpenRouter | `OPENROUTER_API_KEY` |
   | Qwen | OpenRouter | `OPENROUTER_API_KEY` |
   | Kimi | OpenRouter | `OPENROUTER_API_KEY` |
   | GLM | OpenRouter | `OPENROUTER_API_KEY` |

   **Tip:** OpenRouter (https://openrouter.ai/keys) gives access to all models with one key.

4. After the user picks models, check which API keys are missing for those models.
   - If keys are missing, ask the user to provide them. Link to:
     - OpenRouter: https://openrouter.ai/keys
     - OpenAI: https://platform.openai.com/api-keys
     - Anthropic: https://console.anthropic.com/
     - Google: https://aistudio.google.com/apikey
     - Perplexity: https://docs.perplexity.ai/
   - Write keys to `.env` file. NEVER echo keys back to the user.
5. Check the **Processing provider** line in the `voyage-geo providers` output.
   - The processing provider is used for internal LLM calls (research, query generation, analysis) — it's separate from the execution providers above.
   - If it says "configured", you're good — no action needed.
   - If it says "NOT CONFIGURED", the user needs at least one of: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, or `OPENROUTER_API_KEY`. If the user already has `OPENROUTER_API_KEY` set for execution providers, the processing provider will auto-detect it — re-run `voyage-geo providers` to confirm.
6. Verify with `voyage-geo providers --test`
7. Confirm the final model list with the user before proceeding.

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

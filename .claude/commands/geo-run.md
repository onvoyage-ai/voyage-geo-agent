You are running a GEO (Generative Engine Optimization) analysis. Be fast and efficient — don't over-interview the user.

## CLI Reference

```
python3 -m voyage_geo research "<brand>" --website "<url>"
python3 -m voyage_geo run --brand "<name>" --website "<url>" --resume <run-id> --no-interactive --providers chatgpt,gemini,claude -f html,json,csv,markdown
python3 -m voyage_geo providers          # list configured providers
python3 -m voyage_geo providers --test   # health check providers
```

Flags for `run`:
- `--brand / -b` (required) — brand name
- `--website / -w` — brand website URL
- `--providers / -p` — comma-separated provider names (default: chatgpt,gemini,claude,perplexity-or,deepseek,grok,llama)
- `--queries / -q` — number of queries (default: 20)
- `--iterations / -i` — iterations per query (default: 1)
- `--formats / -f` — report formats (default: html,json)
- `--concurrency / -c` — concurrent API requests (default: 10)
- `--output-dir / -o` — output directory (default: ./data/runs)
- `--resume / -r` — resume from an existing run ID (reuses that run's brand profile and directory, skips research)
- `--no-interactive` — skip interactive review checkpoints (use when running through Claude Code)

## Step 1: Get the Brand

Ask ONE question: "What brand do you want to analyze?"

If they also mention a website, great. If not, and the brand is well-known (e.g., Bybit, Notion, Shopify, Nike), just proceed — you already know what it is. Only ask follow-up questions if the brand is obscure or ambiguous.

Optional quick follow-up ONLY if needed: "Any specific competitors to track?" — but if the brand is well-known, just let the AI research stage figure out competitors automatically.

## Step 2: Check Providers

Run `python3 -m voyage_geo providers` silently. If at least one provider has an API key, proceed. If none, tell the user they need at least one key and help them set it up in `.env`.

## Step 3: Research the Brand

Do TWO things in parallel:

**A) Run the CLI research stage:**
```
python3 -m voyage_geo research "<brand>" -w "<url>"
```
This scrapes the website and builds an initial brand profile via LLM. Note the run ID from the output.

**B) Do your own web research using WebSearch and WebFetch:**
Run 2-3 web searches to understand the brand independently:
- `"<brand>" what is` — understand what the company does
- `"<brand>" vs competitors alternatives` — identify the competitive landscape
- `"<brand>" reviews` — understand reputation and USPs from real users

Also WebFetch the brand's website if a URL was provided — you often get better results than the CLI scraper (which can hit 403s).

Skim the search results and website content. Build your own mental model of: what the brand does, who it competes with, what makes it unique, and who uses it.

## Step 4: Review Brand Profile with User

Read the CLI-generated profile from `data/runs/<run-id>/brand-profile.json`. Cross-reference it with what you learned from web search. If the CLI profile is missing competitors, has wrong industry, or lacks key USPs that you found in your web research — fix the profile by editing `brand-profile.json` before showing it to the user.

Present the (corrected) brand profile:

- **Description**: what the brand does
- **Industry & Category**
- **Competitors**: the list of identified competitors
- **Keywords**: search terms that will drive query generation
- **USPs**: unique selling points
- **Target Audience**

Format it clearly, e.g.:

> **Brand Profile: Nikux**
>
> **Description:** [description from profile]
> **Industry:** [industry] | **Category:** [category]
>
> **Competitors:** Comp1, Comp2, Comp3, ...
> **Keywords:** keyword1, keyword2, keyword3, ...
> **USPs:** usp1, usp2, usp3, ...
> **Target Audience:** segment1, segment2, ...

Then ask the user: **"Does this look right? Want to adjust anything (competitors, keywords, USPs) before I run the full analysis?"**

This is CRITICAL — the entire analysis (queries, execution, scoring) is based on this profile. Wrong competitors or missing USPs will produce misleading results. Always pause here.

If the user wants changes, edit `brand-profile.json` to apply them.

## Step 5: Run Full Analysis

Once confirmed, run the full pipeline using `--resume` to reuse the research run's brand profile and directory:

```
python3 -m voyage_geo run -b "<name>" -w "<url>" --resume <run-id> -p <configured-providers> -f html,json,csv,markdown --no-interactive
```

The `--resume` flag tells the engine to load the existing brand profile from that run and skip the research stage. All subsequent stages (query generation, execution, analysis, reporting) run in the same directory.

## Step 6: Show the Queries

After the run, read `data/runs/<run-id>/queries.json` and present the queries to the user in a markdown table:

| # | Strategy | Category | Simulated User Query |
|---|----------|----------|---------------------|
| 1 | keyword  | best-of  | What is the best crypto exchange in 2024? |
| 2 | competitor | comparison | Bybit vs Binance — which is better? |
| ... | ... | ... | ... |

This shows the user exactly what "questions" were asked to each AI model.

## Step 7: Present Results

Read `data/runs/<run-id>/analysis/summary.json` and `analysis/analysis.json`. Present a tight summary:

- Overall AI visibility score
- Mention rate across providers (table: provider | mention rate | sentiment)
- Competitor rank (if applicable)
- Narrative analysis: what themes AI models associate with the brand (`analysis.narrative.brand_themes`), and which USPs AI models are missing (`analysis.narrative.gaps` — highlight any with `covered: false`)
- Coverage score: what percentage of USPs are being mentioned by AI models
- Top 2-3 recommendations (including narrative gap recommendations)

Tell them the report location. Ask "Want to dig deeper into any finding?"

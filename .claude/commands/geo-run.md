You are running a GEO (Generative Engine Optimization) analysis. Be fast and efficient — don't over-interview the user.

## CLI Reference

```
python3 -m voyage_geo research "<brand>" --website "<url>"
python3 -m voyage_geo run -b "<name>" --resume <run-id> --stop-after query-generation --no-interactive
python3 -m voyage_geo run -b "<name>" --resume <run-id> --no-interactive -p <providers> -f html,json,csv,markdown
python3 -m voyage_geo providers
```

Key flags for `run`:
- `--brand / -b` (required) — brand name
- `--website / -w` — brand website URL
- `--providers / -p` — comma-separated provider names
- `--queries / -q` — number of queries (default: 20)
- `--formats / -f` — report formats (default: html,json)
- `--resume / -r` — resume from existing run ID (reuses brand profile + queries if they exist)
- `--stop-after` — stop after a stage (e.g. `research`, `query-generation`)
- `--no-interactive` — skip terminal-based review prompts (always use this from Claude Code)

## Step 1: Get the Brand

Ask ONE question: "What brand do you want to analyze?"

If they also mention a website, great. If not, and the brand is well-known, just proceed. Only ask follow-up questions if the brand is obscure or ambiguous.

## Step 2: Check Providers

Run `python3 -m voyage_geo providers` silently. If at least one provider has an API key, proceed. If none, help set up `.env`.

## Step 3: Research the Brand

Do TWO things in parallel:

**A) Run CLI research:**
```
python3 -m voyage_geo research "<brand>" -w "<url>"
```
Note the run ID from the output.

**B) Your own web research (WebSearch + WebFetch):**
- `"<brand>" what is` — what the company does
- `"<brand>" vs competitors alternatives` — competitive landscape
- `"<brand>" reviews` — reputation and USPs

Also WebFetch the brand website if URL provided (backup for 403s).

## Step 4: Review Brand Profile with User

Read `data/runs/<run-id>/brand-profile.json`. Cross-reference with your web research. Fix the profile if the CLI got things wrong, then present it:

> **Brand Profile: [name]**
> **Description:** ...
> **Industry:** ... | **Category:** ...
> **Competitors:** ...
> **Keywords:** ...
> **USPs:** ...
> **Target Audience:** ...

Ask: **"Does this look right? Want to adjust anything before I generate the test queries?"**

If user wants changes, edit `brand-profile.json` to apply them.

## Step 5: Generate Queries

Once the brand profile is confirmed, generate queries only (not the full execution):

```
python3 -m voyage_geo run -b "<name>" --resume <run-id> --stop-after query-generation --no-interactive
```

This generates the simulated search queries and saves them to `data/runs/<run-id>/queries.json`, then stops — it does NOT run them against AI models yet.

## Step 6: Review Queries with User

Read `data/runs/<run-id>/queries.json` and present them in a titled markdown table called **"Simulated Search Queries"**:

### Simulated Search Queries

| # | Strategy | Category | Query |
|---|----------|----------|-------|
| 1 | keyword | best-of | best wagyu restaurant in los angeles |
| 2 | keyword | recommendation | recommend a high end japanese bbq spot |
| 3 | persona | how-to | where should i eat wagyu for a special occasion |
| 4 | intent | general | is yakiniku worth the price |
| ... | ... | ... | ... |

> **20 queries** — 7 keyword · 7 persona · 6 intent

Then ask: **"These are the queries I'll send to all AI models. Look good? Want me to remove or change any before I run?"**

If the user wants changes, edit `queries.json` directly (remove entries, adjust query text, update `total_count`).

This review is important — these queries determine the entire analysis. Bad queries = meaningless results.

## Step 7: Run Full Execution

Once queries are confirmed, run the full pipeline. Since both profile and queries now exist in the run directory, they'll be loaded and the expensive stages (execution → analysis → reporting) will run:

```
python3 -m voyage_geo run -b "<name>" --resume <run-id> -p <configured-providers> -f html,json,csv,markdown --no-interactive
```

## Step 8: Present Results

Read `data/runs/<run-id>/analysis/summary.json` and `analysis/analysis.json`. Present a tight summary:

- Overall AI visibility score
- Mention rate across providers (table: provider | mention rate | sentiment)
- Competitor rank (if applicable)
- Narrative analysis: what themes AI models associate with the brand, and which USPs AI models are missing
- Coverage score: what percentage of USPs are being mentioned
- Top 2-3 recommendations

Tell them the report location. Ask "Want to dig deeper into any finding?"

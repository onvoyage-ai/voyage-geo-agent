You are running a GEO leaderboard — ranking brands by how often AI models actually recommend them. Brands are NOT preset — they're extracted from AI responses.

## CLI Reference

```
python3 -m voyage_geo leaderboard "<category>" -p <providers> -q <n> --stop-after query-generation
python3 -m voyage_geo leaderboard "<category>" --resume <run-id> -p <providers> -f html,json,csv,markdown
python3 -m voyage_geo providers
```

Key flags:
- `category` (positional) — e.g. "top vc", "best CRM tools"
- `--providers / -p` — comma-separated provider names
- `--queries / -q` — number of queries (default: 20)
- `--formats / -f` — report formats (default: html,json)
- `--max-brands` — max brands to extract (default: 50)
- `--stop-after` — stop after stage for review
- `--resume / -r` — resume from existing run ID

## Step 1: Get the Category

Ask: "What category do you want to rank?"

## Step 2: Check Providers

Run `python3 -m voyage_geo providers` silently. Proceed if any have API keys.

## Step 3: Generate Queries (stop for review)

```
python3 -m voyage_geo leaderboard "<category>" -p <providers> -q <n> --stop-after query-generation
```

## Step 4: Review Queries

Read `data/runs/<run-id>/queries.json`. Present as table. Ask: **"Look good?"**

## Step 5: Execute

```
python3 -m voyage_geo leaderboard "<category>" --resume <run-id> -p <providers> -f html,json,csv,markdown
```

## Step 6: Present Results

Read `data/runs/<run-id>/analysis/leaderboard.json`. Present rankings. The brands in the table are what AI actually recommended — no preset list.

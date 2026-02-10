You are doing brand research for a GEO analysis. Be efficient.

## CLI Reference

```
python3 -m voyage_geo research "<brand>" --website "<url>"
```

Flags for `research`:
- `brand` (required, positional) — brand name to research
- `--website / -w` — brand website URL to scrape
- `--output-dir / -o` — output directory (default: ./data/runs)

## For well-known brands

If the user gives you a brand name that's well-known (Bybit, Notion, Stripe, etc.), just run the research immediately — don't ask 7 questions. You already know the industry, competitors, and category.

```
python3 -m voyage_geo research "<brand>" -w "<url>"
```

Read the result from `data/runs/<run-id>/brand-profile.json` and show a quick summary: industry, competitors found, keywords. Ask "Looks good, or want to tweak anything?"

## For obscure/unknown brands

Only if you genuinely don't know the brand, ask:
1. "What does [brand] do?"
2. "Who are the main competitors?"

That's it. Then run the research command and show results.

Don't ask about target audience, USPs, industry category, etc. — the AI research stage handles all of that automatically.

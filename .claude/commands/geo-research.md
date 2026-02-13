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

If the user gives you a brand name that's well-known (Bybit, Notion, Stripe, etc.), run the CLI research AND your own web research in parallel:

**In parallel:**
1. `python3 -m voyage_geo research "<brand>" -w "<url>"` — CLI scrapes site + LLM builds initial profile
2. WebSearch for `"<brand>" what is` and `"<brand>" vs competitors alternatives` — gather independent context
3. WebFetch the brand website if URL provided — backup in case CLI scraper hits a 403

Read the result from `data/runs/<run-id>/brand-profile.json`. Cross-reference with your web search findings. If the CLI profile is missing competitors, has wrong industry, or lacks key USPs — edit `brand-profile.json` to fix it.

Show the final profile: industry, category, competitors, keywords, USPs, target audience. Ask "Looks good, or want to tweak anything?"

## For obscure/unknown brands

Only if you genuinely don't know the brand, ask:
1. "What does [brand] do?"
2. "Who are the main competitors?"

Then run the CLI research AND your own web research in parallel (same as above). Your web search results are especially important for obscure brands since the LLM may not know them well.

Don't ask about target audience, USPs, industry category, etc. — between the CLI research stage and your web searches, all of that gets figured out automatically.

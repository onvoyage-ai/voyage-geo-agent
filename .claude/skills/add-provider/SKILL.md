---
name: add-provider
description: Add a new AI provider — Claude Code walks you through implementing and registering a new AI model provider
user_invocable: true
---

# Add Provider

You are a developer helping the user add a new AI provider to Voyage GEO.

## CLI Reference

```
python3 -m voyage_geo providers            # list configured providers
python3 -m voyage_geo providers --test     # health check providers
python3 -m mypy src/voyage_geo/ --ignore-missing-imports  # type check
python3 -m pytest tests/ -v               # run tests
```

## Step 1: Understand What They Want

Ask: "Which AI provider do you want to add?" Get:
- Provider name (e.g., "Mistral", "Cohere", "Groq")
- Which SDK or API it uses
- Whether it's OpenAI-compatible (many are — just need a custom base_url)

## Step 2: Choose Approach

If it's OpenAI-compatible (like Groq, Together, etc.):
- Show them the Perplexity provider as a template — it uses the OpenAI SDK with a custom `base_url`
- This is the fastest path

If it needs a custom SDK:
- Show them the Anthropic or Google provider as templates
- Help them install the SDK: `pip install <sdk-package>`

## Step 3: Implement

Create the provider file at `src/voyage_geo/providers/<name>_provider.py` by:
1. Reading `src/voyage_geo/providers/base.py` for the BaseProvider abstract class
2. Reading an existing provider as reference
3. Writing the new provider, implementing the `query()` method
4. Registering it in `src/voyage_geo/providers/registry.py`
5. Adding defaults in `src/voyage_geo/config/defaults.py`
6. Adding env variable loading in `src/voyage_geo/config/loader.py`

## Step 4: Verify

1. Run `python3 -m mypy src/voyage_geo/ --ignore-missing-imports` — fix any errors
2. Run `python3 -m pytest tests/ -v`
3. Add the API key to `.env`
4. Test: `python3 -m voyage_geo providers --test`

Show the user the test results and confirm it works.

## Allowed Tools

- Read
- Write
- Edit
- Bash
- Glob
- Grep

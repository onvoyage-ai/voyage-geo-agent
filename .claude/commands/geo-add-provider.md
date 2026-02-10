Help the user add a new AI provider to Voyage GEO.

## CLI Reference

```
python3 -m voyage_geo providers            # list configured providers
python3 -m voyage_geo providers --test     # health check providers
python3 -m mypy src/voyage_geo/ --ignore-missing-imports  # type check
python3 -m pytest tests/ -v               # run tests
```

## Step 1: Understand

Ask: "Which AI provider do you want to add?" Get the provider name, SDK, and whether it's OpenAI-compatible (just needs a custom base_url).

## Step 2: Choose Approach

If OpenAI-compatible (Groq, Together, etc.): use `src/voyage_geo/providers/perplexity_provider.py` as template — just change the base_url.
If custom SDK: use Anthropic or Google provider as template. Install SDK with `pip install <package>` and add it to `pyproject.toml` dependencies.

## Step 3: Implement

1. Read `src/voyage_geo/providers/base.py` for the BaseProvider abstract class
2. Read an existing provider as reference
3. Create `src/voyage_geo/providers/<name>_provider.py`
4. Register in `src/voyage_geo/providers/registry.py`
5. Add defaults in `src/voyage_geo/config/defaults.py`
6. Add env var loading in `src/voyage_geo/config/loader.py`

## Step 4: Verify

Run `python3 -m mypy src/voyage_geo/ --ignore-missing-imports`, add API key to `.env`, test with `python3 -m voyage_geo providers --test`.

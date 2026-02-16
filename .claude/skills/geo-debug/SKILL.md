---
name: geo-debug
description: Debug a failed GEO run — Claude Code diagnoses issues, checks API keys, and helps fix problems
user_invocable: true
---

# Debug Run

You are a support engineer. Help the user figure out why their GEO analysis failed or produced unexpected results.

## CLI Reference

```
python3 -m voyage_geo providers            # list configured providers
python3 -m voyage_geo providers --test     # health check providers
python3 -m voyage_geo runs                 # list past runs
```

## Step 1: Identify the Problem

Ask: "What went wrong? Did a run fail, or are the results not what you expected?"

Check recent runs:
```bash
python3 -m voyage_geo runs
```

Read the metadata of the most recent run:
- `data/runs/<run-id>/metadata.json` — check `status` and `errors`

## Step 2: Diagnose

Based on the error:

**No providers configured:**
- Check `.env` for API keys
- Run `python3 -m voyage_geo providers --test`
- Help them add keys

**Rate limit errors (429):**
- Read results to see which provider hit limits
- Suggest: reduce `--queries` count, or reduce concurrency with `-c`
- Show them how to set rate limits in config

**Timeout errors:**
- Check latency values in results
- Suggest increasing timeout in config

**Provider-specific errors:**
- Read `data/runs/<run-id>/results/by-provider/<provider>.json`
- Check for auth errors (bad API key), model errors (invalid model name)
- Help fix the specific issue

**Empty or unexpected results:**
- Read the brand profile — is it accurate?
- Read the queries — are they relevant?
- Read sample responses — are models actually responding?

## Step 3: Fix & Re-run

After identifying the issue:
1. Help the user fix the root cause
2. Offer to re-run: "Want me to try again with the fix applied?"
3. If it was a partial failure, offer to re-run just the failed stage

## Allowed Tools

- Read
- Glob
- Grep
- Bash
- Write
- Edit

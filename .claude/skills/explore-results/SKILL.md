---
name: explore-results
description: Interactively explore GEO results — Claude Code walks you through findings, answers questions, and helps you understand your AI visibility
user_invocable: true
---

# Explore Results

You are a data analyst helping the user understand their GEO analysis results. Be conversational and insightful — don't just dump numbers.

## CLI Reference

```
python3 -m voyage_geo runs   # list past runs
```

## Step 1: Find the Run

Check for available runs:
```bash
python3 -m voyage_geo runs
```

If multiple runs exist, ask which one to explore. If only one, use it. If none, tell the user to run an analysis first.

## Step 2: Load & Summarize

Read these files:
- `data/runs/<run-id>/analysis/summary.json` — executive summary
- `data/runs/<run-id>/analysis/analysis.json` — full analysis
- `data/runs/<run-id>/brand-profile.json` — brand info

Present a conversational overview:
- Lead with the headline finding (e.g., "Your brand has a 45% AI visibility score")
- Give 2-3 key takeaways in plain language
- Compare across providers ("Claude mentions you most, Gemini least")
- Mention sentiment ("AI models describe you positively, especially around [attribute]")
- Summarize narrative analysis: what themes AI models associate with the brand, and which USPs they're missing (from `analysis.narrative`)

## Step 3: Interactive Q&A

After the overview, ask: "What would you like to dig into?"

Offer suggestions:
- "How do I compare to competitors?"
- "Which AI model likes my brand the most?"
- "What words do AI models use to describe me?"
- "What narratives are AI models telling about my brand?" (uses `analysis.narrative.brand_themes`)
- "Which of my USPs are AI models missing?" (uses `analysis.narrative.gaps`)
- "What narratives do competitors own that I don't?" (uses `analysis.narrative.competitor_themes`)
- "Show me the raw responses where my brand was mentioned"
- "What should I do to improve my AI visibility?"

For each question, read the relevant data and explain it conversationally.

## Step 4: Deep Dives

If the user wants to see specific responses:
- Read `data/runs/<run-id>/results/results.json`
- Filter to responses that mention their brand
- Show relevant excerpts with context

If they want competitor details:
- Show the competitor comparison table
- Explain relative positioning

If they want recommendations:
- Read the summary recommendations
- Add your own strategic advice based on the data

## Step 5: Next Actions

Based on what you found, suggest:
- "Want me to re-run with more queries for deeper data?"
- "Want to generate a report to share with your team?"
- "Want to track changes over time with another run?"

## Allowed Tools

- Read
- Glob
- Grep
- Bash

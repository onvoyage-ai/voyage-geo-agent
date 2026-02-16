---
name: geo-report
description: Generate a shareable GEO report — Claude Code creates HTML/PDF/CSV reports and explains the key takeaways
user_invocable: true
---

# Generate Report

You help the user create reports from their GEO analysis data to share with their team.

## CLI Reference

```
python3 -m voyage_geo report --run-id <id> --formats html,json,csv,markdown
python3 -m voyage_geo runs   # list past runs
```

Flags for `report`:
- `--run-id / -r` (required) — run ID to generate report from
- `--formats / -f` — report formats: html,json,csv,markdown (default: html,json)
- `--output-dir / -o` — output directory (default: ./data/runs)

## Step 1: Find the Run

Check for available runs:
```bash
python3 -m voyage_geo runs
```

If multiple runs exist, ask which one. Show the brand name and date for each by reading their metadata.

## Step 2: Ask About Format

Ask the user: "What format do you need?"
- **HTML** — Interactive report you can open in a browser (recommended for sharing)
- **Markdown** — Good for pasting into docs or Notion
- **CSV** — Good for spreadsheets and further analysis
- **JSON** — Raw data for developers
- **All of the above**

## Step 3: Generate

Run the report command:
```bash
python3 -m voyage_geo report -r <id> -f <formats>
```

## Step 4: Present

After generation:
1. Tell them exactly where the files are
2. Read the summary and present the headline findings
3. If HTML was generated, tell them: "Open `data/runs/<id>/reports/report.html` in your browser for the full interactive report"
4. If CSV was generated, list the CSV files available for import

Ask: "Want me to walk you through the findings, or is the report enough?"

## Allowed Tools

- Bash
- Read
- Glob
- Grep

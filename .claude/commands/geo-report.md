Help the user create shareable reports from their GEO analysis data.

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

Check `data/runs/` for available runs. If multiple, show brand name and date for each (read metadata.json) and ask which one.

## Step 2: Ask Format

Ask: "What format do you need?"
- **HTML** — Interactive report for browser (recommended)
- **Markdown** — Good for docs/Notion
- **CSV** — Good for spreadsheets
- **JSON** — Raw data
- **All of the above**

## Step 3: Generate

Run `python3 -m voyage_geo report -r <id> -f <formats>`

## Step 4: Present

Tell them where the files are. If HTML, say to open `reports/report.html` in a browser. Read the summary and present headline findings. Ask if they want a walkthrough.

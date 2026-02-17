"""Tests for app-mode job helpers."""

from __future__ import annotations

import json

from voyage_geo.app.jobs import RUN_ID_RE, get_run_details, list_runs


def test_run_id_regex_extracts_analysis_and_leaderboard() -> None:
    line = "Run: run-20260217-060702-3eb67e and lb-20260214-061931-fa1f71"
    matches = RUN_ID_RE.findall(line)
    assert "run-20260217-060702-3eb67e" in matches
    assert "lb-20260214-061931-fa1f71" in matches


def test_list_runs_and_details(tmp_path) -> None:
    runs = tmp_path / "runs"
    run = runs / "run-20260217-060702-3eb67e"
    (run / "analysis").mkdir(parents=True)
    (run / "reports").mkdir(parents=True)
    (run / "metadata.json").write_text(json.dumps({
        "type": "analysis",
        "status": "completed",
        "brand": "Acme",
        "started_at": "2026-02-17T06:07:02+00:00",
        "as_of_date": "2026-02-15",
    }))
    (run / "analysis" / "summary.json").write_text(json.dumps({"headline": "ok"}))
    (run / "analysis" / "snapshot.json").write_text(json.dumps({"overall_score": 42}))

    rows = list_runs(str(runs), limit=10)
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run-20260217-060702-3eb67e"
    assert rows[0]["brand"] == "Acme"

    details = get_run_details(str(runs), "run-20260217-060702-3eb67e")
    assert details["metadata"]["brand"] == "Acme"
    assert details["summary"]["headline"] == "ok"
    assert details["snapshot"]["overall_score"] == 42

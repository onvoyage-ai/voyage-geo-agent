"""Trend indexing helpers for time-series GEO analysis."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def collect_trend_records(output_dir: str, brand: str | None = None) -> list[dict[str, Any]]:
    runs_dir = Path(output_dir)
    if not runs_dir.exists():
        return []

    records: list[dict[str, Any]] = []
    for run_dir in sorted(runs_dir.iterdir(), reverse=True):
        if not run_dir.is_dir() or not run_dir.name.startswith("run-"):
            continue

        meta_path = run_dir / "metadata.json"
        if not meta_path.exists():
            continue

        try:
            metadata = json.loads(meta_path.read_text())
        except Exception:
            continue

        if metadata.get("type", "analysis") != "analysis":
            continue

        snapshot = _load_snapshot(run_dir)
        if not snapshot:
            continue

        snap_brand = str(snapshot.get("brand", "")).strip()
        if brand and snap_brand.lower() != brand.lower():
            continue

        as_of_date = metadata.get("as_of_date") or _to_date(snapshot.get("analyzed_at")) or _to_date(metadata.get("completed_at")) or _to_date(metadata.get("started_at"))

        record = {
            "run_id": run_dir.name,
            "as_of_date": as_of_date,
            "brand": snap_brand,
            "status": metadata.get("status", ""),
            "overall_score": snapshot.get("overall_score", 0.0),
            "mention_rate": snapshot.get("mention_rate", 0.0),
            "mindshare": snapshot.get("mindshare", 0.0),
            "sentiment_score": snapshot.get("sentiment_score", 0.0),
            "mindshare_rank": snapshot.get("mindshare_rank", 0),
            "total_brands_detected": snapshot.get("total_brands_detected", 0),
            "competitor_relative": snapshot.get("competitor_relative", {}),
        }
        records.append(record)

    records.sort(key=lambda r: (str(r.get("as_of_date", "")), str(r.get("run_id", ""))))
    return records


def build_competitor_series(records: list[dict[str, Any]], competitors: list[str] | None = None) -> dict[str, list[dict[str, Any]]]:
    names = [c.lower() for c in competitors] if competitors else None
    series: dict[str, list[dict[str, Any]]] = {}

    for record in records:
        relative = record.get("competitor_relative", {})
        for comp in relative.get("top_competitors", []) or []:
            name = str(comp.get("name", "")).strip()
            if not name:
                continue
            if names and name.lower() not in names:
                continue
            series.setdefault(name, []).append({
                "as_of_date": record.get("as_of_date"),
                "run_id": record.get("run_id"),
                "mindshare": comp.get("mindshare", 0.0),
                "mention_rate": comp.get("mention_rate", 0.0),
                "sentiment": comp.get("sentiment", 0.0),
            })

    for values in series.values():
        values.sort(key=lambda r: (str(r.get("as_of_date", "")), str(r.get("run_id", ""))))

    return series


def write_trend_index(records: list[dict[str, Any]], output_path: str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2))
    return path


def _load_snapshot(run_dir: Path) -> dict[str, Any] | None:
    snapshot_path = run_dir / "analysis" / "snapshot.json"
    if snapshot_path.exists():
        try:
            return json.loads(snapshot_path.read_text())
        except Exception:
            return None
    return None


def _to_date(value: Any) -> str:
    if not value:
        return ""
    text = str(value)
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except Exception:
        return text[:10]

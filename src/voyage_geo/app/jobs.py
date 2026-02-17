"""Background job execution and run artifact helpers for app mode."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RUN_ID_RE = re.compile(r"\b(run-\d{8}-\d{6}-[a-f0-9]{6}|lb-\d{8}-\d{6}-[a-f0-9]{6})\b")


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class JobRecord:
    job_id: str
    kind: str
    command: list[str]
    status: str = "queued"  # queued|running|completed|failed|cancelled
    created_at: str = field(default_factory=now_iso)
    started_at: str | None = None
    completed_at: str | None = None
    pid: int | None = None
    return_code: int | None = None
    run_id: str | None = None
    logs: list[str] = field(default_factory=list)


class JobStore:
    """In-memory job registry that streams subprocess logs."""

    def __init__(self, output_dir: str = "./data/runs", cwd: str | None = None) -> None:
        self.output_dir = output_dir
        self.cwd = cwd or str(Path.cwd())
        self._lock = threading.Lock()
        self._jobs: dict[str, JobRecord] = {}
        self._procs: dict[str, subprocess.Popen[str]] = {}

    def create_job(self, kind: str, args: list[str]) -> JobRecord:
        job_id = uuid.uuid4().hex[:12]
        command = [sys.executable, "-m", "voyage_geo", *args]
        job = JobRecord(job_id=job_id, kind=kind, command=command)
        with self._lock:
            self._jobs[job_id] = job
        self._start(job_id)
        return self.get_job(job_id)

    def _start(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
            job.started_at = now_iso()

        proc = subprocess.Popen(
            job.command,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        with self._lock:
            job.pid = proc.pid
            self._procs[job_id] = proc

        thread = threading.Thread(target=self._stream_job, args=(job_id, proc), daemon=True)
        thread.start()

    def _stream_job(self, job_id: str, proc: subprocess.Popen[str]) -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip("\n")
            match = RUN_ID_RE.search(line)
            with self._lock:
                job = self._jobs[job_id]
                job.logs.append(line)
                # Keep recent logs bounded.
                if len(job.logs) > 2000:
                    job.logs = job.logs[-2000:]
                if match and not job.run_id:
                    job.run_id = match.group(1)

        rc = proc.wait()
        with self._lock:
            job = self._jobs[job_id]
            job.return_code = rc
            if job.status != "cancelled":
                job.status = "completed" if rc == 0 else "failed"
            job.completed_at = now_iso()
            self._procs.pop(job_id, None)

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            proc = self._procs.get(job_id)
            job = self._jobs.get(job_id)
            if not proc or not job:
                return False
            proc.terminate()
            job.status = "cancelled"
            job.completed_at = now_iso()
            return True

    def get_job(self, job_id: str) -> JobRecord:
        with self._lock:
            job = self._jobs[job_id]
            return JobRecord(**job.__dict__)

    def list_jobs(self, limit: int = 100) -> list[JobRecord]:
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [JobRecord(**j.__dict__) for j in jobs[:limit]]

    def tail_logs(self, job_id: str, tail: int = 200) -> list[str]:
        with self._lock:
            logs = self._jobs[job_id].logs
            return logs[-tail:]


def list_runs(output_dir: str, limit: int = 100) -> list[dict[str, Any]]:
    runs_dir = Path(output_dir)
    if not runs_dir.exists():
        return []

    items: list[dict[str, Any]] = []
    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir():
            continue
        if not (run_dir.name.startswith("run-") or run_dir.name.startswith("lb-")):
            continue

        meta_path = run_dir / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            continue

        items.append({
            "run_id": run_dir.name,
            "type": meta.get("type", "analysis"),
            "status": meta.get("status", ""),
            "brand": meta.get("brand", ""),
            "category": meta.get("category", ""),
            "started_at": meta.get("started_at", ""),
            "completed_at": meta.get("completed_at", ""),
            "as_of_date": meta.get("as_of_date", ""),
        })

    items.sort(key=lambda r: (str(r.get("started_at", "")), str(r.get("run_id", ""))), reverse=True)
    return items[:limit]


def get_run_details(output_dir: str, run_id: str) -> dict[str, Any]:
    run_dir = Path(output_dir) / run_id
    if not run_dir.exists():
        raise FileNotFoundError(run_id)

    def _load(rel_path: str) -> Any:
        path = run_dir / rel_path
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception:
            return None

    meta = _load("metadata.json") or {}
    summary = _load("analysis/summary.json")
    snapshot = _load("analysis/snapshot.json")
    leaderboard = _load("analysis/leaderboard.json")
    return {
        "run_id": run_id,
        "metadata": meta,
        "summary": summary,
        "snapshot": snapshot,
        "leaderboard": leaderboard,
        "paths": {
            "report_html": str(run_dir / "reports" / ("leaderboard.html" if run_id.startswith("lb-") else "report.html")),
            "report_json": str(run_dir / "reports" / ("leaderboard.json" if run_id.startswith("lb-") else "report.json")),
            "analysis_json": str(run_dir / "analysis" / ("leaderboard.json" if run_id.startswith("lb-") else "analysis.json")),
        },
    }


"""File-based storage for run data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class FileSystemStorage:
    def __init__(self, base_dir: str = "./data/runs") -> None:
        self.base_dir = Path(base_dir)

    async def create_run_dir(self, run_id: str) -> Path:
        run_dir = self.base_dir / run_id
        for sub in [
            "",
            "results",
            "results/by-provider",
            "analysis",
            "reports",
            "reports/charts",
        ]:
            (run_dir / sub).mkdir(parents=True, exist_ok=True)
        return run_dir

    def run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    async def save_json(self, run_id: str, filename: str, data: Any) -> Path:
        path = self.base_dir / run_id / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Pydantic models to dicts
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.debug("storage.saved", path=str(path))
        return path

    async def load_json(self, run_id: str, filename: str) -> Any:
        path = self.base_dir / run_id / filename
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    async def save_metadata(self, run_id: str, metadata: dict) -> None:
        await self.save_json(run_id, "metadata.json", metadata)

    async def save_text(self, run_id: str, filename: str, text: str) -> Path:
        path = self.base_dir / run_id / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        return path

    def list_runs(self) -> list[str]:
        if not self.base_dir.exists():
            return []
        return sorted(
            [d.name for d in self.base_dir.iterdir() if d.is_dir() and (d.name.startswith("run-") or d.name.startswith("lb-"))],
            reverse=True,
        )

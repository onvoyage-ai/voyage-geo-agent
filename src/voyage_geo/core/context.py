"""RunContext — state carrier through the pipeline."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from voyage_geo.config.schema import VoyageGeoConfig
from voyage_geo.types.analysis import AnalysisResult
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import QuerySet
from voyage_geo.types.result import ExecutionRun


@dataclass
class RunContext:
    run_id: str
    config: VoyageGeoConfig
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    started_at: str = ""
    completed_at: str | None = None
    brand_profile: BrandProfile | None = None
    query_set: QuerySet | None = None
    execution_run: ExecutionRun | None = None
    analysis_result: AnalysisResult | None = None
    errors: list[str] = field(default_factory=list)


def create_run_context(config: VoyageGeoConfig) -> RunContext:
    now = datetime.now(UTC).isoformat()
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    short = uuid.uuid4().hex[:6]
    run_id = f"run-{ts}-{short}"
    return RunContext(run_id=run_id, config=config, started_at=now)

"""Pipeline — sequential stage runner."""

from __future__ import annotations

import abc

import structlog

from voyage_geo.core.context import RunContext

logger = structlog.get_logger()


class PipelineStage(abc.ABC):
    name: str
    description: str

    @abc.abstractmethod
    async def execute(self, ctx: RunContext) -> RunContext: ...


class Pipeline:
    def __init__(self) -> None:
        self._stages: list[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> Pipeline:
        self._stages.append(stage)
        return self

    async def run(self, ctx: RunContext) -> RunContext:
        current = ctx
        current.status = "running"

        for stage in self._stages:
            logger.info("pipeline.stage_started", stage=stage.name)
            try:
                current = await stage.execute(current)
                logger.info("pipeline.stage_completed", stage=stage.name)
            except Exception as exc:
                current.status = "failed"
                current.errors.append(f"[{stage.name}] {exc}")
                logger.error("pipeline.stage_failed", stage=stage.name, error=str(exc))
                raise

        current.status = "completed"
        return current

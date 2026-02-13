"""Pipeline — sequential stage runner."""

from __future__ import annotations

import abc
from collections.abc import Awaitable, Callable

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
        self._hooks: dict[str, Callable[[RunContext], Awaitable[RunContext]]] = {}

    def add_stage(self, stage: PipelineStage) -> Pipeline:
        self._stages.append(stage)
        return self

    def add_hook(self, after_stage: str, callback: Callable[[RunContext], Awaitable[RunContext]]) -> None:
        """Register a callback to run after a named stage completes."""
        self._hooks[after_stage] = callback

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

            if stage.name in self._hooks:
                current = await self._hooks[stage.name](current)

        current.status = "completed"
        return current

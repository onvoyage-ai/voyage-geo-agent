"""Stage 3: Execution — runs queries against all configured AI providers."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import structlog

from voyage_geo.core.context import RunContext
from voyage_geo.core.pipeline import PipelineStage
from voyage_geo.providers.registry import ProviderRegistry
from voyage_geo.storage.filesystem import FileSystemStorage
from voyage_geo.types.result import ExecutionRun, QueryResult, TokenUsage
from voyage_geo.utils.progress import console, stage_header

logger = structlog.get_logger()


class ExecutionStage(PipelineStage):
    name = "execution"
    description = "Run queries against AI providers"

    def __init__(self, provider_registry: ProviderRegistry, storage: FileSystemStorage) -> None:
        self.provider_registry = provider_registry
        self.storage = storage

    async def execute(self, ctx: RunContext) -> RunContext:
        stage_header(self.name, self.description)

        if not ctx.query_set:
            raise RuntimeError("Query set is required for execution")

        queries = ctx.query_set.queries
        providers = self.provider_registry.get_enabled()
        config = ctx.config.execution
        concurrency = config.concurrency
        iterations = config.iterations

        total_tasks = len(queries) * len(providers) * iterations
        console.print(f"  [bold]{total_tasks}[/bold] tasks = {len(queries)} queries x {len(providers)} providers x {iterations} iterations")
        console.print(f"  Concurrency: {concurrency} | Timeout: {config.timeout_ms}ms")

        execution_run = ExecutionRun(
            run_id=ctx.run_id,
            brand=ctx.query_set.brand,
            providers=[p.name for p in providers],
            total_queries=total_tasks,
            started_at=datetime.now(UTC).isoformat(),
        )

        semaphore = asyncio.Semaphore(concurrency)
        completed = 0
        failed = 0

        async def run_task(query, provider, iteration):
            nonlocal completed, failed
            async with semaphore:
                start = datetime.now(UTC)
                try:
                    import time
                    t0 = time.perf_counter()
                    resp = await asyncio.wait_for(
                        provider.query(query.text),
                        timeout=config.timeout_ms / 1000,
                    )
                    latency = int((time.perf_counter() - t0) * 1000)

                    usage = None
                    if resp.token_usage:
                        usage = TokenUsage(**resp.token_usage)

                    result = QueryResult(
                        query_id=query.id,
                        query_text=query.text,
                        provider=provider.name,
                        model=resp.model,
                        response=resp.text,
                        latency_ms=latency,
                        token_usage=usage,
                        iteration=iteration,
                        timestamp=start.isoformat(),
                    )
                    completed += 1
                except Exception as e:
                    result = QueryResult(
                        query_id=query.id,
                        query_text=query.text,
                        provider=provider.name,
                        model="unknown",
                        response="",
                        latency_ms=0,
                        iteration=iteration,
                        timestamp=start.isoformat(),
                        error=str(e),
                    )
                    failed += 1
                    logger.warning("execution.task_failed", provider=provider.name, query_id=query.id, error=str(e))

                execution_run.results.append(result)
                done = completed + failed
                if done % 5 == 0 or done == total_tasks:
                    console.print(f"  [dim]Progress: {done}/{total_tasks} ({completed} ok, {failed} err)[/dim]")
                return result

        tasks = []
        for iteration in range(1, iterations + 1):
            for query in queries:
                for provider in providers:
                    tasks.append(run_task(query, provider, iteration))

        await asyncio.gather(*tasks)

        execution_run.completed_queries = completed
        execution_run.failed_queries = failed
        execution_run.completed_at = datetime.now(UTC).isoformat()
        execution_run.status = "completed" if failed == 0 else "partial" if completed > 0 else "failed"

        await self.storage.save_json(ctx.run_id, "results/results.json", execution_run)

        # Save per-provider splits
        by_provider: dict[str, list] = {}
        for r in execution_run.results:
            by_provider.setdefault(r.provider, []).append(r.model_dump())
        for prov, results in by_provider.items():
            await self.storage.save_json(ctx.run_id, f"results/by-provider/{prov}.json", results)

        console.print(f"  [green]Execution complete:[/green] {completed} succeeded, {failed} failed")

        ctx.execution_run = execution_run
        return ctx

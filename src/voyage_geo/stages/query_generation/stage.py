"""Stage 2: Query generation — uses AI to generate contextual search queries."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from voyage_geo.core.context import RunContext
from voyage_geo.core.pipeline import PipelineStage
from voyage_geo.providers.base import BaseProvider
from voyage_geo.providers.registry import ProviderRegistry
from voyage_geo.stages.query_generation.strategies import competitor, intent, keyword, persona
from voyage_geo.storage.filesystem import FileSystemStorage
from voyage_geo.types.query import GeneratedQuery, QuerySet
from voyage_geo.utils.progress import console, print_query_table, stage_header

logger = structlog.get_logger()

STRATEGY_MAP = {
    "keyword": keyword.generate,
    "persona": persona.generate,
    "competitor": competitor.generate,
    "intent": intent.generate,
}


class QueryGenerationStage(PipelineStage):
    name = "query-generation"
    description = "Generate search queries with AI"

    def __init__(self, provider_registry: ProviderRegistry, storage: FileSystemStorage) -> None:
        self.provider_registry = provider_registry
        self.storage = storage

    async def execute(self, ctx: RunContext) -> RunContext:
        stage_header(self.name, self.description)

        if not ctx.brand_profile:
            raise RuntimeError("Brand profile is required for query generation")

        profile = ctx.brand_profile
        query_config = ctx.config.queries
        strategies_enabled = query_config.strategies
        total_count = query_config.count
        per_strategy = -(-total_count // len(strategies_enabled))  # ceil div

        generator = self._pick_provider()
        console.print(f"  Generating queries via [bold]{generator.display_name}[/bold]...")

        all_queries: list[GeneratedQuery] = []

        for strategy_name in strategies_enabled:
            fn = STRATEGY_MAP.get(strategy_name)
            if not fn:
                logger.warning("unknown_strategy", strategy=strategy_name)
                continue

            console.print(f"  [dim]→ {strategy_name} strategy ({per_strategy} queries)...[/dim]")
            queries = await fn(profile, per_strategy, generator)
            all_queries.extend(queries)

        trimmed = all_queries[:total_count]

        query_set = QuerySet(
            brand=profile.name,
            queries=trimmed,
            generated_at=datetime.now(UTC).isoformat(),
            total_count=len(trimmed),
        )

        await self.storage.save_json(ctx.run_id, "queries.json", query_set)
        console.print(f"  [green]Generated {len(trimmed)} AI-crafted queries across {len(strategies_enabled)} strategies[/green]")
        console.print()
        print_query_table(trimmed)

        ctx.query_set = query_set
        return ctx

    def _pick_provider(self) -> BaseProvider:
        enabled = self.provider_registry.get_enabled()
        if not enabled:
            raise RuntimeError("No providers available for query generation")
        preferred = ["openai", "anthropic", "google", "perplexity"]
        for name in preferred:
            match = next((p for p in enabled if p.name == name), None)
            if match:
                return match
        return enabled[0]

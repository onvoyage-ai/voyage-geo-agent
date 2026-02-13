"""Stage 2: Query generation — uses AI to generate contextual search queries."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from voyage_geo.core.context import RunContext
from voyage_geo.core.pipeline import PipelineStage
from voyage_geo.providers.base import BaseProvider
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

# Industries/categories where "[competitor] alternatives" is a natural query pattern
_COMPETITOR_STRATEGY_KEYWORDS = {
    "saas", "software", "platform", "tool", "app", "service",
    "fintech", "edtech", "martech", "devtools", "cloud",
    "crm", "erp", "cms", "analytics", "automation",
}


class QueryGenerationStage(PipelineStage):
    name = "query-generation"
    description = "Generate search queries with AI"

    def __init__(self, processing_provider: BaseProvider, storage: FileSystemStorage) -> None:
        self.processing_provider = processing_provider
        self.storage = storage

    async def execute(self, ctx: RunContext) -> RunContext:
        stage_header(self.name, self.description)

        if ctx.query_set:
            console.print(f"  [dim]Using existing query set ({len(ctx.query_set.queries)} queries)[/dim]")
            return ctx

        if not ctx.brand_profile:
            raise RuntimeError("Brand profile is required for query generation")

        profile = ctx.brand_profile
        query_config = ctx.config.queries
        strategies_enabled = list(query_config.strategies)
        total_count = query_config.count

        # Auto-enable competitor strategy for SaaS/software/platform categories
        if "competitor" not in strategies_enabled and profile.competitors:
            category_lower = (profile.category + " " + profile.industry).lower()
            if any(kw in category_lower for kw in _COMPETITOR_STRATEGY_KEYWORDS):
                strategies_enabled.append("competitor")
                console.print(f"  [dim]Auto-enabled competitor strategy (SaaS/software category)[/dim]")

        per_strategy = -(-total_count // len(strategies_enabled))  # ceil div

        console.print(f"  Generating queries via [bold]{self.processing_provider.display_name}[/bold]...")
        console.print(f"  [dim]Strategies: {', '.join(strategies_enabled)}[/dim]")

        all_queries: list[GeneratedQuery] = []

        for strategy_name in strategies_enabled:
            fn = STRATEGY_MAP.get(strategy_name)
            if not fn:
                logger.warning("unknown_strategy", strategy=strategy_name)
                continue

            console.print(f"  [dim]→ {strategy_name} strategy ({per_strategy} queries)...[/dim]")
            queries = await fn(profile, per_strategy, self.processing_provider)
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


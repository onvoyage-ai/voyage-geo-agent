"""VoyageGeoEngine — top-level orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from voyage_geo.config.schema import ProviderConfig, VoyageGeoConfig
from voyage_geo.core.context import RunContext, create_run_context
from voyage_geo.core.pipeline import Pipeline
from voyage_geo.providers.registry import ProviderRegistry, create_provider
from voyage_geo.stages.analysis.stage import AnalysisStage
from voyage_geo.stages.execution.stage import ExecutionStage
from voyage_geo.stages.query_generation.stage import QueryGenerationStage
from voyage_geo.stages.reporting.stage import ReportingStage
from voyage_geo.stages.research.stage import ResearchStage
from voyage_geo.storage.filesystem import FileSystemStorage

logger = structlog.get_logger()


class VoyageGeoEngine:
    def __init__(
        self,
        config: VoyageGeoConfig,
        *,
        interactive: bool = True,
        resume_run_id: str | None = None,
        stop_after: str | None = None,
    ) -> None:
        self.config = config
        self.interactive = interactive
        self.resume_run_id = resume_run_id
        self.stop_after = stop_after
        self.storage = FileSystemStorage(config.output_dir)
        self.provider_registry = ProviderRegistry()
        self.pipeline = Pipeline()

        self._register_providers()
        self._processing_provider = self._create_processing_provider()
        self._build_pipeline()
        self._register_hooks()

    def _register_providers(self) -> None:
        for name, pconfig in self.config.providers.items():
            if pconfig.enabled and pconfig.api_key:
                self.provider_registry.register(name, pconfig)

    def _create_processing_provider(self):
        """Create a dedicated provider for non-execution LLM calls (research, query gen, analysis)."""
        proc = self.config.processing
        if not proc.api_key:
            logger.warning("processing.no_api_key", provider=proc.provider)
            raise RuntimeError(
                f"No API key found for processing provider '{proc.provider}'. "
                f"Set the appropriate env var (e.g. ANTHROPIC_API_KEY) or configure processing.api_key."
            )
        provider_config = ProviderConfig(
            name=proc.provider,
            model=proc.model,
            api_key=proc.api_key,
            max_tokens=proc.max_tokens,
        )
        provider = create_provider(proc.provider, provider_config)
        logger.info("processing.provider_created", provider=proc.provider, model=proc.model)
        return provider

    def _build_pipeline(self) -> None:
        self.pipeline.add_stage(ResearchStage(self._processing_provider, self.storage))
        self.pipeline.add_stage(QueryGenerationStage(self._processing_provider, self.storage))
        self.pipeline.add_stage(ExecutionStage(self.provider_registry, self.storage))
        self.pipeline.add_stage(AnalysisStage(self.storage, self._processing_provider))
        self.pipeline.add_stage(ReportingStage(self.storage))

    def _register_hooks(self) -> None:
        if self.interactive:
            from voyage_geo.utils.interactive import review_brand_profile, review_queries

            self.pipeline.add_hook("research", review_brand_profile)
            self.pipeline.add_hook("query-generation", review_queries)

    async def _load_resume_context(self, ctx: RunContext) -> RunContext:
        """Load existing data from a previous run into the context."""
        run_id = self.resume_run_id
        assert run_id is not None

        from voyage_geo.types.brand import BrandProfile
        from voyage_geo.types.query import QuerySet

        profile_data = await self.storage.load_json(run_id, "brand-profile.json")
        if profile_data:
            ctx.brand_profile = BrandProfile(**profile_data)
            logger.info("engine.resume.loaded_profile", run_id=run_id)
        else:
            logger.warning("engine.resume.no_profile", run_id=run_id)

        query_data = await self.storage.load_json(run_id, "queries.json")
        if query_data:
            ctx.query_set = QuerySet(**query_data)
            logger.info("engine.resume.loaded_queries", run_id=run_id, count=len(ctx.query_set.queries))

        return ctx

    async def run(self) -> RunContext:
        if self.resume_run_id:
            # Reuse the existing run directory
            ctx = create_run_context(self.config)
            ctx.run_id = self.resume_run_id
            ctx = await self._load_resume_context(ctx)
            logger.info("engine.resume", run_id=ctx.run_id, brand=self.config.brand)
        else:
            ctx = create_run_context(self.config)
            logger.info("engine.start", run_id=ctx.run_id, brand=self.config.brand)

        await self.storage.create_run_dir(ctx.run_id)
        await self.storage.save_metadata(ctx.run_id, {
            "run_id": ctx.run_id,
            "started_at": ctx.started_at,
            "status": "running",
        })

        try:
            result = await self.pipeline.run(ctx, stop_after=self.stop_after)
            result.completed_at = datetime.now(UTC).isoformat()

            await self.storage.save_metadata(ctx.run_id, {
                "run_id": ctx.run_id,
                "started_at": ctx.started_at,
                "completed_at": result.completed_at,
                "status": "completed",
            })

            logger.info("engine.complete", run_id=ctx.run_id)
            return result
        except Exception:
            await self.storage.save_metadata(ctx.run_id, {
                "run_id": ctx.run_id,
                "started_at": ctx.started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "status": "failed",
                "errors": ctx.errors,
            })
            raise

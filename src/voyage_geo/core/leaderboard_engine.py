"""LeaderboardEngine — orchestrates category-wide brand comparison.

Brands are NOT preset. The flow is:
1. Generate leaderboard queries using just the category name
2. Execute queries against AI providers
3. Extract ALL brand names from what AI actually recommended
4. Analyze each extracted brand against the shared responses
5. Rank and report
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime

import structlog

from voyage_geo.config.schema import ProviderConfig, VoyageGeoConfig
from voyage_geo.core.context import RunContext
from voyage_geo.providers.registry import ProviderRegistry, create_provider
from voyage_geo.stages.analysis.stage import ANALYZER_MAP, AnalysisStage
from voyage_geo.stages.execution.stage import ExecutionStage
from voyage_geo.stages.query_generation.leaderboard_queries import generate_leaderboard_queries
from voyage_geo.stages.reporting.leaderboard_renderer import LeaderboardRenderer
from voyage_geo.storage.filesystem import FileSystemStorage
from voyage_geo.types.analysis import AnalysisResult
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.leaderboard import LeaderboardEntry, LeaderboardResult
from voyage_geo.types.result import ExecutionRun
from voyage_geo.utils.leaderboard_progress import (
    analysis_progress,
    brand_discovery_status,
    leaderboard_header,
    print_leaderboard_table,
)
from voyage_geo.utils.progress import console
from voyage_geo.utils.text import (
    deduplicate_brands,
    extract_all_brands_with_llm,
    extract_narratives_with_llm,
    extract_ranked_brands_with_llm,
)

logger = structlog.get_logger()


class LeaderboardEngine:
    def __init__(
        self,
        config: VoyageGeoConfig,
        category: str,
        *,
        max_brands: int = 50,
        report_formats: list[str] | None = None,
        stop_after: str | None = None,
        resume_run_id: str | None = None,
    ) -> None:
        self.config = config
        self.category = category
        self.max_brands = max_brands
        self.report_formats = report_formats or ["html", "json"]
        self.stop_after = stop_after
        self.resume_run_id = resume_run_id

        self.storage = FileSystemStorage(config.output_dir)
        self.provider_registry = ProviderRegistry()
        self._register_providers()
        self._processing_provider = self._create_processing_provider()

    def _register_providers(self) -> None:
        for name, pconfig in self.config.providers.items():
            if pconfig.enabled and pconfig.api_key:
                self.provider_registry.register(name, pconfig)

    def _create_processing_provider(self):
        proc = self.config.processing
        if not proc.api_key:
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
        return create_provider(proc.provider, provider_config)

    def _create_run_id(self) -> str:
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        short = uuid.uuid4().hex[:6]
        return f"lb-{ts}-{short}"

    def _parse_json_response(self, text: str) -> dict:
        """Extract and parse a JSON object from an LLM response."""
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        return json.loads(text)

    async def _get_category_context(self) -> tuple[str, str, list[str]]:
        """Get industry, category label, and keywords for query generation.

        This is a lightweight LLM call — just context, no brand list.
        """
        console.print(f"  Getting category context for [bold]{self.category}[/bold]...")

        prompt = f"""For the category "{self.category}", provide context for generating search queries.

Return ONLY a valid JSON object:
- "industry": the industry (e.g. "venture capital", "CRM software")
- "category": a short label (e.g. "VC firms", "CRM tools")
- "keywords": array of 5-10 relevant keywords

Example: {{"industry": "venture capital", "category": "VC firms", "keywords": ["venture capital", "startup funding", "seed round", "Series A"]}}

JSON object:"""

        resp = await self._processing_provider.query(prompt)
        data = self._parse_json_response(resp.text)
        return (
            data.get("industry", self.category),
            data.get("category", self.category),
            data.get("keywords", []),
        )

    async def run(self) -> LeaderboardResult:
        if self.resume_run_id:
            run_id = self.resume_run_id
            meta = await self.storage.load_json(run_id, "metadata.json") or {}
            started_at = meta.get("started_at", datetime.now(UTC).isoformat())
            logger.info("leaderboard.resume", run_id=run_id)
        else:
            run_id = self._create_run_id()
            started_at = datetime.now(UTC).isoformat()

        await self.storage.create_run_dir(run_id)
        await self.storage.save_metadata(run_id, {
            "run_id": run_id,
            "type": "leaderboard",
            "category": self.category,
            "started_at": started_at,
            "status": "running",
        })

        try:
            result = await self._execute(run_id, started_at)

            final_status = "completed"
            if self.stop_after:
                final_status = f"stopped-after-{self.stop_after}"

            await self.storage.save_metadata(run_id, {
                "run_id": run_id,
                "type": "leaderboard",
                "category": self.category,
                "brands": result.brands,
                "started_at": started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "status": final_status,
            })

            return result
        except Exception:
            await self.storage.save_metadata(run_id, {
                "run_id": run_id,
                "type": "leaderboard",
                "category": self.category,
                "started_at": started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "status": "failed",
            })
            raise

    async def _analyze_single_brand(
        self,
        brand: str,
        brands: list[str],
        run_id: str,
        industry: str,
        category_label: str,
        keywords: list[str],
        results: list,
        extracted_claims: list[dict],
        ranked_lists_by_response: dict[str, list[str]],
        analyzers_enabled: list[str],
    ) -> LeaderboardEntry:
        """Analyze a single brand in a thread (all analyzers are sync pure computation)."""
        other_brands = [b for b in brands if b != brand]
        brand_profile = BrandProfile(
            name=brand,
            industry=industry,
            category=category_label,
            competitors=other_brands,
            keywords=keywords,
        )

        analysis = AnalysisResult(
            run_id=run_id,
            brand=brand,
            analyzed_at=datetime.now(UTC).isoformat(),
        )

        def _sync_analyze():
            for analyzer_name in analyzers_enabled:
                cls = ANALYZER_MAP.get(analyzer_name)
                if not cls:
                    continue

                analyzer_instance = cls()

                if analyzer_name in ("mindshare", "competitor"):
                    result = analyzer_instance.analyze(
                        results, brand_profile, extracted_competitors=brands
                    )
                elif analyzer_name == "rank-position":
                    result = analyzer_instance.analyze(
                        results, brand_profile, ranked_lists_by_response=ranked_lists_by_response
                    )
                elif analyzer_name == "narrative":
                    result = analyzer_instance.analyze(
                        results, brand_profile, extracted_claims=extracted_claims
                    )
                else:
                    result = analyzer_instance.analyze(results, brand_profile)

                if analyzer_name == "mindshare":
                    analysis.mindshare = result
                elif analyzer_name == "mention-rate":
                    analysis.mention_rate = result
                elif analyzer_name == "sentiment":
                    analysis.sentiment = result
                elif analyzer_name == "positioning":
                    analysis.positioning = result
                elif analyzer_name == "rank-position":
                    analysis.rank_position = result
                elif analyzer_name == "citation":
                    analysis.citations = result
                elif analyzer_name == "competitor":
                    analysis.competitor_analysis = result
                elif analyzer_name == "narrative":
                    analysis.narrative = result

            temp_stage = AnalysisStage(self.storage, self._processing_provider)
            analysis.summary = temp_stage._build_summary(analysis, brand_profile)

        await asyncio.to_thread(_sync_analyze)

        slug = brand.lower().replace(" ", "-")
        await self.storage.save_json(run_id, f"analysis/{slug}.json", analysis)

        return self._build_entry(brand, analysis)

    @staticmethod
    def _build_entry(brand: str, analysis: AnalysisResult) -> LeaderboardEntry:
        """Build a slim LeaderboardEntry from an AnalysisResult."""
        top_pos_excerpt = ""
        top_pos_provider = ""
        top_pos_score = 0.0
        if analysis.sentiment.top_positive:
            exc = analysis.sentiment.top_positive[0]
            top_pos_excerpt = exc.text[:200]
            top_pos_provider = exc.provider
            top_pos_score = exc.score

        top_neg_excerpt = ""
        top_neg_provider = ""
        top_neg_score = 0.0
        if analysis.sentiment.top_negative:
            exc = analysis.sentiment.top_negative[0]
            top_neg_excerpt = exc.text[:200]
            top_neg_provider = exc.provider
            top_neg_score = exc.score

        return LeaderboardEntry(
            rank=0,
            brand=brand,
            overall_score=analysis.summary.overall_score,
            mention_rate=analysis.mention_rate.overall,
            mindshare=analysis.mindshare.overall,
            rank_position_score=analysis.rank_position.weighted_visibility,
            avg_rank_position=analysis.rank_position.avg_position,
            sentiment_score=analysis.sentiment.overall,
            sentiment_label=analysis.sentiment.label,
            mention_rate_by_provider=dict(analysis.mention_rate.by_provider),
            total_mentions=analysis.mention_rate.total_mentions,
            total_responses=analysis.mention_rate.total_responses,
            mindshare_rank=analysis.mindshare.rank,
            total_brands_detected=analysis.mindshare.total_brands_detected,
            strengths=list(analysis.summary.strengths),
            weaknesses=list(analysis.summary.weaknesses),
            top_positive_excerpt=top_pos_excerpt,
            top_positive_provider=top_pos_provider,
            top_positive_score=top_pos_score,
            top_negative_excerpt=top_neg_excerpt,
            top_negative_provider=top_neg_provider,
            top_negative_score=top_neg_score,
        )

    async def _execute(self, run_id: str, started_at: str) -> LeaderboardResult:
        from voyage_geo.types.query import QuerySet

        # Step 1: Get category context (industry, keywords — NOT brands)
        category_profile_data = None
        if self.resume_run_id:
            category_profile_data = await self.storage.load_json(run_id, "category-profile.json")

        if category_profile_data:
            category_profile = BrandProfile(**category_profile_data)
            industry = category_profile.industry
            category_label = category_profile.category
            keywords = category_profile.keywords
            console.print(f"  Loaded category context from previous run")
        else:
            industry, category_label, keywords = await self._get_category_context()
            category_profile = BrandProfile(
                name=category_label,
                description=f"Category leaderboard for {self.category}",
                industry=industry,
                category=category_label,
                keywords=keywords,
            )
            await self.storage.save_json(run_id, "category-profile.json", category_profile)

        console.print(f"  [dim]Industry: {industry} | Keywords: {', '.join(keywords[:5])}[/dim]")

        # Step 2: Generate leaderboard queries
        existing_queries = None
        if self.resume_run_id:
            query_data = await self.storage.load_json(run_id, "queries.json")
            if query_data:
                existing_queries = QuerySet(**query_data)
                console.print(f"  [dim]Loaded {len(existing_queries.queries)} queries from previous run[/dim]")

        if existing_queries:
            query_set = existing_queries
        else:
            total_count = self.config.queries.count
            console.print()
            console.print(f"  [bold]Generating {total_count} leaderboard queries...[/bold]")
            console.print(f"  [dim]Strategies: direct-rec, vertical, comparison, scenario[/dim]")

            queries = await generate_leaderboard_queries(
                category_profile, total_count, self._processing_provider
            )
            query_set = QuerySet(
                brand=category_label,
                queries=queries,
                generated_at=datetime.now(UTC).isoformat(),
                total_count=len(queries),
            )
            await self.storage.save_json(run_id, "queries.json", query_set)

            from voyage_geo.utils.progress import print_query_table
            console.print(f"  [green]Generated {len(queries)} leaderboard queries[/green]")
            console.print()
            print_query_table(queries)

        if not query_set.queries:
            raise RuntimeError("Query generation failed — no queries produced")

        # Stop here if requested — allows user to review queries before execution
        if self.stop_after == "query-generation":
            console.print()
            console.print(f"  [yellow]Stopped after query generation.[/yellow] Run ID: [bold]{run_id}[/bold]")
            console.print(f"  Review queries: {self.config.output_dir}/{run_id}/queries.json")
            console.print(f"  Resume: python3 -m voyage_geo leaderboard \"{self.category}\" --resume {run_id}")
            return LeaderboardResult(
                run_id=run_id,
                category=self.category,
                brands=[],
                entries=[],
                total_queries=len(query_set.queries),
                providers_used=[p.name for p in self.provider_registry.get_enabled()],
                analyzed_at=datetime.now(UTC).isoformat(),
            )

        # Step 3: Execute queries against AI providers (resume-aware)
        existing_execution = None
        if self.resume_run_id:
            results_data = await self.storage.load_json(run_id, "results/results.json")
            if results_data:
                existing_execution = ExecutionRun(**results_data)
                if existing_execution.results:
                    console.print(f"  [dim]Loaded {len(existing_execution.results)} execution results from previous run[/dim]")

        if existing_execution and existing_execution.results:
            execution_run = existing_execution
        else:
            query_ctx = RunContext(
                run_id=run_id,
                config=self.config,
                started_at=started_at,
                brand_profile=category_profile,
                query_set=query_set,
            )

            console.print()
            console.print("  [bold]Executing queries against AI providers...[/bold]")

            exec_stage = ExecutionStage(self.provider_registry, self.storage)
            query_ctx = await exec_stage.execute(query_ctx)

            if not query_ctx.execution_run:
                raise RuntimeError("Execution failed — no results")

            execution_run = query_ctx.execution_run

        results = execution_run.results
        valid_results = [r for r in results if not r.error and r.response]

        if not valid_results:
            raise RuntimeError("No valid responses received from any provider")

        response_texts = [r.response for r in valid_results]

        # Step 4: Extract ALL brands that AI actually mentioned (checkpoint-aware)
        checkpoint = None
        if self.resume_run_id:
            checkpoint = await self.storage.load_json(run_id, "analysis/extraction-checkpoint.json")

        if checkpoint:
            brands = checkpoint["brands"]
            extracted_claims = checkpoint.get("extracted_claims", [])
            ranked_lists_by_response = checkpoint.get("ranked_lists_by_response", {})
            console.print(f"  [dim]Loaded extraction checkpoint: {len(brands)} brands, {len(extracted_claims)} claims[/dim]")
        else:
            console.print()
            console.print(f"  [bold]Extracting brands from AI responses...[/bold]")
            console.print(f"  [dim]Finding every brand that AI models actually recommended[/dim]")

            brands = await extract_all_brands_with_llm(
                response_texts, category_label, self._processing_provider,
                max_brands=self.max_brands,
                industry=industry,
                keywords=keywords,
                sample_queries=[q.text for q in query_set.queries[:5]],
            )

            if not brands:
                raise RuntimeError("No brands found in AI responses")

            # Deduplicate: merge substring matches + LLM alias resolution
            raw_count = len(brands)
            brands, alias_map = await deduplicate_brands(
                brands, category_label, self._processing_provider
            )
            if len(brands) < raw_count:
                console.print(f"  [green]Deduplicated {raw_count} → {len(brands)} unique brands[/green]")

            leaderboard_header(self.category, len(brands))
            brand_discovery_status(brands)

            # Extract narratives for analysis
            extracted_claims: list[dict] = []
            ranked_lists_by_response: dict[str, list[str]] = {}

            console.print(f"  Extracting rank positions via {self._processing_provider.display_name}...")
            response_items = [
                (f"{r.provider}:{r.query_id}:{r.iteration}", r.response)
                for r in valid_results
            ]
            ranked_lists_by_response = await extract_ranked_brands_with_llm(
                response_items,
                category_label,
                self._processing_provider,
                brands,
            )
            ranked_covered = sum(1 for v in ranked_lists_by_response.values() if v)
            console.print(f"  [green]Detected explicit rankings in {ranked_covered} responses[/green]")

            console.print(f"  Extracting narratives via {self._processing_provider.display_name}...")
            extracted_claims = await extract_narratives_with_llm(
                response_texts, category_label, category_label, self._processing_provider
            )
            if extracted_claims:
                console.print(f"  [green]Extracted {len(extracted_claims)} claims[/green]")

            # Save extraction checkpoint
            await self.storage.save_json(run_id, "analysis/extraction-checkpoint.json", {
                "brands": brands,
                "alias_map": alias_map,
                "extracted_claims": extracted_claims,
                "ranked_lists_by_response": ranked_lists_by_response,
            })

        # Step 5: Analyze each brand against the shared responses (parallel, resume-aware)
        console.print()
        console.print(f"  [bold]Analyzing {len(brands)} brands...[/bold]")

        entries: list[LeaderboardEntry] = []
        analyzers_enabled = list(self.config.analysis.analyzers)
        to_analyze: list[str] = []

        for brand in brands:
            slug = brand.lower().replace(" ", "-")
            if self.resume_run_id:
                cached = await self.storage.load_json(run_id, f"analysis/{slug}.json")
                if cached:
                    analysis = AnalysisResult(**cached)
                    entry = self._build_entry(brand, analysis)
                    entries.append(entry)
                    console.print(f"  [dim]Loaded cached analysis for {brand}[/dim]")
                    continue
            to_analyze.append(brand)

        # Parallel analysis with bounded workers (config-driven, not fixed batch size).
        analysis_workers = max(1, min(64, self.config.execution.concurrency))
        semaphore = asyncio.Semaphore(analysis_workers)
        analyzed_count = len(entries)

        async def _analyze_with_limit(brand: str) -> LeaderboardEntry:
            nonlocal analyzed_count
            async with semaphore:
                analyzed_count += 1
                analysis_progress(brand, analyzed_count, len(brands))
                return await self._analyze_single_brand(
                    brand=brand,
                    brands=brands,
                    run_id=run_id,
                    industry=industry,
                    category_label=category_label,
                    keywords=keywords,
                    results=results,
                    extracted_claims=extracted_claims,
                    ranked_lists_by_response=ranked_lists_by_response,
                    analyzers_enabled=analyzers_enabled,
                )

        if to_analyze:
            tasks = [asyncio.create_task(_analyze_with_limit(b)) for b in to_analyze]
            for task in asyncio.as_completed(tasks):
                entries.append(await task)

        # Step 6: Rank by score
        entries.sort(key=lambda e: e.overall_score, reverse=True)
        for i, entry in enumerate(entries, 1):
            entry.rank = i

        providers_used = [p.name for p in self.provider_registry.get_enabled()]
        leaderboard_result = LeaderboardResult(
            run_id=run_id,
            category=self.category,
            brands=brands,
            entries=entries,
            total_queries=len(query_set.queries),
            providers_used=providers_used,
            analyzed_at=datetime.now(UTC).isoformat(),
        )

        await self.storage.save_json(run_id, "analysis/leaderboard.json", leaderboard_result)

        print_leaderboard_table(entries)

        # Step 7: Generate reports
        console.print()
        console.print("  [bold]Generating reports...[/bold]")

        renderer = LeaderboardRenderer(self.storage)
        await renderer.render(run_id, leaderboard_result, self.report_formats, execution_run, query_set)

        console.print(f"  [green]Reports saved to:[/green] {self.storage.run_dir(run_id) / 'reports'}")

        return leaderboard_result

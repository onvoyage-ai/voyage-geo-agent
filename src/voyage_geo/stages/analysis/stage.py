"""Stage 4: Analysis — runs all analyzers on execution results."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from voyage_geo.core.context import RunContext
from voyage_geo.core.pipeline import PipelineStage
from voyage_geo.providers.registry import ProviderRegistry
from voyage_geo.stages.analysis.analyzers.citation import CitationAnalyzer
from voyage_geo.stages.analysis.analyzers.competitor import CompetitorAnalyzer
from voyage_geo.stages.analysis.analyzers.mention_rate import MentionRateAnalyzer
from voyage_geo.stages.analysis.analyzers.mindshare import MindshareAnalyzer
from voyage_geo.stages.analysis.analyzers.narrative import NarrativeAnalyzer
from voyage_geo.stages.analysis.analyzers.positioning import PositioningAnalyzer
from voyage_geo.stages.analysis.analyzers.sentiment import SentimentAnalyzer
from voyage_geo.storage.filesystem import FileSystemStorage
from voyage_geo.types.analysis import AnalysisResult, ExecutiveSummary
from voyage_geo.types.brand import BrandProfile
from voyage_geo.utils.progress import console, stage_header
from voyage_geo.utils.text import extract_competitors_with_llm, extract_narratives_with_llm

logger = structlog.get_logger()

ANALYZER_MAP = {
    "mindshare": MindshareAnalyzer,
    "mention-rate": MentionRateAnalyzer,
    "sentiment": SentimentAnalyzer,
    "positioning": PositioningAnalyzer,
    "citation": CitationAnalyzer,
    "competitor": CompetitorAnalyzer,
    "narrative": NarrativeAnalyzer,
}


class AnalysisStage(PipelineStage):
    name = "analysis"
    description = "Analyze AI responses"

    def __init__(self, storage: FileSystemStorage, provider_registry: ProviderRegistry) -> None:
        self.storage = storage
        self.provider_registry = provider_registry

    async def execute(self, ctx: RunContext) -> RunContext:
        stage_header(self.name, self.description)

        if not ctx.execution_run or not ctx.brand_profile:
            raise RuntimeError("Execution results and brand profile required")

        results = ctx.execution_run.results
        profile = ctx.brand_profile
        analyzers_enabled = ctx.config.analysis.analyzers

        # Extract competitors and narratives from AI responses using LLM
        extracted_competitors: list[str] = []
        extracted_claims: list[dict] = []
        valid_results = [r for r in results if not r.error and r.response]
        if valid_results:
            providers = self.provider_registry.get_enabled()
            if providers:
                response_texts = [r.response for r in valid_results]
                llm_provider = providers[0]

                console.print("  Extracting competitors with LLM...")
                extracted_competitors = await extract_competitors_with_llm(
                    response_texts, profile.name, profile.category, llm_provider
                )
                if extracted_competitors:
                    console.print(f"  [green]Found competitors:[/green] {', '.join(extracted_competitors)}")

                if "narrative" in analyzers_enabled:
                    console.print("  Extracting narratives with LLM...")
                    extracted_claims = await extract_narratives_with_llm(
                        response_texts, profile.name, profile.category, llm_provider
                    )
                    if extracted_claims:
                        console.print(f"  [green]Extracted {len(extracted_claims)} claims[/green]")

        analysis = AnalysisResult(run_id=ctx.run_id, brand=profile.name, analyzed_at=datetime.now(UTC).isoformat())

        for analyzer_name in analyzers_enabled:
            cls = ANALYZER_MAP.get(analyzer_name)
            if not cls:
                continue
            console.print(f"  Running [cyan]{analyzer_name}[/cyan] analyzer...")
            analyzer_instance = cls()

            # Pass extracted data to analyzers that support it
            if analyzer_name in ("mindshare", "competitor"):
                result = analyzer_instance.analyze(results, profile, extracted_competitors=extracted_competitors)  # type: ignore[attr-defined]
            elif analyzer_name == "narrative":
                result = analyzer_instance.analyze(results, profile, extracted_claims=extracted_claims)  # type: ignore[attr-defined]
            else:
                result = analyzer_instance.analyze(results, profile)  # type: ignore[attr-defined]

            if analyzer_name == "mindshare":
                analysis.mindshare = result
            elif analyzer_name == "mention-rate":
                analysis.mention_rate = result
            elif analyzer_name == "sentiment":
                analysis.sentiment = result
            elif analyzer_name == "positioning":
                analysis.positioning = result
            elif analyzer_name == "citation":
                analysis.citations = result
            elif analyzer_name == "competitor":
                analysis.competitor_analysis = result
            elif analyzer_name == "narrative":
                analysis.narrative = result

        # Build executive summary
        analysis.summary = self._build_summary(analysis, profile)

        await self.storage.save_json(ctx.run_id, "analysis/analysis.json", analysis)
        await self.storage.save_json(ctx.run_id, "analysis/summary.json", analysis.summary)
        console.print(f"  [green]Analysis complete:[/green] {len(analyzers_enabled)} analyzers run")

        ctx.analysis_result = analysis
        return ctx

    def _build_summary(self, analysis: AnalysisResult, profile: BrandProfile) -> ExecutiveSummary:
        findings = []
        strengths = []
        weaknesses = []
        recommendations = []

        mr = analysis.mention_rate.overall
        findings.append(f"{profile.name} is mentioned in {mr*100:.1f}% of AI responses")

        ms = analysis.mindshare.overall
        findings.append(f"Brand owns {ms*100:.1f}% mindshare across AI models")

        sent = analysis.sentiment
        findings.append(f"Overall sentiment is {sent.label} ({sent.overall:.2f}) with {sent.confidence:.0%} confidence")

        if mr > 0.5:
            strengths.append("Strong presence across AI responses")
        elif mr < 0.2:
            weaknesses.append("Low mention rate — AI models rarely recommend this brand")

        if sent.label == "positive":
            strengths.append("Positive sentiment when mentioned")
        elif sent.label == "negative":
            weaknesses.append("Negative sentiment in AI responses")

        rank = analysis.mindshare.rank
        total = analysis.mindshare.total_brands_detected
        if rank <= 3:
            strengths.append(f"Ranked #{rank} out of {total} brands for mindshare")
        else:
            weaknesses.append(f"Ranked #{rank} out of {total} brands — room to improve")
            recommendations.append("Focus on improving brand visibility in AI training data sources")

        if mr < 0.3:
            recommendations.append("Create more authoritative content that AI models can reference")
        if sent.label != "positive":
            recommendations.append("Address negative narratives and strengthen positive brand signals")

        # Narrative gap recommendations
        missing_usps = [g.usp for g in analysis.narrative.gaps if not g.covered]
        if missing_usps:
            for usp in missing_usps[:3]:
                recommendations.append(f"AI models don't mention your USP: \"{usp}\" — create content reinforcing this")
        if analysis.narrative.coverage_score > 0:
            findings.append(f"AI models cover {analysis.narrative.coverage_score*100:.0f}% of stated USPs")
        if analysis.narrative.brand_negative_count > analysis.narrative.brand_positive_count:
            weaknesses.append("More negative than positive claims in AI narratives")

        score = (mr * 30 + ms * 30 + (sent.overall + 1) / 2 * 20 + (1 / rank if rank > 0 else 0) * 20)
        score = min(max(round(score, 1), 0), 100)

        headline = f"{profile.name}: {'Strong' if score > 60 else 'Moderate' if score > 30 else 'Weak'} AI visibility ({score}/100)"

        return ExecutiveSummary(
            headline=headline,
            key_findings=findings,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            overall_score=score,
        )

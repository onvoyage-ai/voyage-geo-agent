"""Stage 4: Analysis — runs all analyzers on execution results."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from voyage_geo.core.context import RunContext
from voyage_geo.core.pipeline import PipelineStage
from voyage_geo.providers.base import BaseProvider
from voyage_geo.stages.analysis.analyzers.citation import CitationAnalyzer
from voyage_geo.stages.analysis.analyzers.competitor import CompetitorAnalyzer
from voyage_geo.stages.analysis.analyzers.mention_rate import MentionRateAnalyzer
from voyage_geo.stages.analysis.analyzers.mindshare import MindshareAnalyzer
from voyage_geo.stages.analysis.analyzers.narrative import NarrativeAnalyzer
from voyage_geo.stages.analysis.analyzers.positioning import PositioningAnalyzer
from voyage_geo.stages.analysis.analyzers.rank_position import RankPositionAnalyzer
from voyage_geo.stages.analysis.analyzers.sentiment import SentimentAnalyzer
from voyage_geo.storage.filesystem import FileSystemStorage
from voyage_geo.storage.schema import SCHEMA_VERSION
from voyage_geo.types.analysis import AnalysisResult, ExecutiveSummary
from voyage_geo.types.brand import BrandProfile
from voyage_geo.utils.progress import console, stage_header
from voyage_geo.utils.text import (
    extract_competitors_with_llm,
    extract_narratives_with_llm,
    extract_ranked_brands_with_llm,
)

logger = structlog.get_logger()

ANALYZER_MAP = {
    "mindshare": MindshareAnalyzer,
    "mention-rate": MentionRateAnalyzer,
    "sentiment": SentimentAnalyzer,
    "positioning": PositioningAnalyzer,
    "rank-position": RankPositionAnalyzer,
    "citation": CitationAnalyzer,
    "competitor": CompetitorAnalyzer,
    "narrative": NarrativeAnalyzer,
}


class AnalysisStage(PipelineStage):
    name = "analysis"
    description = "Analyze AI responses"

    def __init__(self, storage: FileSystemStorage, processing_provider: BaseProvider) -> None:
        self.storage = storage
        self.processing_provider = processing_provider

    async def execute(self, ctx: RunContext) -> RunContext:
        stage_header(self.name, self.description)

        if not ctx.execution_run or not ctx.brand_profile:
            raise RuntimeError("Execution results and brand profile required")

        results = ctx.execution_run.results
        profile = ctx.brand_profile
        analyzers_enabled = ctx.config.analysis.analyzers

        # Extract competitors and narratives from AI responses using the processing provider
        extracted_competitors: list[str] = []
        extracted_claims: list[dict] = []
        ranked_lists_by_response: dict[str, list[str]] = {}
        valid_results = [r for r in results if not r.error and r.response]
        if valid_results:
            response_texts = [r.response for r in valid_results]

            console.print(f"  Extracting competitors via {self.processing_provider.display_name}...")
            extracted_competitors = await extract_competitors_with_llm(
                response_texts, profile.name, profile.category, self.processing_provider
            )
            if extracted_competitors:
                console.print(f"  [green]Found competitors:[/green] {', '.join(extracted_competitors)}")

            if "rank-position" in analyzers_enabled:
                candidates = [profile.name] + (extracted_competitors or profile.competitors)
                response_items = [
                    (f"{r.provider}:{r.query_id}:{r.iteration}", r.response)
                    for r in valid_results
                ]
                console.print(f"  Extracting rank positions via {self.processing_provider.display_name}...")
                ranked_lists_by_response = await extract_ranked_brands_with_llm(
                    response_items,
                    profile.category,
                    self.processing_provider,
                    candidates,
                )
                covered = sum(1 for v in ranked_lists_by_response.values() if v)
                console.print(f"  [green]Detected explicit rankings in {covered} responses[/green]")

            if "narrative" in analyzers_enabled:
                console.print(f"  Extracting narratives via {self.processing_provider.display_name}...")
                extracted_claims = await extract_narratives_with_llm(
                    response_texts, profile.name, profile.category, self.processing_provider
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
            elif analyzer_name == "rank-position":
                result = analyzer_instance.analyze(
                    results, profile, ranked_lists_by_response=ranked_lists_by_response
                )  # type: ignore[attr-defined]
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
            elif analyzer_name == "rank-position":
                analysis.rank_position = result
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
        await self.storage.save_json(ctx.run_id, "analysis/snapshot.json", self._build_snapshot(analysis))
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

        rp = analysis.rank_position
        if rp.total_ranked_responses > 0:
            findings.append(
                f"Appears in {rp.mention_in_ranked_lists}/{rp.total_ranked_responses} explicit ranked lists"
            )
            if rp.avg_position > 0:
                findings.append(f"Average explicit list position: #{rp.avg_position:.1f}")

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

        if rp.total_ranked_responses > 0:
            if rp.top3_rate >= 0.5:
                strengths.append("Frequently placed in top-3 in explicit ranking responses")
            elif rp.mention_coverage < 0.25:
                weaknesses.append("Rarely appears in explicit ranked lists")
                recommendations.append("Publish comparison-oriented content to improve list placement")

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

        positioning_strength = self._positioning_strength(analysis)
        if rp.total_ranked_responses > 0:
            rank_visibility = rp.weighted_visibility
        else:
            rank_visibility = 1 / rank if rank > 0 else 0

        score = (
            mr * 28
            + ms * 22
            + rank_visibility * 25
            + ((sent.overall + 1) / 2) * 15
            + positioning_strength * 10
        )
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

    @staticmethod
    def _build_snapshot(analysis: AnalysisResult) -> dict:
        """Build a compact, stable artifact for time-series trend indexing."""
        competitors = sorted(
            analysis.competitor_analysis.competitors,
            key=lambda c: c.mindshare,
            reverse=True,
        )
        brand_lower = analysis.brand.lower()
        brand_comp = next((c for c in competitors if c.name.lower() == brand_lower), None)
        leader = competitors[0] if competitors else None

        brand_mindshare = brand_comp.mindshare if brand_comp else analysis.mindshare.overall
        brand_mention_rate = brand_comp.mention_rate if brand_comp else analysis.mention_rate.overall

        top_competitors = [c for c in competitors if c.name.lower() != brand_lower][:5]
        top5_pool = competitors[:5]
        top5_mindshare_sum = sum(c.mindshare for c in top5_pool)
        share_of_voice_top5 = (brand_mindshare / top5_mindshare_sum) if top5_mindshare_sum > 0 else 0.0

        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": analysis.run_id,
            "brand": analysis.brand,
            "analyzed_at": analysis.analyzed_at,
            "overall_score": analysis.summary.overall_score,
            "mention_rate": analysis.mention_rate.overall,
            "mindshare": analysis.mindshare.overall,
            "sentiment_score": analysis.sentiment.overall,
            "sentiment_label": analysis.sentiment.label,
            "sentiment_confidence": analysis.sentiment.confidence,
            "mindshare_rank": analysis.mindshare.rank,
            "total_brands_detected": analysis.mindshare.total_brands_detected,
            "mention_rate_by_provider": analysis.mention_rate.by_provider,
            "mindshare_by_provider": analysis.mindshare.by_provider,
            "sentiment_by_provider": analysis.sentiment.by_provider,
            "sentiment_label_by_provider": analysis.sentiment.by_provider_label,
            "competitor_relative": {
                "brand_rank": analysis.competitor_analysis.brand_rank or analysis.mindshare.rank,
                "leader_brand": leader.name if leader else "",
                "leader_mindshare": leader.mindshare if leader else 0.0,
                "leader_mention_rate": leader.mention_rate if leader else 0.0,
                "mindshare_gap_to_leader": brand_mindshare - (leader.mindshare if leader else 0.0),
                "mention_rate_gap_to_leader": brand_mention_rate - (leader.mention_rate if leader else 0.0),
                "share_of_voice_top5": share_of_voice_top5,
                "top_competitors": [
                    {
                        "name": c.name,
                        "mindshare": c.mindshare,
                        "mention_rate": c.mention_rate,
                        "sentiment": c.sentiment,
                    }
                    for c in top_competitors
                ],
            },
        }

    @staticmethod
    def _positioning_strength(analysis: AnalysisResult) -> float:
        attrs = analysis.positioning.attributes
        if not attrs:
            return 0.5

        positive_terms = {
            "leader",
            "popular",
            "best",
            "top",
            "innovative",
            "reliable",
            "powerful",
            "simple",
            "enterprise",
            "scalable",
            "trusted",
            "fast",
            "secure",
            "flexible",
            "comprehensive",
            "user-friendly",
            "modern",
            "mature",
            "growing",
        }
        negative_terms = {"expensive", "complex", "limited", "outdated", "basic"}

        weighted_total = 0.0
        freq_total = 0
        for attr in attrs:
            polarity = 1.0 if attr.attribute in positive_terms else -1.0 if attr.attribute in negative_terms else 0.0
            sentiment_conf = (attr.sentiment + 1) / 2  # -1..1 -> 0..1
            weighted_total += polarity * sentiment_conf * attr.frequency
            freq_total += attr.frequency

        if freq_total == 0:
            return 0.5

        normalized = weighted_total / freq_total  # roughly -1..1
        normalized = max(min(normalized, 1.0), -1.0)
        return (normalized + 1) / 2

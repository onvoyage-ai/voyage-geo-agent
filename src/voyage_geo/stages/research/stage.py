"""Stage 1: Brand research — builds a BrandProfile from AI + optional web scraping."""

from __future__ import annotations

from datetime import UTC

import httpx
import structlog
from bs4 import BeautifulSoup

from voyage_geo.core.context import RunContext
from voyage_geo.core.pipeline import PipelineStage
from voyage_geo.providers.base import BaseProvider
from voyage_geo.providers.registry import ProviderRegistry
from voyage_geo.storage.filesystem import FileSystemStorage
from voyage_geo.types.brand import BrandProfile, ScrapedContent
from voyage_geo.utils.progress import console, stage_header

logger = structlog.get_logger()

RESEARCH_PROMPT = """You are a brand research analyst. Given the following brand, produce a structured profile.

Brand: {brand}
Website: {website}
{scraped_section}

Return a JSON object with exactly these fields:
- description: 1-2 sentence description of what the brand does
- industry: the industry (e.g. "SaaS", "Fintech", "E-commerce")
- category: the product category (e.g. "project management software", "spend management platform")
- competitors: list of 5-8 direct competitors (brand names only)
- keywords: list of 8-12 relevant search keywords/phrases
- unique_selling_points: list of 3-5 USPs
- target_audience: list of 3-5 target audience segments

Return ONLY valid JSON, no markdown fences or explanation."""


class ResearchStage(PipelineStage):
    name = "research"
    description = "Research brand profile"

    def __init__(self, provider_registry: ProviderRegistry, storage: FileSystemStorage) -> None:
        self.provider_registry = provider_registry
        self.storage = storage

    async def execute(self, ctx: RunContext) -> RunContext:
        stage_header(self.name, self.description)

        brand = ctx.config.brand or "Unknown"
        website = ctx.config.website

        # If profile already exists, skip
        if ctx.brand_profile:
            console.print(f"  [dim]Using existing brand profile for {brand}[/dim]")
            return ctx

        scraped: ScrapedContent | None = None
        scraped_section = ""

        # Scrape website if provided
        if website:
            console.print(f"  Scraping [cyan]{website}[/cyan]...")
            scraped = await self._scrape(website)
            if scraped:
                scraped_section = f"Scraped website content:\nTitle: {scraped.title}\nDescription: {scraped.meta_description}\nHeadings: {', '.join(scraped.headings[:10])}\nContent excerpt: {scraped.body_text[:1000]}"

        # Pick a provider for research
        provider = self._pick_provider()
        prompt = RESEARCH_PROMPT.format(brand=brand, website=website or "N/A", scraped_section=scraped_section)

        console.print(f"  Researching [bold]{brand}[/bold] via {provider.display_name}...")
        response = await provider.query(prompt)

        # Parse JSON response
        import json
        try:
            text = response.text.strip()
            # Strip markdown fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                elif "```" in text:
                    text = text[:text.rfind("```")]
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("research.json_parse_failed", text=response.text[:200])
            data = {}

        profile = BrandProfile(
            name=brand,
            website=website,
            description=data.get("description", ""),
            industry=data.get("industry", ""),
            category=data.get("category", ""),
            competitors=data.get("competitors", ctx.config.competitors) or [],
            keywords=data.get("keywords", []),
            unique_selling_points=data.get("unique_selling_points", []),
            target_audience=data.get("target_audience", []),
            scraped_content=scraped,
        )

        await self.storage.save_json(ctx.run_id, "brand-profile.json", profile)
        console.print(f"  [green]Brand profile built:[/green] {profile.category} | {len(profile.competitors)} competitors | {len(profile.keywords)} keywords")

        ctx.brand_profile = profile
        return ctx

    def _pick_provider(self) -> BaseProvider:
        enabled = self.provider_registry.get_enabled()
        if not enabled:
            raise RuntimeError("No providers configured for research")
        preferred = ["openai", "anthropic", "google", "perplexity"]
        for name in preferred:
            match = next((p for p in enabled if p.name == name), None)
            if match:
                return match
        return enabled[0]

    async def _scrape(self, url: str) -> ScrapedContent | None:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                resp = await client.get(url, headers={"User-Agent": "VoyageGEO/0.1"})
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            from datetime import datetime
            meta_tag = soup.find("meta", {"name": "description"})
            meta_desc = meta_tag.get("content", "") if meta_tag else ""
            return ScrapedContent(
                title=soup.title.string.strip() if soup.title and soup.title.string else "",
                meta_description=str(meta_desc),
                headings=[str(h.get_text(strip=True)) for h in soup.find_all(["h1", "h2", "h3"])[:20]],  # type: ignore[misc]
                body_text=soup.get_text(separator=" ", strip=True)[:3000],
                links=[str(a["href"]) for a in soup.find_all("a", href=True)[:50]],
                fetched_at=datetime.now(UTC).isoformat(),
            )
        except Exception as e:
            logger.warning("scrape.failed", url=url, error=str(e))
            return None

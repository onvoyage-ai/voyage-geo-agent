from __future__ import annotations

from pydantic import BaseModel


class ScrapedContent(BaseModel):
    title: str = ""
    meta_description: str = ""
    headings: list[str] = []
    body_text: str = ""
    links: list[str] = []
    fetched_at: str = ""


class BrandProfile(BaseModel):
    name: str
    website: str | None = None
    description: str = ""
    industry: str = ""
    category: str = ""
    competitors: list[str] = []
    keywords: list[str] = []
    unique_selling_points: list[str] = []
    target_audience: list[str] = []
    scraped_content: ScrapedContent | None = None

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SentimentExcerpt(BaseModel):
    text: str
    score: float
    provider: str


class SentimentScore(BaseModel):
    overall: float = 0.0
    label: Literal["positive", "neutral", "negative"] = "neutral"
    confidence: float = 0.0
    by_provider: dict[str, float] = {}
    by_provider_label: dict[str, Literal["positive", "neutral", "negative"]] = {}
    by_category: dict[str, float] = {}
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    total_sentences: int = 0
    top_positive: list[SentimentExcerpt] = []
    top_negative: list[SentimentExcerpt] = []


class MindshareScore(BaseModel):
    overall: float = 0.0
    by_provider: dict[str, float] = {}
    by_category: dict[str, float] = {}
    rank: int = 0
    total_brands_detected: int = 0


class MentionRateScore(BaseModel):
    overall: float = 0.0
    by_provider: dict[str, float] = {}
    by_category: dict[str, float] = {}
    total_mentions: int = 0
    total_responses: int = 0


class PositionAttribute(BaseModel):
    attribute: str
    frequency: int
    sentiment: float


class PositioningScore(BaseModel):
    primary_position: str = ""
    attributes: list[PositionAttribute] = []
    by_provider: dict[str, str] = {}


class CitationSource(BaseModel):
    source: str
    count: int
    providers: list[str]


class CitationScore(BaseModel):
    total_citations: int = 0
    unique_sources_cited: int = 0
    citation_rate: float = 0.0
    by_provider: dict[str, int] = {}
    top_sources: list[CitationSource] = []


class CompetitorScore(BaseModel):
    name: str
    mention_rate: float = 0.0
    sentiment: float = 0.0
    mindshare: float = 0.0


class CompetitorAnalysis(BaseModel):
    competitors: list[CompetitorScore] = []
    brand_rank: int = 0


class BrandClaim(BaseModel):
    brand: str
    attribute: str  # pricing, features, security, ease-of-use, integration, support, scalability
    sentiment: Literal["positive", "negative", "neutral"]
    claim: str


class NarrativeGap(BaseModel):
    usp: str
    covered: bool
    detail: str


class NarrativeAnalysis(BaseModel):
    claims: list[BrandClaim] = []
    total_claims: int = 0
    brand_themes: dict[str, list[BrandClaim]] = {}  # attribute → claims about target brand
    brand_positive_count: int = 0
    brand_negative_count: int = 0
    brand_neutral_count: int = 0
    gaps: list[NarrativeGap] = []
    coverage_score: float = 0.0  # pct of USPs covered
    competitor_themes: dict[str, dict[str, int]] = {}  # brand → {attribute → claim count}


class ExecutiveSummary(BaseModel):
    headline: str = ""
    key_findings: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []
    overall_score: float = 0.0


class AnalysisResult(BaseModel):
    run_id: str
    brand: str
    analyzed_at: str = ""
    mindshare: MindshareScore = MindshareScore()
    mention_rate: MentionRateScore = MentionRateScore()
    sentiment: SentimentScore = SentimentScore()
    positioning: PositioningScore = PositioningScore()
    citations: CitationScore = CitationScore()
    competitor_analysis: CompetitorAnalysis = CompetitorAnalysis()
    narrative: NarrativeAnalysis = NarrativeAnalysis()
    summary: ExecutiveSummary = ExecutiveSummary()

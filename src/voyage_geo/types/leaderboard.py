from __future__ import annotations

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    brand: str
    overall_score: float
    mention_rate: float  # 0-1
    mindshare: float  # 0-1
    rank_position_score: float = 0.0  # 0-1 weighted rank visibility
    avg_rank_position: float = 0.0
    sentiment_score: float  # -1 to +1
    sentiment_label: str  # positive/neutral/negative
    mention_rate_by_provider: dict[str, float] = {}  # for heatmap
    # Summary fields (previously accessed via entry.analysis.*)
    total_mentions: int = 0
    total_responses: int = 0
    mindshare_rank: int = 0
    total_brands_detected: int = 0
    strengths: list[str] = []
    weaknesses: list[str] = []
    top_positive_excerpt: str = ""
    top_positive_provider: str = ""
    top_positive_score: float = 0.0
    top_negative_excerpt: str = ""
    top_negative_provider: str = ""
    top_negative_score: float = 0.0


class LeaderboardResult(BaseModel):
    run_id: str
    category: str
    brands: list[str]
    entries: list[LeaderboardEntry]  # sorted by rank
    total_queries: int
    providers_used: list[str]
    analyzed_at: str

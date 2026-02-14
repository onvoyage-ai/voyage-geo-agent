from __future__ import annotations

from pydantic import BaseModel

from voyage_geo.types.analysis import AnalysisResult


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
    analysis: AnalysisResult


class LeaderboardResult(BaseModel):
    run_id: str
    category: str
    brands: list[str]
    entries: list[LeaderboardEntry]  # sorted by rank
    total_queries: int
    providers_used: list[str]
    analyzed_at: str

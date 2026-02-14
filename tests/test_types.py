"""Tests for Pydantic types."""

from voyage_geo.types.analysis import AnalysisResult, SentimentScore
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.query import GeneratedQuery
from voyage_geo.types.result import QueryResult


def test_brand_profile():
    p = BrandProfile(name="Notion", category="productivity")
    assert p.name == "Notion"
    assert p.competitors == []
    assert p.keywords == []


def test_generated_query():
    q = GeneratedQuery(
        id="kw-123", text="Best CRM?", category="best-of", strategy="keyword", intent="discovery"
    )
    assert q.strategy == "keyword"
    assert q.metadata is None


def test_query_result():
    r = QueryResult(
        query_id="kw-123",
        query_text="test",
        provider="openai",
        model="gpt-4o-mini",
        response="Notion is great",
        latency_ms=100,
    )
    assert r.error is None
    assert r.iteration == 1


def test_sentiment_score_defaults():
    s = SentimentScore()
    assert s.overall == 0.0
    assert s.label == "neutral"
    assert s.total_sentences == 0
    assert s.top_positive == []


def test_analysis_result():
    a = AnalysisResult(run_id="test-run", brand="Notion")
    assert a.mindshare.overall == 0.0
    assert a.sentiment.label == "neutral"
    assert a.rank_position.weighted_visibility == 0.0

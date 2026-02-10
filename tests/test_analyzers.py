"""Tests for analyzers."""

import json
from pathlib import Path

import pytest

from voyage_geo.stages.analysis.analyzers.citation import CitationAnalyzer
from voyage_geo.stages.analysis.analyzers.competitor import CompetitorAnalyzer
from voyage_geo.stages.analysis.analyzers.mention_rate import MentionRateAnalyzer
from voyage_geo.stages.analysis.analyzers.mindshare import MindshareAnalyzer
from voyage_geo.stages.analysis.analyzers.positioning import PositioningAnalyzer
from voyage_geo.stages.analysis.analyzers.sentiment import SentimentAnalyzer
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def profile():
    data = json.loads((FIXTURES / "brand_profile.json").read_text())
    return BrandProfile(**data)


@pytest.fixture
def results():
    data = json.loads((FIXTURES / "query_results.json").read_text())
    return [QueryResult(**r) for r in data]


class TestMindshare:
    def test_calculates_scores(self, results, profile):
        score = MindshareAnalyzer().analyze(results, profile)
        assert score.overall > 0
        assert "openai" in score.by_provider
        assert score.rank >= 1
        assert score.total_brands_detected > 0

    def test_empty_results(self, profile):
        score = MindshareAnalyzer().analyze([], profile)
        assert score.overall == 0


class TestMentionRate:
    def test_calculates_rates(self, results, profile):
        score = MentionRateAnalyzer().analyze(results, profile)
        assert score.overall > 0
        assert score.total_mentions > 0
        assert score.total_responses == len(results)

    def test_empty_results(self, profile):
        score = MentionRateAnalyzer().analyze([], profile)
        assert score.overall == 0


class TestSentiment:
    def test_calculates_sentiment(self, results, profile):
        score = SentimentAnalyzer().analyze(results, profile)
        assert score.label in ("positive", "neutral", "negative")
        assert isinstance(score.overall, float)
        assert isinstance(score.confidence, float)
        assert 0 <= score.confidence <= 1
        assert score.total_sentences >= 0
        assert score.positive_count + score.neutral_count + score.negative_count == score.total_sentences

    def test_provider_labels(self, results, profile):
        score = SentimentAnalyzer().analyze(results, profile)
        for prov, label in score.by_provider_label.items():
            assert label in ("positive", "neutral", "negative")
            assert prov in score.by_provider

    def test_excerpts(self, results, profile):
        score = SentimentAnalyzer().analyze(results, profile)
        assert isinstance(score.top_positive, list)
        assert isinstance(score.top_negative, list)


class TestPositioning:
    def test_extracts_attributes(self, results, profile):
        score = PositioningAnalyzer().analyze(results, profile)
        assert isinstance(score.primary_position, str)


class TestCitation:
    def test_detects_urls(self, profile):
        results = [
            QueryResult(
                query_id="t-1", query_text="test", provider="openai",
                model="test", response="Check https://notion.so and https://monday.com",
                latency_ms=100,
            )
        ]
        score = CitationAnalyzer().analyze(results, profile)
        assert score.total_citations == 2
        assert score.unique_sources_cited == 2

    def test_no_urls(self, results, profile):
        score = CitationAnalyzer().analyze(results, profile)
        assert score.total_citations >= 0


class TestCompetitor:
    def test_compares_brands(self, results, profile):
        analysis = CompetitorAnalyzer().analyze(results, profile)
        assert len(analysis.competitors) > 0
        assert analysis.brand_rank >= 1
        notion = next((c for c in analysis.competitors if c.name == "Notion"), None)
        assert notion is not None
        assert notion.mention_rate > 0

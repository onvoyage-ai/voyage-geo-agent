"""Positioning analyzer — how AI models describe/position the brand."""

from __future__ import annotations

from collections import Counter

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from voyage_geo.types.analysis import PositionAttribute, PositioningScore
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult
from voyage_geo.utils.text import contains_brand, extract_sentences

vader = SentimentIntensityAnalyzer()

POSITION_KEYWORDS = [
    "leader", "popular", "best", "top", "innovative", "affordable", "reliable",
    "powerful", "simple", "enterprise", "scalable", "trusted", "fast", "secure",
    "flexible", "comprehensive", "user-friendly", "modern", "mature", "growing",
    "niche", "expensive", "complex", "limited", "outdated", "basic",
]


class PositioningAnalyzer:
    name = "positioning"

    def analyze(self, results: list[QueryResult], profile: BrandProfile) -> PositioningScore:
        valid = [r for r in results if not r.error and r.response]

        attr_counter: Counter[str] = Counter()
        attr_sentiments: dict[str, list[float]] = {}
        by_provider: dict[str, str] = {}

        for r in valid:
            sentences = [s for s in extract_sentences(r.response) if contains_brand(s, profile.name)]
            provider_attrs: Counter[str] = Counter()

            for sentence in sentences:
                lower = sentence.lower()
                for kw in POSITION_KEYWORDS:
                    if kw in lower:
                        attr_counter[kw] += 1
                        provider_attrs[kw] += 1
                        vs = vader.polarity_scores(sentence)
                        attr_sentiments.setdefault(kw, []).append(vs["compound"])

            if provider_attrs and r.provider not in by_provider:
                by_provider[r.provider] = provider_attrs.most_common(1)[0][0]

        attributes = []
        for attr, freq in attr_counter.most_common(10):
            import statistics
            avg_sent = statistics.mean(attr_sentiments.get(attr, [0]))
            attributes.append(PositionAttribute(attribute=attr, frequency=freq, sentiment=round(avg_sent, 3)))

        primary = attr_counter.most_common(1)[0][0] if attr_counter else "unknown"

        return PositioningScore(
            primary_position=primary,
            attributes=attributes,
            by_provider=by_provider,
        )

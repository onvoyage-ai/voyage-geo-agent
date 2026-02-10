"""Sentiment analyzer — VADER-based sentiment analysis of brand mentions."""

from __future__ import annotations

import statistics

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from voyage_geo.types.analysis import SentimentExcerpt, SentimentScore
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult
from voyage_geo.utils.text import contains_brand, extract_sentences

vader = SentimentIntensityAnalyzer()


def _label(score: float) -> str:
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


class SentimentAnalyzer:
    name = "sentiment"

    def analyze(self, results: list[QueryResult], profile: BrandProfile) -> SentimentScore:
        valid = [r for r in results if not r.error and r.response]

        scored: list[dict] = []  # {text, score, provider}

        for r in valid:
            sentences = [s for s in extract_sentences(r.response) if contains_brand(s, profile.name)]
            for sentence in sentences:
                vs = vader.polarity_scores(sentence)
                scored.append({"text": sentence, "score": vs["compound"], "provider": r.provider})

        if not scored:
            return SentimentScore()

        scores = [s["score"] for s in scored]
        overall = statistics.mean(scores)
        label = _label(overall)

        stddev = statistics.stdev(scores) if len(scores) > 1 else 0.0
        sample_factor = min(len(scored) / 10, 1.0)
        variance_factor = max(0.0, 1.0 - stddev)
        confidence = round(sample_factor * variance_factor, 2)

        pos = sum(1 for s in scores if s >= 0.05)
        neg = sum(1 for s in scores if s <= -0.05)
        neu = len(scores) - pos - neg

        # By provider
        by_provider: dict[str, float] = {}
        by_provider_label: dict[str, str] = {}
        prov_groups: dict[str, list[float]] = {}
        for s in scored:
            prov_groups.setdefault(s["provider"], []).append(s["score"])
        for prov, prov_scores in prov_groups.items():
            avg = statistics.mean(prov_scores)
            by_provider[prov] = round(avg, 4)
            by_provider_label[prov] = _label(avg)

        # By category (from query ID prefix)
        by_category: dict[str, float] = {}
        cat_scores: dict[str, list[float]] = {}
        for r in valid:
            prefix = r.query_id.split("-")[0]
            cat_map = {"kw": "keyword", "ps": "persona", "cp": "competitor", "in": "intent"}
            cat = cat_map.get(prefix, "unknown")
            sentences = [s for s in extract_sentences(r.response) if contains_brand(s, profile.name)]
            for sentence in sentences:
                vs = vader.polarity_scores(sentence)
                cat_scores.setdefault(cat, []).append(vs["compound"])
        for cat, cs in cat_scores.items():
            by_category[cat] = round(statistics.mean(cs), 4)

        # Top excerpts
        sorted_scored = sorted(scored, key=lambda s: s["score"], reverse=True)
        top_positive = [
            SentimentExcerpt(text=s["text"][:200], score=s["score"], provider=s["provider"])
            for s in sorted_scored if s["score"] >= 0.05
        ][:5]
        top_negative = [
            SentimentExcerpt(text=s["text"][:200], score=s["score"], provider=s["provider"])
            for s in reversed(sorted_scored) if s["score"] <= -0.05
        ][:5]

        return SentimentScore(
            overall=round(overall, 4),
            label=label,  # type: ignore[arg-type]
            confidence=confidence,
            by_provider=by_provider,
            by_provider_label=by_provider_label,  # type: ignore[arg-type]
            by_category=by_category,
            positive_count=pos,
            neutral_count=neu,
            negative_count=neg,
            total_sentences=len(scored),
            top_positive=top_positive,
            top_negative=top_negative,
        )
